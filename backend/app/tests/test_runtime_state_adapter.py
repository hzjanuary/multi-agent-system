"""Tests for runtime state adapter contracts."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.models.enums import WorkflowStatus
from app.runtime import (
    RUNTIME_STAGES,
    RuntimeStage,
    RuntimeStateAdapterError,
    RuntimeWorkflowState,
    runtime_stage_values,
    runtime_state_to_workflow_state,
    workflow_state_to_runtime_state,
)
from app.workflows.schemas import WorkflowError, WorkflowState, WorkflowType


def _workflow_state() -> WorkflowState:
    return WorkflowState(
        workflow_id="workflow-001",
        workflow_type=WorkflowType.PROCUREMENT_QUOTATION,
        domain="it_equipment",
        status=WorkflowStatus.PLANNING,
        request={"raw_text": "Need 50 laptops.", "source": "manual_text"},
        customer={"name": "Acme Manufacturing Group"},
        items=[{"name": "Laptop", "quantity": 50}],
        planner={"plan_id": "plan-001"},
        current_step="planner",
        runtime_context={
            "correlation_id": "runtime-001",
            "completed_stages": ["planner"],
        },
        outputs={"summary": "placeholder", "stage_outputs": {"planner": {"ok": True}}},
        retry_count=1,
        events=[{"event_type": "workflow.node.completed"}],
    )


def test_runtime_package_exports_contracts() -> None:
    assert RuntimeStage.PLANNER in RUNTIME_STAGES
    assert runtime_stage_values() == (
        "planner",
        "retrieval",
        "quotation",
        "compliance",
        "validation",
        "approval",
        "email_preparation",
    )


def test_workflow_state_to_runtime_state_preserves_fields() -> None:
    state = _workflow_state()

    runtime_state = workflow_state_to_runtime_state(state)
    data = runtime_state.model_dump(mode="json")

    assert runtime_state.workflow_id == state.workflow_id
    assert runtime_state.workflow_type is state.workflow_type
    assert runtime_state.domain == state.domain
    assert runtime_state.status is state.status
    assert runtime_state.request == state.request
    assert runtime_state.metadata == state.metadata
    assert runtime_state.current_stage is RuntimeStage.PLANNER
    assert runtime_state.completed_stages == (RuntimeStage.PLANNER,)
    assert runtime_state.stage_outputs[RuntimeStage.PLANNER] == {"plan_id": "plan-001"}
    assert runtime_state.outputs == state.outputs
    assert runtime_state.retry_count == state.retry_count
    assert data["current_stage"] == "planner"
    assert data["stage_outputs"]["planner"] == {"plan_id": "plan-001"}


def test_runtime_state_to_workflow_state_round_trip_preserves_existing_state() -> None:
    state = _workflow_state()
    runtime_state = workflow_state_to_runtime_state(state)
    updated_runtime_state = runtime_state.model_copy(
        update={
            "status": WorkflowStatus.WAITING_APPROVAL,
            "current_stage": RuntimeStage.APPROVAL,
            "completed_stages": (
                RuntimeStage.PLANNER,
                RuntimeStage.RETRIEVAL,
                RuntimeStage.QUOTATION,
                RuntimeStage.COMPLIANCE,
                RuntimeStage.VALIDATION,
            ),
            "stage_outputs": {
                **runtime_state.stage_outputs,
                RuntimeStage.RETRIEVAL: {"documents_found": 0},
                RuntimeStage.APPROVAL: {"approval_required": True},
            },
            "runtime_context": {
                **runtime_state.runtime_context,
                "run_id": "run-001",
            },
        },
    )

    updated_state = runtime_state_to_workflow_state(updated_runtime_state, state)

    assert updated_state.workflow_id == state.workflow_id
    assert updated_state.workflow_type is state.workflow_type
    assert updated_state.domain == state.domain
    assert updated_state.request == state.request
    assert updated_state.metadata == state.metadata
    assert updated_state.status is WorkflowStatus.WAITING_APPROVAL
    assert updated_state.current_step == "approval"
    assert updated_state.runtime_context["completed_stages"] == [
        "planner",
        "retrieval",
        "quotation",
        "compliance",
        "validation",
    ]
    assert updated_state.runtime_context["run_id"] == "run-001"
    assert updated_state.outputs["stage_outputs"]["approval"] == {
        "approval_required": True,
    }
    assert updated_state.planner == {"plan_id": "plan-001"}
    assert updated_state.retrieval == {"documents_found": 0}
    assert updated_state.approval == {"approval_required": True}
    assert updated_state.retry_count == 1


def test_runtime_state_adapter_does_not_mutate_inputs() -> None:
    state = _workflow_state()
    original_state_dump = deepcopy(state.model_dump(mode="json"))

    runtime_state = workflow_state_to_runtime_state(state)
    updated_runtime_state = runtime_state.model_copy(
        update={
            "current_stage": RuntimeStage.RETRIEVAL,
            "completed_stages": (RuntimeStage.PLANNER,),
            "stage_outputs": {
                RuntimeStage.PLANNER: {"changed": True},
                RuntimeStage.RETRIEVAL: {"documents_found": 0},
            },
        },
    )
    updated_state = runtime_state_to_workflow_state(updated_runtime_state, state)

    assert state.model_dump(mode="json") == original_state_dump
    assert runtime_state.stage_outputs[RuntimeStage.PLANNER] == {
        "plan_id": "plan-001",
    }
    assert updated_state is not state
    assert updated_state.planner == {"changed": True}


def test_runtime_state_rejects_invalid_current_stage() -> None:
    with pytest.raises(ValidationError):
        RuntimeWorkflowState.model_validate(
            {
                "workflow_id": "workflow-001",
                "workflow_type": "procurement_quotation",
                "status": "CREATED",
                "current_stage": "unknown",
            },
        )


def test_runtime_adapter_rejects_invalid_workflow_current_step() -> None:
    state = _workflow_state().model_copy(update={"current_step": "unknown"})

    with pytest.raises(RuntimeStateAdapterError, match="unknown"):
        workflow_state_to_runtime_state(state)


@pytest.mark.parametrize(
    "current_step",
    [None, "", "created", "CREATED", "not_started", "Not started"],
)
def test_workflow_state_to_runtime_state_accepts_not_started_markers(
    current_step: str | None,
) -> None:
    state = _workflow_state().model_copy(
        update={
            "status": WorkflowStatus.CREATED,
            "current_step": current_step,
            "runtime_context": {},
        },
    )

    runtime_state = workflow_state_to_runtime_state(state)

    assert runtime_state.current_stage is None
    assert runtime_state.status is WorkflowStatus.CREATED


@pytest.mark.parametrize(
    ("current_step", "expected_stage"),
    [
        ("planner", RuntimeStage.PLANNER),
        ("PLANNER", RuntimeStage.PLANNER),
        ("Email_Preparation", RuntimeStage.EMAIL_PREPARATION),
    ],
)
def test_workflow_state_to_runtime_state_accepts_case_insensitive_stages(
    current_step: str,
    expected_stage: RuntimeStage,
) -> None:
    state = _workflow_state().model_copy(update={"current_step": current_step})

    runtime_state = workflow_state_to_runtime_state(state)

    assert runtime_state.current_stage is expected_stage


def test_runtime_adapter_accepts_case_insensitive_completed_stages() -> None:
    state = _workflow_state().model_copy(
        update={"runtime_context": {"completed_stages": ["PLANNER", "retrieval"]}},
    )

    runtime_state = workflow_state_to_runtime_state(state)

    assert runtime_state.completed_stages == (
        RuntimeStage.PLANNER,
        RuntimeStage.RETRIEVAL,
    )


def test_runtime_state_supports_error_and_failed_stage() -> None:
    state = _workflow_state().model_copy(
        update={
            "status": WorkflowStatus.FAILED,
            "current_step": "retrieval",
            "runtime_context": {"failed_stage": "retrieval"},
            "error": WorkflowError(
                code="RUNTIME_NODE_FAILED",
                message="Retrieval placeholder failed.",
                failed_step="retrieval",
            ),
        },
    )

    runtime_state = workflow_state_to_runtime_state(state)

    assert runtime_state.failed_stage is RuntimeStage.RETRIEVAL
    assert runtime_state.error is not None
    assert runtime_state.error.code == "RUNTIME_NODE_FAILED"
