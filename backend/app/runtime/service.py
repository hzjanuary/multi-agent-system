"""Leased PostgreSQL worker and per-node application-owned checkpoints.

LangGraph chooses every transition. PostgreSQL commits are authoritative; there
is no independent LangGraph checkpoint database or execution engine.
"""

from __future__ import annotations

import asyncio
import inspect
from contextlib import suppress
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select

from app.definitions import NodeDefinition, resolve_mapping
from app.llm.errors import LLMProviderError
from app.models import Approval, Job, NodeExecution, Run, RunStatus
from app.runtime.graph import build_workflow_graph
from app.workflows.service import RunError, RunService, bounded, digest


class Worker:
    def __init__(
        self,
        service: RunService,
        llm_service: Any,
        *,
        lease_seconds: float = 60,
        heartbeat_seconds: float = 10,
    ) -> None:
        if (
            not 1 <= lease_seconds <= 3600
            or not 0 < heartbeat_seconds < lease_seconds / 2
        ):
            raise ValueError("invalid lease/heartbeat configuration")
        self.service = service
        self.llm = llm_service
        self.lease_seconds = lease_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.owner = str(uuid4())

    async def reconcile(self) -> int:
        count = 0
        async with self.service.transaction() as session:
            expired = (
                await session.scalars(
                    select(Run)
                    .where(
                        Run.status == RunStatus.RUNNING,
                        Run.lease_expires_at < func.clock_timestamp(),
                    )
                    .with_for_update(skip_locked=True)
                )
            ).all()
            for run in expired:
                run.status = (
                    RunStatus.CANCELLED
                    if run.cancel_requested
                    else RunStatus.INTERRUPTED
                )
                run.generation += 1
                run.owner = None
                run.lease_expires_at = None
                run.revision += 1
                rows = (
                    await session.scalars(
                        select(NodeExecution).where(
                            NodeExecution.run_id == run.id,
                            NodeExecution.status == "EXECUTING",
                        )
                    )
                ).all()
                for row in rows:
                    row.status = "INTERRUPTED"
                job = await session.scalar(select(Job).where(Job.run_id == run.id))
                if job is not None:
                    job.status = "DONE"
                self.service._event(
                    session,
                    run,
                    "run.cancelled" if run.cancel_requested else "run.interrupted",
                )
                count += 1
        return count

    async def claim(self) -> tuple[UUID, int] | None:
        await self.reconcile()
        async with self.service.transaction() as session:
            run = await session.scalar(
                select(Run)
                .join(Job, Job.run_id == Run.id)
                .where(Run.status == RunStatus.QUEUED, Job.status == "QUEUED")
                .order_by(Job.updated_at, Job.created_at)
                .with_for_update(of=Run, skip_locked=True)
                .limit(1)
            )
            if run is None:
                return None
            try:
                self.service.definition(run)
            except RunError as exc:
                # No ownership was acquired: keep the original queued submission.
                # Move this blocked job behind other jobs without claiming it.
                error = {"code": exc.code}
                if run.error != error:
                    run.error = error
                    run.revision += 1
                    self.service._event(
                        session, run, "run.execution_blocked", payload=error
                    )
                job = await session.scalar(select(Job).where(Job.run_id == run.id))
                if job is not None:
                    now = await session.scalar(select(func.clock_timestamp()))
                    assert now is not None
                    job.updated_at = now
                return None
            run.error = None
            run.generation += 1
            run.owner = self.owner
            run.lease_expires_at = await session.scalar(
                select(func.clock_timestamp() + timedelta(seconds=self.lease_seconds))
            )
            run.status = RunStatus.RUNNING
            run.revision += 1
            job = await session.scalar(select(Job).where(Job.run_id == run.id))
            if job is not None:
                job.status = "OWNED"
            self.service._event(session, run, "run.started")
            return run.id, run.generation

    async def _owned(self, session: Any, run_id: UUID, generation: int) -> Run:
        run = await self.service._get(session, run_id, lock=True)
        now = await session.scalar(select(func.clock_timestamp()))
        if (
            run.status != RunStatus.RUNNING
            or run.owner != self.owner
            or run.generation != generation
            or run.lease_expires_at is None
            or run.lease_expires_at <= now
        ):
            raise RunError("stale_execution_claim")
        return run

    async def _stop(
        self, session: Any, run: Run, status: RunStatus, event: str
    ) -> None:
        run.status = status
        run.revision += 1
        run.owner = None
        run.lease_expires_at = None
        job = await session.scalar(select(Job).where(Job.run_id == run.id))
        if job is not None:
            job.status = "DONE"
        if status == RunStatus.CANCELLED:
            await self.service.cancel_active_attempts(session, run)
        self.service._event(session, run, event)

    async def heartbeat(self, run_id: UUID, generation: int) -> bool:
        try:
            async with self.service.transaction() as session:
                run = await self._owned(session, run_id, generation)
                run.lease_expires_at = await session.scalar(
                    select(
                        func.clock_timestamp() + timedelta(seconds=self.lease_seconds)
                    )
                )
            return True
        except RunError:
            return False

    async def _heartbeats(self, run_id: UUID, generation: int) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_seconds)
            if not await self.heartbeat(run_id, generation):
                return

    async def reserve_call(self, run_id: UUID, generation: int) -> None:
        async with self.service.transaction() as session:
            run = await self._owned(session, run_id, generation)
            if run.cancel_requested:
                raise RunError("cancellation_requested")
            definition = self.service.definition(run)
            if run.call_count >= definition.max_calls:
                raise RunError("provider_call_limit")
            run.call_count += 1
            row = await session.scalar(
                select(NodeExecution).where(
                    NodeExecution.run_id == run.id,
                    NodeExecution.node_id == run.current_node,
                    NodeExecution.generation == generation,
                    NodeExecution.status == "EXECUTING",
                )
            )
            if row is not None:
                row.execution_metadata = {
                    **row.execution_metadata,
                    "reserved_calls": row.execution_metadata.get("reserved_calls", 0)
                    + 1,
                }

    async def _execute(
        self, run_id: UUID, generation: int, node: NodeDefinition
    ) -> bool:
        async with self.service.transaction() as session:
            run = await self._owned(session, run_id, generation)
            if run.cancel_requested:
                await self._stop(session, run, RunStatus.CANCELLED, "run.cancelled")
                return False
            if node.id in run.outputs:
                return True
            definition = self.service.definition(run)
            content = resolve_mapping(node.input_mapping, run.input, run.outputs)
            bounded(content, definition.max_total_bytes)
            count = await session.scalar(
                select(func.count())
                .select_from(NodeExecution)
                .where(NodeExecution.run_id == run.id, NodeExecution.node_id == node.id)
            )
            execution = NodeExecution(
                id=uuid4(),
                run_id=run.id,
                node_id=node.id,
                kind=node.kind,
                attempt=(count or 0) + 1,
                generation=generation,
                status="EXECUTING",
                execution_metadata={},
            )
            session.add(execution)
            run.current_node = node.id
            run.revision += 1
            self.service._event(
                session,
                run,
                "node.started",
                node=node.id,
                payload={"attempt": execution.attempt},
            )
            if node.kind == "approval":
                bounded(content, definition.max_node_output_bytes)
                bounded(
                    {"input": run.input, "outputs": run.outputs, "pending": content},
                    definition.max_total_bytes,
                )
                approval = Approval(
                    id=uuid4(),
                    run_id=run.id,
                    node_id=node.id,
                    workflow_version=run.workflow_version,
                    definition_hash=run.definition_hash,
                    content_revision=run.revision,
                    content_hash=digest(content),
                    content=content,
                )
                session.add(approval)
                execution.status = "WAITING_APPROVAL"
                await self._stop(
                    session, run, RunStatus.WAITING_APPROVAL, "approval.requested"
                )
                return False
            execution_id = execution.id
        # All network and installed handler execution occurs outside any transaction.
        metadata: dict[str, Any] = {}
        if node.kind == "agent" and node.agent is not None:

            async def reserve() -> None:
                await self.reserve_call(run_id, generation)

            output, metadata = await self.llm.invoke(node.agent, content, reserve)
        elif node.kind == "tool" and node.tool is not None:
            validated = node.tool.input_schema.model_validate(content)
            if inspect.iscoroutinefunction(node.tool.handler):
                result = await node.tool.handler(validated)
            else:
                result = await asyncio.to_thread(node.tool.handler, validated)
                if inspect.isawaitable(result):
                    result = await result
            output = node.tool.output_schema.model_validate(
                result.model_dump(mode="json")
                if isinstance(result, BaseModel)
                else result
            ).model_dump(mode="json")
        else:
            raise RunError("invalid_definition")
        async with self.service.transaction() as session:
            run = await self._owned(session, run_id, generation)
            if run.cancel_requested:
                await self._stop(session, run, RunStatus.CANCELLED, "run.cancelled")
                return False
            definition = self.service.definition(run)
            bounded(output, definition.max_node_output_bytes)
            outputs = {**run.outputs, node.id: output}
            bounded(
                {"input": run.input, "context": run.context, "outputs": outputs},
                definition.max_total_bytes,
            )
            committed_execution = await session.get(NodeExecution, execution_id)
            if committed_execution is None:
                raise RunError("stale_execution_claim")
            committed_execution.status = "COMPLETED"
            committed_execution.output = output
            # Provider invocation only returns known safe metadata, never prompts.
            committed_execution.execution_metadata = {
                **committed_execution.execution_metadata,
                **metadata,
            }
            run.outputs = outputs
            run.revision += 1
            self.service._event(session, run, "node.completed", node=node.id)
        return True

    async def _finalize(self, run_id: UUID, generation: int) -> None:
        async with self.service.transaction() as session:
            run = await self._owned(session, run_id, generation)
            if run.cancel_requested:
                await self._stop(session, run, RunStatus.CANCELLED, "run.cancelled")
                return
            definition = self.service.definition(run)
            final = definition.output_schema.model_validate(
                resolve_mapping(definition.output_mapping, run.input, run.outputs)
            ).model_dump(mode="json")
            bounded(final, definition.max_node_output_bytes)
            bounded(
                {
                    "input": run.input,
                    "context": run.context,
                    "outputs": run.outputs,
                    "final_output": final,
                },
                definition.max_total_bytes,
            )
            run.final_output = final
            await self._stop(session, run, RunStatus.COMPLETED, "run.completed")

    async def _fail(self, run_id: UUID, generation: int, exc: Exception) -> None:
        # Persist in a fresh transaction, independent of the failed operation.
        try:
            async with self.service.transaction() as session:
                run = await self._owned(session, run_id, generation)
                if run.cancel_requested:
                    await self._stop(session, run, RunStatus.CANCELLED, "run.cancelled")
                    return
                category = getattr(exc, "category", None)
                code = (
                    exc.code
                    if isinstance(exc, RunError)
                    else (
                        "invalid_output"
                        if isinstance(exc, ValidationError)
                        else (
                            f"provider_{category.value}"
                            if category is not None
                            else "execution_failed"
                        )
                    )
                )
                run.error = {"code": code}
                rows = (
                    await session.scalars(
                        select(NodeExecution).where(
                            NodeExecution.run_id == run.id,
                            NodeExecution.generation == generation,
                            NodeExecution.status == "EXECUTING",
                        )
                    )
                ).all()
                for row in rows:
                    row.status = "FAILED"
                    row.error = run.error
                    if (
                        isinstance(exc, LLMProviderError)
                        and exc.diagnostics is not None
                    ):
                        row.execution_metadata = {
                            **row.execution_metadata,
                            "provider_diagnostics": exc.diagnostics.model_dump(
                                mode="json", exclude_none=True
                            ),
                        }
                if rows:
                    self.service._event(
                        session,
                        run,
                        "node.failed",
                        node=run.current_node,
                        payload=run.error,
                    )
                await self._stop(session, run, RunStatus.FAILED, "run.failed")
        except RunError:
            # Ownership already expired/reconciled: stale worker must not write.
            return

    async def execute_claim(self, run_id: UUID, generation: int) -> None:
        heartbeats = asyncio.create_task(self._heartbeats(run_id, generation))
        try:
            run = await self.service.get(run_id)
            definition = self.service.definition(run)

            async def execute(node: NodeDefinition) -> bool:
                return await self._execute(run_id, generation, node)

            async def finalize() -> None:
                await self._finalize(run_id, generation)

            graph = build_workflow_graph(definition, execute, finalize)
            await graph.ainvoke(
                {"halted": False}, {"recursion_limit": len(definition.nodes) + 5}
            )
        except Exception as exc:
            await self._fail(run_id, generation, exc)
        finally:
            heartbeats.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeats

    async def tick(self) -> bool:
        claim = await self.claim()
        if claim is None:
            return False
        await self.execute_claim(*claim)
        return True

    async def run_forever(self, poll_seconds: float = 1) -> None:
        while True:
            if not await self.tick():
                await asyncio.sleep(poll_seconds)
