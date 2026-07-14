"""Runtime service orchestration for deterministic LangGraph execution."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast
from uuid import UUID

from app.llm.contracts import LLMErrorCategory
from app.llm.errors import LLMProviderError
from app.llm.service import LLMService
from app.llm.settings import LLMSettings
from app.models.enums import WorkflowEventStatus, WorkflowStatus
from app.runtime.graph import (
    RuntimeNodeHandlers,
    RuntimeStatePayload,
    build_workflow_graph,
)
from app.runtime.llm_adapter import LLMCompletionService, LLMRuntimeAdapter
from app.runtime.nodes import create_deterministic_node_handlers
from app.runtime.schemas import (
    RuntimeStage,
    RuntimeWorkflowResult,
    RuntimeWorkflowState,
)
from app.runtime.state_adapter import (
    runtime_state_to_workflow_state,
    workflow_state_to_runtime_state,
)
from app.workflows.events import WorkflowEventService
from app.workflows.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
)
from app.workflows.schemas import WorkflowError, WorkflowEventCreate, WorkflowState
from app.workflows.service import WorkflowService

PRE_APPROVAL_RUNTIME_STAGES: tuple[RuntimeStage, ...] = (
    RuntimeStage.PLANNER,
    RuntimeStage.RETRIEVAL,
    RuntimeStage.QUOTATION,
    RuntimeStage.COMPLIANCE,
    RuntimeStage.VALIDATION,
    RuntimeStage.APPROVAL,
)

RUNTIME_STAGE_STATUSES: dict[RuntimeStage, WorkflowStatus] = {
    RuntimeStage.PLANNER: WorkflowStatus.PLANNING,
    RuntimeStage.RETRIEVAL: WorkflowStatus.RETRIEVING,
    RuntimeStage.QUOTATION: WorkflowStatus.CALCULATING,
    RuntimeStage.COMPLIANCE: WorkflowStatus.CHECKING_COMPLIANCE,
    RuntimeStage.VALIDATION: WorkflowStatus.VALIDATING,
    RuntimeStage.APPROVAL: WorkflowStatus.WAITING_APPROVAL,
    RuntimeStage.EMAIL_PREPARATION: WorkflowStatus.GENERATING_EMAIL,
}


class WorkflowRuntimeError(Exception):
    """Base runtime service error."""


class WorkflowRuntimePreconditionError(WorkflowRuntimeError):
    """Raised when a workflow cannot be run from its current state."""


class WorkflowRuntimeNodeError(WorkflowRuntimeError):
    """Raised when a runtime node fails."""

    def __init__(self, stage: RuntimeStage, message: str) -> None:
        super().__init__(f"Runtime node {stage.value} failed: {message}")
        self.stage = stage


class RuntimeService:
    """Orchestrate deterministic runtime execution through workflow services."""

    def __init__(
        self,
        workflow_service: WorkflowService,
        workflow_event_service: WorkflowEventService,
        *,
        node_handlers: RuntimeNodeHandlers | None = None,
        stages: Sequence[RuntimeStage] = PRE_APPROVAL_RUNTIME_STAGES,
        llm_settings: LLMSettings | None = None,
        llm_service: LLMCompletionService | None = None,
    ) -> None:
        self.workflow_service = workflow_service
        self.workflow_event_service = workflow_event_service
        self.llm_settings = llm_settings or LLMSettings()
        self.llm_runtime_enabled = self.llm_settings.runtime_enabled
        self.llm_service = (
            llm_service
            if llm_service is not None
            else (
                LLMService(settings=self.llm_settings)
                if self.llm_runtime_enabled
                else None
            )
        )
        self.llm_adapter = (
            LLMRuntimeAdapter(self.llm_service)
            if self.llm_runtime_enabled and self.llm_service is not None
            else None
        )
        self.node_handlers = (
            dict(node_handlers)
            if node_handlers is not None
            else create_deterministic_node_handlers()
        )
        self.stages = tuple(stages)
        self.graph = build_workflow_graph(self.node_handlers, stages=self.stages)

    async def run_workflow(
        self,
        workflow_id: UUID,
        *,
        actor_type: str | None = None,
        actor_id: UUID | None = None,
    ) -> RuntimeWorkflowResult:
        """Run one workflow through the deterministic pre-approval runtime."""
        workflow_state = await self.workflow_service.get_workflow(workflow_id)
        if workflow_state is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} was not found")

        if workflow_state.status is not WorkflowStatus.CREATED:
            await self._append_runtime_failed_event(
                workflow_id,
                actor_type=actor_type,
                actor_id=actor_id,
                message="Workflow runtime can only start from CREATED status.",
                payload={"status": workflow_state.status.value},
            )
            raise WorkflowRuntimePreconditionError(
                "Workflow runtime can only start from CREATED status",
            )

        await self._append_runtime_event(
            workflow_id,
            "workflow.runtime.started",
            WorkflowEventStatus.STARTED,
            actor_type=actor_type,
            actor_id=actor_id,
            message="Workflow runtime started.",
            payload={"status": workflow_state.status.value},
        )

        runtime_state = workflow_state_to_runtime_state(workflow_state)
        current_workflow_state = workflow_state
        runtime_payload = cast(
            RuntimeStatePayload, runtime_state.model_dump(mode="json")
        )
        stream = iter(self.graph.stream(runtime_payload))

        try:
            for stage in self.stages:
                stage_status = RUNTIME_STAGE_STATUSES[stage]
                current_workflow_state = (
                    await self.workflow_service.transition_workflow_status(
                        workflow_id,
                        stage_status,
                        actor_type=actor_type,
                        actor_id=actor_id,
                        reason=f"Runtime entered {stage.value} stage.",
                    )
                )
                runtime_payload = self._payload_with_status(
                    runtime_payload,
                    stage_status,
                )
                await self._append_node_event(
                    workflow_id,
                    stage,
                    "workflow.node.started",
                    WorkflowEventStatus.STARTED,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    workflow_status=stage_status,
                    message=f"Runtime stage {stage.value} started.",
                    payload=self._llm_stage_event_payload(stage),
                )

                runtime_payload = await self._execute_stage(
                    stream,
                    runtime_payload,
                    stage,
                )
                runtime_payload = self._payload_with_status(
                    runtime_payload,
                    stage_status,
                )
                stage_runtime_state = RuntimeWorkflowState.model_validate(
                    runtime_payload,
                )
                await self._append_node_event(
                    workflow_id,
                    stage,
                    "workflow.node.completed",
                    WorkflowEventStatus.COMPLETED,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    workflow_status=stage_status,
                    message=f"Runtime stage {stage.value} completed.",
                    stage_output=stage_runtime_state.stage_outputs.get(stage),
                    payload=self._llm_stage_event_payload(stage),
                )
        except Exception as exc:
            await self._handle_runtime_failure(
                workflow_id,
                current_workflow_state,
                runtime_payload,
                stage,
                exc,
                actor_type=actor_type,
                actor_id=actor_id,
            )
            raise WorkflowRuntimeNodeError(stage, str(exc)) from exc

        final_runtime_state = RuntimeWorkflowState.model_validate(
            runtime_payload,
        ).model_copy(update={"status": current_workflow_state.status})
        updated_workflow_state = runtime_state_to_workflow_state(
            final_runtime_state,
            current_workflow_state,
        )
        await self.workflow_service.update_workflow_state(
            workflow_id,
            updated_workflow_state,
            actor_type=actor_type,
            actor_id=actor_id,
            reason="Runtime persisted deterministic pre-approval state.",
        )
        await self._append_runtime_event(
            workflow_id,
            "workflow.runtime.waiting_for_approval",
            WorkflowEventStatus.COMPLETED,
            actor_type=actor_type,
            actor_id=actor_id,
            message="Workflow runtime is waiting for approval.",
            payload={
                "status": WorkflowStatus.WAITING_APPROVAL.value,
                "completed_stages": [
                    stage.value for stage in final_runtime_state.completed_stages
                ],
            },
        )

        return RuntimeWorkflowResult(
            state=final_runtime_state,
            completed=False,
            failed=False,
            message="Workflow is waiting for approval.",
        )

    def _next_stage_payload(
        self,
        stream: Any,
        stage: RuntimeStage,
    ) -> RuntimeStatePayload:
        chunk = next(stream)
        if isinstance(chunk, dict):
            stage_chunk = chunk.get(stage.value)
            if isinstance(stage_chunk, dict):
                return cast(RuntimeStatePayload, stage_chunk)
            return cast(RuntimeStatePayload, chunk)
        raise TypeError("Runtime graph stream yielded an invalid state payload")

    async def _execute_stage(
        self,
        stream: Any,
        runtime_payload: RuntimeStatePayload,
        stage: RuntimeStage,
    ) -> RuntimeStatePayload:
        if self.llm_adapter is None:
            return self._next_stage_payload(stream, stage)

        runtime_state = RuntimeWorkflowState.model_validate(runtime_payload)
        next_state = await self.llm_adapter.run_stage(runtime_state, stage)
        return cast(RuntimeStatePayload, next_state.model_dump(mode="json"))

    def _payload_with_status(
        self,
        payload: RuntimeStatePayload,
        status: WorkflowStatus,
    ) -> RuntimeStatePayload:
        runtime_state = RuntimeWorkflowState.model_validate(payload)
        return cast(
            RuntimeStatePayload,
            runtime_state.model_copy(update={"status": status}).model_dump(
                mode="json",
            ),
        )

    async def _handle_runtime_failure(
        self,
        workflow_id: UUID,
        workflow_state: WorkflowState,
        runtime_payload: RuntimeStatePayload,
        stage: RuntimeStage,
        exc: Exception,
        *,
        actor_type: str | None,
        actor_id: UUID | None,
    ) -> WorkflowState:
        await self._append_node_event(
            workflow_id,
            stage,
            "workflow.node.failed",
            WorkflowEventStatus.FAILED,
            actor_type=actor_type,
            actor_id=actor_id,
            workflow_status=workflow_state.status,
            message=f"Runtime stage {stage.value} failed.",
            payload=self._safe_runtime_error_payload(exc),
        )
        await self._append_runtime_failed_event(
            workflow_id,
            actor_type=actor_type,
            actor_id=actor_id,
            message="Workflow runtime failed.",
            payload={
                "failed_stage": stage.value,
                "status": workflow_state.status.value,
                **self._safe_runtime_error_payload(exc),
            },
        )

        failed_workflow_state = await self._transition_to_failed_if_allowed(
            workflow_id,
            workflow_state,
            actor_type=actor_type,
            actor_id=actor_id,
            reason=f"Runtime failed during {stage.value} stage.",
        )
        runtime_state = RuntimeWorkflowState.model_validate(runtime_payload).model_copy(
            update={
                "status": failed_workflow_state.status,
                "failed_stage": stage,
                "error": WorkflowError(
                    code="RUNTIME_NODE_FAILED",
                    message=f"Runtime stage {stage.value} failed.",
                    failed_step=stage.value,
                    retryable=False,
                    details=self._safe_runtime_error_payload(exc),
                ),
            },
        )
        updated_state = runtime_state_to_workflow_state(
            runtime_state,
            failed_workflow_state,
        )
        return await self.workflow_service.update_workflow_state(
            workflow_id,
            updated_state,
            actor_type=actor_type,
            actor_id=actor_id,
            reason="Runtime persisted failure state.",
        )

    async def _transition_to_failed_if_allowed(
        self,
        workflow_id: UUID,
        workflow_state: WorkflowState,
        *,
        actor_type: str | None,
        actor_id: UUID | None,
        reason: str,
    ) -> WorkflowState:
        try:
            return await self.workflow_service.transition_workflow_status(
                workflow_id,
                WorkflowStatus.FAILED,
                actor_type=actor_type,
                actor_id=actor_id,
                reason=reason,
            )
        except InvalidWorkflowTransitionError:
            return workflow_state

    async def _append_runtime_failed_event(
        self,
        workflow_id: UUID,
        *,
        actor_type: str | None,
        actor_id: UUID | None,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        await self._append_runtime_event(
            workflow_id,
            "workflow.runtime.failed",
            WorkflowEventStatus.FAILED,
            actor_type=actor_type,
            actor_id=actor_id,
            message=message,
            payload=payload,
        )

    async def _append_runtime_event(
        self,
        workflow_id: UUID,
        event_type: str,
        status: WorkflowEventStatus,
        *,
        actor_type: str | None,
        actor_id: UUID | None,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        await self.workflow_event_service.append_event(
            WorkflowEventCreate(
                workflow_id=workflow_id,
                event_type=event_type,
                actor_type=actor_type,
                actor_id=actor_id,
                status=status,
                message=message,
                payload={"workflow_id": str(workflow_id), **payload},
            ),
        )

    async def _append_node_event(
        self,
        workflow_id: UUID,
        stage: RuntimeStage,
        event_type: str,
        status: WorkflowEventStatus,
        *,
        actor_type: str | None,
        actor_id: UUID | None,
        workflow_status: WorkflowStatus,
        message: str,
        stage_output: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event_payload: dict[str, Any] = {
            "workflow_id": str(workflow_id),
            "stage": stage.value,
            "workflow_status": workflow_status.value,
        }
        if stage_output:
            event_payload["stage_output"] = self._safe_stage_output(stage_output)
        if payload:
            event_payload.update(payload)

        await self.workflow_event_service.append_event(
            WorkflowEventCreate(
                workflow_id=workflow_id,
                event_type=event_type,
                actor_type=actor_type,
                actor_id=actor_id,
                agent_name=stage.value,
                status=status,
                message=message,
                payload=event_payload,
            ),
        )

    def _safe_stage_output(self, stage_output: dict[str, Any]) -> dict[str, Any]:
        safe_output = {
            "stage": stage_output.get("stage"),
            "status": stage_output.get("status"),
            "summary": stage_output.get("summary"),
            "placeholder": stage_output.get("placeholder"),
        }
        for key in (
            "llm_runtime_enabled",
            "llm_skipped",
            "llm_output_schema",
            "llm_provider",
            "llm_model",
            "llm_request_id",
            "llm_finish_reason",
        ):
            if key in stage_output:
                safe_output[key] = stage_output[key]
        return safe_output

    def _llm_stage_event_payload(self, stage: RuntimeStage) -> dict[str, Any]:
        if not self.llm_runtime_enabled:
            return {}
        return {
            "llm_runtime_enabled": True,
            "llm_stage_mode": (
                "deterministic_no_llm"
                if stage is RuntimeStage.QUOTATION
                else "structured_prompt"
            ),
        }

    def _safe_runtime_error_payload(self, exc: Exception) -> dict[str, Any]:
        payload: dict[str, Any] = {"error_type": type(exc).__name__}
        if isinstance(exc, LLMProviderError):
            payload["llm_error_category"] = exc.category.value
            if exc.provider is not None:
                payload["llm_provider"] = exc.provider.value
            if exc.request_id is not None:
                payload["llm_request_id"] = exc.request_id
        elif isinstance(exc.__cause__, LLMProviderError):
            cause = exc.__cause__
            payload["llm_error_category"] = cause.category.value
            if cause.provider is not None:
                payload["llm_provider"] = cause.provider.value
            if cause.request_id is not None:
                payload["llm_request_id"] = cause.request_id
        if payload.get("llm_error_category") == LLMErrorCategory.INVALID_RESPONSE.value:
            payload["retryable"] = False
        return payload


__all__ = [
    "PRE_APPROVAL_RUNTIME_STAGES",
    "RUNTIME_STAGE_STATUSES",
    "RuntimeService",
    "WorkflowRuntimeError",
    "WorkflowRuntimeNodeError",
    "WorkflowRuntimePreconditionError",
]
