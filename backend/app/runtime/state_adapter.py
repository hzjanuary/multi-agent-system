"""Pure adapters between persisted workflow state and runtime state."""

from __future__ import annotations

from typing import Any

from app.runtime.schemas import RuntimeStage, RuntimeWorkflowState
from app.workflows.schemas import WorkflowState

_STAGE_TO_WORKFLOW_SECTION: dict[RuntimeStage, str] = {
    RuntimeStage.PLANNER: "planner",
    RuntimeStage.RETRIEVAL: "retrieval",
    RuntimeStage.QUOTATION: "quotation",
    RuntimeStage.COMPLIANCE: "compliance",
    RuntimeStage.VALIDATION: "validation",
    RuntimeStage.APPROVAL: "approval",
    RuntimeStage.EMAIL_PREPARATION: "email",
}

_INITIAL_STAGE_MARKERS = frozenset(
    {
        "",
        "created",
        "not_started",
        "not started",
        "not-started",
        "none",
        "null",
    },
)


class RuntimeStateAdapterError(Exception):
    """Raised when persisted workflow state cannot be converted for runtime."""


def workflow_state_to_runtime_state(state: WorkflowState) -> RuntimeWorkflowState:
    """Convert persisted WorkflowState into a runtime-compatible state copy."""
    runtime_context = dict(state.runtime_context)

    return RuntimeWorkflowState(
        workflow_id=state.workflow_id,
        workflow_type=state.workflow_type,
        domain=state.domain,
        status=state.status,
        request=dict(state.request),
        metadata=state.metadata,
        customer=dict(state.customer),
        items=[dict(item) for item in state.items],
        current_stage=_stage_or_none(state.current_step),
        completed_stages=_stages_from_values(
            runtime_context.get("completed_stages", ()),
            field_name="completed_stages",
        ),
        failed_stage=_stage_or_none(runtime_context.get("failed_stage")),
        runtime_context=runtime_context,
        stage_outputs=_stage_outputs_from_workflow_state(state),
        outputs=dict(state.outputs),
        steps=list(state.steps),
        error=state.error,
        retry_count=state.retry_count,
        events=[dict(event) for event in state.events],
    )


def runtime_state_to_workflow_state(
    runtime_state: RuntimeWorkflowState,
    workflow_state: WorkflowState,
) -> WorkflowState:
    """Return an updated WorkflowState copy from runtime state output."""
    runtime_context = dict(runtime_state.runtime_context)
    runtime_context["completed_stages"] = [
        stage.value for stage in runtime_state.completed_stages
    ]
    if runtime_state.failed_stage is None:
        runtime_context.pop("failed_stage", None)
    else:
        runtime_context["failed_stage"] = runtime_state.failed_stage.value

    outputs = dict(runtime_state.outputs)
    outputs["stage_outputs"] = {
        stage.value: dict(output)
        for stage, output in runtime_state.stage_outputs.items()
        if output
    }

    stage_section_updates = _workflow_section_updates(runtime_state)
    return workflow_state.model_copy(
        update={
            "workflow_id": runtime_state.workflow_id,
            "workflow_type": runtime_state.workflow_type,
            "domain": runtime_state.domain,
            "status": runtime_state.status,
            "request": dict(runtime_state.request),
            "metadata": runtime_state.metadata,
            "customer": dict(runtime_state.customer),
            "items": [dict(item) for item in runtime_state.items],
            "current_step": (
                runtime_state.current_stage.value
                if runtime_state.current_stage is not None
                else None
            ),
            "runtime_context": runtime_context,
            "outputs": outputs,
            "steps": list(runtime_state.steps),
            "error": runtime_state.error,
            "retry_count": runtime_state.retry_count,
            "events": [dict(event) for event in runtime_state.events],
            **stage_section_updates,
        },
    )


def _stage_outputs_from_workflow_state(
    state: WorkflowState,
) -> dict[RuntimeStage, dict[str, Any]]:
    outputs: dict[RuntimeStage, dict[str, Any]] = {}
    raw_stage_outputs = state.outputs.get("stage_outputs", {})
    if isinstance(raw_stage_outputs, dict):
        for stage_value, output in raw_stage_outputs.items():
            stage = _runtime_stage_from_value(
                stage_value,
                field_name="outputs.stage_outputs",
                allow_initial=False,
            )
            if stage is None:
                raise RuntimeStateAdapterError(
                    "outputs.stage_outputs cannot contain an initial workflow marker",
                )
            outputs[stage] = dict(output) if isinstance(output, dict) else {}

    for stage, section_name in _STAGE_TO_WORKFLOW_SECTION.items():
        section_output = getattr(state, section_name)
        if section_output:
            outputs[stage] = dict(section_output)

    return outputs


def _workflow_section_updates(
    runtime_state: RuntimeWorkflowState,
) -> dict[str, dict[str, Any]]:
    updates: dict[str, dict[str, Any]] = {}
    for stage, output in runtime_state.stage_outputs.items():
        section_name = _STAGE_TO_WORKFLOW_SECTION[stage]
        updates[section_name] = dict(output)
    return updates


def _stage_or_none(value: Any) -> RuntimeStage | None:
    return _runtime_stage_from_value(
        value,
        field_name="current_step",
        allow_initial=True,
    )


def _runtime_stage_from_value(
    value: Any,
    *,
    field_name: str,
    allow_initial: bool,
) -> RuntimeStage | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeStateAdapterError(f"{field_name} must be a runtime stage string")

    normalized = value.strip().lower().replace("-", "_")
    if allow_initial and normalized in _INITIAL_STAGE_MARKERS:
        return None

    for stage in RuntimeStage:
        if normalized == stage.value:
            return stage

    raise RuntimeStateAdapterError(
        f"{field_name} contains unknown runtime stage: {value}",
    )


def _stages_from_values(values: Any, *, field_name: str) -> tuple[RuntimeStage, ...]:
    if values in (None, ""):
        return ()
    if isinstance(values, str):
        raise TypeError(f"{field_name} must be a sequence of runtime stages")
    stages: list[RuntimeStage] = []
    for value in values:
        stage = _runtime_stage_from_value(
            value,
            field_name=field_name,
            allow_initial=False,
        )
        if stage is None:
            raise RuntimeStateAdapterError(
                f"{field_name} cannot contain an initial workflow marker",
            )
        stages.append(stage)
    return tuple(stages)
