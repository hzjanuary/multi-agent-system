"""Deterministic no-LLM runtime node handlers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.runtime.graph import RuntimeNodeHandler
from app.runtime.schemas import RuntimeStage, RuntimeWorkflowState

_STAGE_SUMMARIES: Mapping[RuntimeStage, str] = {
    RuntimeStage.PLANNER: (
        "Deterministic planner placeholder recorded workflow planning stage."
    ),
    RuntimeStage.RETRIEVAL: (
        "Deterministic retrieval placeholder recorded retrieval stage without "
        "external lookup."
    ),
    RuntimeStage.QUOTATION: (
        "Deterministic quotation placeholder recorded quotation stage without "
        "pricing calculation."
    ),
    RuntimeStage.COMPLIANCE: (
        "Deterministic compliance placeholder recorded compliance stage without "
        "policy evaluation."
    ),
    RuntimeStage.VALIDATION: (
        "Deterministic validation placeholder recorded validation stage without "
        "business rule enforcement."
    ),
    RuntimeStage.APPROVAL: (
        "Deterministic approval placeholder recorded approval wait stage without "
        "approval decision."
    ),
    RuntimeStage.EMAIL_PREPARATION: (
        "Deterministic email preparation placeholder recorded email stage without "
        "sending email."
    ),
}


def run_planner_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic planner placeholder output."""
    return _complete_stage(state, RuntimeStage.PLANNER)


def run_retrieval_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic retrieval placeholder output."""
    return _complete_stage(state, RuntimeStage.RETRIEVAL)


def run_quotation_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic quotation placeholder output."""
    return _complete_stage(state, RuntimeStage.QUOTATION)


def run_compliance_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic compliance placeholder output."""
    return _complete_stage(state, RuntimeStage.COMPLIANCE)


def run_validation_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic validation placeholder output."""
    return _complete_stage(state, RuntimeStage.VALIDATION)


def run_approval_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic approval placeholder output without approving."""
    return _complete_stage(
        state,
        RuntimeStage.APPROVAL,
        extra_output={"approval_decision_made": False},
    )


def run_email_preparation_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
    """Record deterministic email placeholder output without sending email."""
    return _complete_stage(
        state,
        RuntimeStage.EMAIL_PREPARATION,
        extra_output={"email_sent": False},
    )


def create_deterministic_node_handlers() -> dict[RuntimeStage, RuntimeNodeHandler]:
    """Return a complete runtime stage to deterministic handler mapping."""
    return {
        RuntimeStage.PLANNER: run_planner_node,
        RuntimeStage.RETRIEVAL: run_retrieval_node,
        RuntimeStage.QUOTATION: run_quotation_node,
        RuntimeStage.COMPLIANCE: run_compliance_node,
        RuntimeStage.VALIDATION: run_validation_node,
        RuntimeStage.APPROVAL: run_approval_node,
        RuntimeStage.EMAIL_PREPARATION: run_email_preparation_node,
    }


def _complete_stage(
    state: RuntimeWorkflowState,
    stage: RuntimeStage,
    *,
    extra_output: dict[str, Any] | None = None,
) -> RuntimeWorkflowState:
    stage_output = _stage_output(state, stage)
    if extra_output:
        stage_output.update(extra_output)

    completed_stages = state.completed_stages
    if stage not in completed_stages:
        completed_stages = (*completed_stages, stage)

    stage_outputs = {
        existing_stage: dict(output)
        for existing_stage, output in state.stage_outputs.items()
    }
    stage_outputs[stage] = stage_output

    runtime_context = dict(state.runtime_context)
    runtime_context["last_completed_stage"] = stage.value
    runtime_context["deterministic_runtime"] = True

    outputs = dict(state.outputs)
    output_stage_outputs = _output_stage_outputs(outputs)
    output_stage_outputs[stage.value] = dict(stage_output)
    outputs["stage_outputs"] = output_stage_outputs
    outputs["last_completed_stage"] = stage.value

    return state.model_copy(
        update={
            "current_stage": stage,
            "completed_stages": completed_stages,
            "runtime_context": runtime_context,
            "stage_outputs": stage_outputs,
            "outputs": outputs,
        },
    )


def _stage_output(
    state: RuntimeWorkflowState,
    stage: RuntimeStage,
) -> dict[str, Any]:
    return {
        "stage": stage.value,
        "status": "completed",
        "summary": _STAGE_SUMMARIES[stage],
        "placeholder": True,
        "request_present": bool(state.request),
        "customer_present": bool(state.customer),
        "items_present": bool(state.items),
    }


def _output_stage_outputs(outputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_stage_outputs = outputs.get("stage_outputs")
    if not isinstance(raw_stage_outputs, dict):
        return {}

    stage_outputs: dict[str, dict[str, Any]] = {}
    for stage_value, output in raw_stage_outputs.items():
        if isinstance(stage_value, str) and isinstance(output, dict):
            stage_outputs[stage_value] = dict(output)
    return stage_outputs


__all__ = [
    "create_deterministic_node_handlers",
    "run_approval_node",
    "run_compliance_node",
    "run_email_preparation_node",
    "run_planner_node",
    "run_quotation_node",
    "run_retrieval_node",
    "run_validation_node",
]
