"""Transactional run control. No provider call occurs inside these transactions."""

from __future__ import annotations

import builtins
import hashlib
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.definitions import Registry, WorkflowDefinition
from app.models import (
    Approval,
    Idempotency,
    Job,
    NodeExecution,
    Run,
    RunEvent,
    RunStatus,
)
from app.models.enums import TERMINAL_STATUSES


def canonical(value: Any) -> str:
    try:
        serialized = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        serialized.encode("utf-8")
        return serialized
    except (TypeError, ValueError, UnicodeError) as exc:
        raise RunError("invalid_json", 422) from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class RunError(Exception):
    """Safe, stable error suitable for an API or CLI response."""

    def __init__(self, code: str, status_code: int = 409) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def bounded(value: Any, maximum: int) -> None:
    if len(canonical(value).encode()) > maximum:
        raise RunError("limit_exceeded", 422)


def page(limit: int, offset: int = 0) -> None:
    if not 1 <= limit <= 500 or offset < 0:
        raise RunError("invalid_pagination", 422)


class RunService:
    """One database transaction owner for API controls and worker checkpoints."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        registry: Registry,
        provider_profile: dict[str, Any],
        notifier: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
        max_event_payload_bytes: int = 4096,
        provider_validator: Callable[[], None] | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.registry = registry
        self.provider_profile = provider_profile
        self.provider_validator = provider_validator
        self.notifier = notifier
        if not 512 <= max_event_payload_bytes <= 4096:
            raise ValueError("invalid event payload limit")
        self.max_event_payload_bytes = max_event_payload_bytes

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            async with session.begin():
                yield session
            # Only committed identifiers are published. Redis loss never undoes state.
            if self.notifier is not None:
                for identity in session.info.get("notifications", []):
                    with suppress(Exception):
                        await self.notifier(identity)

    def definition(self, run: Run) -> WorkflowDefinition:
        try:
            definition = self.registry.get(run.workflow_id, run.workflow_version)
        except (KeyError, ValueError) as exc:
            raise RunError("definition_unavailable", 503) from exc
        if definition.definition_hash != run.definition_hash:
            raise RunError("definition_mismatch", 409)
        if run.provider_profile != self.provider_profile:
            raise RunError("provider_profile_mismatch", 503)
        return definition

    async def _get(
        self, session: AsyncSession, run_id: UUID, *, lock: bool = False
    ) -> Run:
        query = select(Run).where(Run.id == run_id)
        if lock:
            query = query.with_for_update()
        run = await session.scalar(query)
        if run is None:
            raise RunError("run_not_found", 404)
        return run

    def _event(
        self,
        session: AsyncSession,
        run: Run,
        event_type: str,
        actor: UUID | None = None,
        node: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        safe_payload = payload or {}
        bounded(safe_payload, self.max_event_payload_bytes)
        run.event_sequence += 1
        event_id = uuid4()
        session.info.setdefault("notifications", []).append(
            {
                "event_id": str(event_id),
                "run_id": str(run.id),
                "sequence": run.event_sequence,
            }
        )
        session.add(
            RunEvent(
                id=event_id,
                run_id=run.id,
                sequence=run.event_sequence,
                event_type=event_type,
                actor_id=actor,
                node_id=node,
                payload=safe_payload,
            )
        )

    async def _idem(
        self,
        session: AsyncSession,
        principal: UUID,
        family: str,
        key: str | None,
        fingerprint: str,
    ) -> UUID | None:
        if key is None:
            return None
        if not key or len(key) > 200:
            raise RunError("invalid_idempotency_key", 422)
        # Serialize the key before querying its record, including concurrent creates.
        lock_id = int.from_bytes(
            hashlib.sha256(f"{principal}:{family}:{key}".encode()).digest()[:8],
            "big",
            signed=True,
        )
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id}
        )
        record = await session.scalar(
            select(Idempotency).where(
                Idempotency.principal == principal,
                Idempotency.family == family,
                Idempotency.key == key,
            )
        )
        if record is None:
            return None
        if record.fingerprint != fingerprint:
            raise RunError("idempotency_conflict")
        return record.run_id

    def _save_idem(
        self,
        session: AsyncSession,
        principal: UUID,
        family: str,
        key: str | None,
        fingerprint: str,
        run_id: UUID,
    ) -> None:
        if key is not None:
            session.add(
                Idempotency(
                    principal=principal,
                    family=family,
                    key=key,
                    fingerprint=fingerprint,
                    run_id=run_id,
                )
            )

    async def create(
        self,
        principal: UUID,
        workflow_id: str,
        version: str,
        input: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> Run:
        try:
            definition = self.registry.get(workflow_id, version)
        except (KeyError, ValueError) as exc:
            raise RunError("workflow_not_found", 404) from exc
        try:
            bounded(input, definition.max_input_bytes)
        except RunError as exc:
            if exc.code == "invalid_json":
                raise RunError("invalid_input", 422) from exc
            raise
        try:
            validated = definition.input_schema.model_validate(input).model_dump(
                mode="json"
            )
        except ValidationError as exc:
            raise RunError("invalid_input", 422) from exc
        bounded(validated, definition.max_input_bytes)
        fingerprint = digest(
            {
                "principal": str(principal),
                "method": "POST",
                "path": "/api/v1/runs",
                "workflow_id": workflow_id,
                "version": version,
                "hash": definition.definition_hash,
                "input": validated,
            }
        )
        async with self.transaction() as session:
            existing = await self._idem(
                session, principal, "create", idempotency_key, fingerprint
            )
            if existing is not None:
                return await self._get(session, existing)
            if any(node.kind == "agent" for node in definition.nodes):
                if not self.provider_profile:
                    raise RunError("provider_configuration_missing", 503)
                if self.provider_validator is not None:
                    self.provider_validator()
            run = Run(
                id=uuid4(),
                workflow_id=workflow_id,
                workflow_version=version,
                definition_hash=definition.definition_hash,
                definition_snapshot=definition.snapshot(),
                schema_version=1,
                created_by_id=principal,
                input=validated,
                context={},
                outputs={},
                provider_profile=self.provider_profile,
                status=RunStatus.CREATED,
                revision=1,
                event_sequence=0,
                generation=0,
                call_count=0,
                cancel_requested=False,
            )
            session.add(run)
            await session.flush([run])
            self._event(session, run, "run.created", principal)
            self._save_idem(
                session, principal, "create", idempotency_key, fingerprint, run.id
            )
            await session.flush()
            return run

    async def _queue(
        self, run_id: UUID, principal: UUID, family: str, key: str | None
    ) -> Run:
        fingerprint = digest(
            {
                "principal": str(principal),
                "method": "POST",
                "path": f"/api/v1/runs/{run_id}/{family}",
                "body": {},
            }
        )
        async with self.transaction() as session:
            existing = await self._idem(session, principal, family, key, fingerprint)
            if existing is not None:
                return await self._get(session, existing)
            run = await self._get(session, run_id, lock=True)
            definition = self.definition(run)
            allowed = (
                {RunStatus.CREATED}
                if family == "start"
                else {RunStatus.APPROVED, RunStatus.INTERRUPTED}
            )
            if run.status not in allowed:
                raise RunError("invalid_transition")
            if (
                run.status == RunStatus.INTERRUPTED
                and run.current_node
                and run.current_node not in run.outputs
            ):
                node = next(
                    item for item in definition.nodes if item.id == run.current_node
                )
                if (
                    node.kind == "tool"
                    and node.tool is not None
                    and node.tool.effect == "non_idempotent"
                ):
                    raise RunError("unsafe_resume_requires_reconciliation")
            if run.status == RunStatus.APPROVED:
                approval = await session.scalar(
                    select(Approval).where(
                        Approval.run_id == run.id, Approval.node_id == run.current_node
                    )
                )
                if (
                    approval is None
                    or approval.decision != "approved"
                    or approval.definition_hash != run.definition_hash
                    or approval.content_hash != digest(approval.content)
                ):
                    raise RunError("stale_approval")
            if (
                any(node.kind == "agent" for node in definition.nodes)
                and self.provider_validator is not None
            ):
                self.provider_validator()
            job = await session.scalar(select(Job).where(Job.run_id == run.id))
            if job is None:
                session.add(Job(run_id=run.id, status="QUEUED"))
            else:
                job.status = "QUEUED"
            run.status = RunStatus.QUEUED
            run.revision += 1
            self._event(
                session,
                run,
                "run.resumed" if family == "resume" else "run.queued",
                principal,
            )
            self._save_idem(session, principal, family, key, fingerprint, run.id)
            await session.flush()
            return run

    async def start(
        self, run_id: UUID, principal: UUID, idempotency_key: str | None = None
    ) -> Run:
        return await self._queue(run_id, principal, "start", idempotency_key)

    async def resume(
        self, run_id: UUID, principal: UUID, idempotency_key: str | None = None
    ) -> Run:
        return await self._queue(run_id, principal, "resume", idempotency_key)

    async def cancel(self, run_id: UUID, principal: UUID) -> Run:
        async with self.transaction() as session:
            run = await self._get(session, run_id, lock=True)
            if run.status in TERMINAL_STATUSES:
                raise RunError("invalid_transition")
            run.cancel_requested = True
            run.revision += 1
            if run.status != RunStatus.RUNNING:
                run.status = RunStatus.CANCELLED
                run.owner = None
                run.lease_expires_at = None
                job = await session.scalar(select(Job).where(Job.run_id == run.id))
                if job is not None:
                    job.status = "DONE"
                await self.cancel_active_attempts(session, run)
                self._event(session, run, "run.cancelled", principal)
            else:
                self._event(session, run, "run.cancellation_requested", principal)
            await session.flush()
            return run

    async def cancel_active_attempts(self, session: AsyncSession, run: Run) -> None:
        attempts = await session.scalars(
            select(NodeExecution).where(
                NodeExecution.run_id == run.id,
                NodeExecution.status.in_(("EXECUTING", "WAITING_APPROVAL")),
            )
        )
        for attempt in attempts:
            attempt.status = "CANCELLED"

    async def decide(
        self,
        run_id: UUID,
        approval_id: UUID,
        principal: UUID,
        decision: str,
        expected_revision: int,
        content_revision: int,
        content_hash: str,
        comment: str | None = None,
    ) -> Run:
        if decision not in {"approved", "rejected"} or (
            comment is not None and len(comment) > 2000
        ):
            raise RunError("invalid_decision", 422)
        async with self.transaction() as session:
            run = await self._get(session, run_id, lock=True)
            approval = await session.scalar(
                select(Approval)
                .where(Approval.id == approval_id, Approval.run_id == run_id)
                .with_for_update()
            )
            if approval is None:
                raise RunError("approval_not_found", 404)
            if (
                run.status != RunStatus.WAITING_APPROVAL
                or run.revision != expected_revision
                or approval.decision is not None
                or approval.content_revision != content_revision
                or approval.content_hash != content_hash
                or digest(approval.content) != content_hash
                or approval.definition_hash != run.definition_hash
            ):
                raise RunError("stale_approval")
            if decision == "approved":
                definition = self.definition(run)
                bounded(
                    {
                        "input": run.input,
                        "context": run.context,
                        "outputs": {**run.outputs, approval.node_id: approval.content},
                    },
                    definition.max_total_bytes,
                )
            approval.decision = decision
            approval.actor_id = principal
            approval.decided_at = await session.scalar(select(func.clock_timestamp()))
            approval.comment = comment
            run.status = (
                RunStatus.APPROVED if decision == "approved" else RunStatus.REJECTED
            )
            run.revision += 1
            if decision == "rejected":
                attempts = await session.scalars(
                    select(NodeExecution).where(
                        NodeExecution.run_id == run.id,
                        NodeExecution.node_id == approval.node_id,
                        NodeExecution.status == "WAITING_APPROVAL",
                    )
                )
                for attempt in attempts:
                    attempt.status = "REJECTED"
            if decision == "approved":
                run.outputs = {**run.outputs, approval.node_id: approval.content}
                execution = await session.scalar(
                    select(NodeExecution)
                    .where(
                        NodeExecution.run_id == run_id,
                        NodeExecution.node_id == approval.node_id,
                    )
                    .order_by(NodeExecution.attempt.desc())
                    .limit(1)
                )
                if execution is not None:
                    execution.status = "COMPLETED"
                    execution.output = approval.content
                self._event(session, run, "node.completed", principal, approval.node_id)
            self._event(
                session,
                run,
                "approval.decided",
                principal,
                approval.node_id,
                {"approval_id": str(approval.id), "decision": decision},
            )
            await session.flush()
            return run

    async def get(self, run_id: UUID) -> Run:
        async with self.session_factory() as session:
            return await self._get(session, run_id)

    async def list(
        self,
        status: str | None = None,
        workflow_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[Run]:
        page(limit, offset)
        query = select(Run)
        if status is not None:
            query = query.where(Run.status == status)
        if workflow_id is not None:
            query = query.where(Run.workflow_id == workflow_id)
        async with self.session_factory() as session:
            return list(
                (
                    await session.scalars(
                        query.order_by(Run.created_at.desc(), Run.id)
                        .limit(limit)
                        .offset(offset)
                    )
                ).all()
            )

    async def _detail(
        self, model: Any, run_id: UUID, limit: int, offset: int
    ) -> builtins.list[Any]:
        page(limit, offset)
        async with self.session_factory() as session:
            await self._get(session, run_id)
            return list(
                (
                    await session.scalars(
                        select(model)
                        .where(model.run_id == run_id)
                        .order_by(model.created_at, model.id)
                        .limit(limit)
                        .offset(offset)
                    )
                ).all()
            )

    async def nodes(
        self, run_id: UUID, limit: int = 100, offset: int = 0
    ) -> builtins.list[NodeExecution]:
        return await self._detail(NodeExecution, run_id, limit, offset)

    async def approvals(
        self, run_id: UUID, limit: int = 100, offset: int = 0
    ) -> builtins.list[Approval]:
        return await self._detail(Approval, run_id, limit, offset)

    async def events(
        self, run_id: UUID, after_sequence: int = 0, limit: int = 100
    ) -> builtins.list[RunEvent]:
        page(limit, after_sequence)
        async with self.session_factory() as session:
            await self._get(session, run_id)
            return list(
                (
                    await session.scalars(
                        select(RunEvent)
                        .where(
                            RunEvent.run_id == run_id,
                            RunEvent.sequence > after_sequence,
                        )
                        .order_by(RunEvent.sequence)
                        .limit(limit)
                    )
                ).all()
            )
