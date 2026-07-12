"""Tests for deterministic runtime node handlers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from app.models.enums import WorkflowStatus
from app.runtime import (
    RUNTIME_STAGES,
    RuntimeNodeHandler,
    RuntimeStage,
    RuntimeStatePayload,
    RuntimeWorkflowState,
    build_workflow_graph,
    create_deterministic_node_handlers,
    run_approval_node,
    run_compliance_node,
    run_email_preparation_node,
    run_planner_node,
    run_quotation_node,
    run_retrieval_node,
    run_validation_node,
)
from app.workflows.schemas import WorkflowType

_HANDLER_CASES: tuple[tuple[RuntimeStage, RuntimeNodeHandler], ...] = (
    (RuntimeStage.PLANNER, run_planner_node),
    (RuntimeStage.RETRIEVAL, run_retrieval_node),
    (RuntimeStage.QUOTATION, run_quotation_node),
    (RuntimeStage.COMPLIANCE, run_compliance_node),
    (RuntimeStage.VALIDATION, run_validation_node),
    (RuntimeStage.APPROVAL, run_approval_node),
    (RuntimeStage.EMAIL_PREPARATION, run_email_preparation_node),
)


def _runtime_state() -> RuntimeWorkflowState:
    return RuntimeWorkflowState(
        workflow_id="workflow-001",
        workflow_type=WorkflowType.PROCUREMENT_QUOTATION,
        domain="it_equipment",
        status=WorkflowStatus.PLANNING,
        request={"raw_text": "Need business laptops.", "source": "manual_text"},
        customer={"name": "Acme Manufacturing Group"},
        items=[{"name": "Laptop", "quantity": 50}],
        runtime_context={"correlation_id": "runtime-001"},
        stage_outputs={RuntimeStage.PLANNER: {"existing": True}},
        outputs={"stage_outputs": {"planner": {"existing": True}}},
        retry_count=2,
    )


def _runtime_payload() -> RuntimeStatePayload:
    return {
        "workflow_id": "workflow-001",
        "workflow_type": WorkflowType.PROCUREMENT_QUOTATION.value,
        "domain": "it_equipment",
        "status": WorkflowStatus.PLANNING.value,
        "request": {"raw_text": "Need business laptops."},
        "customer": {"name": "Acme Manufacturing Group"},
        "items": [{"name": "Laptop", "quantity": 50}],
        "runtime_context": {"correlation_id": "runtime-001"},
        "retry_count": 2,
    }


def test_create_deterministic_node_handlers_covers_every_runtime_stage() -> None:
    handlers = create_deterministic_node_handlers()

    assert set(handlers) == set(RUNTIME_STAGES)
    assert tuple(handlers) == RUNTIME_STAGES


@pytest.mark.parametrize(("stage", "handler"), _HANDLER_CASES)
def test_runtime_node_records_json_compatible_stage_output(
    stage: RuntimeStage,
    handler: RuntimeNodeHandler,
) -> None:
    state = _runtime_state()
    original_state_dump = deepcopy(state.model_dump(mode="json"))

    updated_state = handler(state)
    updated_dump = updated_state.model_dump(mode="json")
    stage_output = updated_state.stage_outputs[stage]

    assert updated_state is not state
    assert state.model_dump(mode="json") == original_state_dump
    assert updated_state.current_stage is stage
    assert stage in updated_state.completed_stages
    assert stage_output["stage"] == stage.value
    assert stage_output["status"] == "completed"
    assert stage_output["placeholder"] is True
    assert stage_output["request_present"] is True
    assert stage_output["customer_present"] is True
    assert stage_output["items_present"] is True
    assert updated_dump["stage_outputs"][stage.value] == stage_output
    assert updated_dump["outputs"]["stage_outputs"][stage.value] == stage_output


@pytest.mark.parametrize(("stage", "handler"), _HANDLER_CASES)
def test_runtime_node_preserves_unrelated_fields(
    stage: RuntimeStage,
    handler: RuntimeNodeHandler,
) -> None:
    state = _runtime_state()

    updated_state = handler(state)

    assert updated_state.workflow_id == state.workflow_id
    assert updated_state.workflow_type is state.workflow_type
    assert updated_state.domain == state.domain
    assert updated_state.status is state.status
    assert updated_state.request == state.request
    assert updated_state.metadata == state.metadata
    assert updated_state.customer == state.customer
    assert updated_state.items == state.items
    assert updated_state.retry_count == state.retry_count
    assert updated_state.error == state.error
    assert updated_state.events == state.events
    assert updated_state.runtime_context["correlation_id"] == "runtime-001"
    assert updated_state.runtime_context["last_completed_stage"] == stage.value
    assert updated_state.runtime_context["deterministic_runtime"] is True


def test_runtime_node_does_not_duplicate_completed_stage() -> None:
    state = _runtime_state().model_copy(
        update={"completed_stages": (RuntimeStage.PLANNER,)},
    )

    updated_state = run_planner_node(state)

    assert updated_state.completed_stages == (RuntimeStage.PLANNER,)


def test_runtime_node_preserves_existing_stage_outputs() -> None:
    state = _runtime_state()

    updated_state = run_retrieval_node(state)

    assert updated_state.stage_outputs[RuntimeStage.PLANNER] == {"existing": True}
    assert updated_state.outputs["stage_outputs"]["planner"] == {"existing": True}
    assert updated_state.stage_outputs[RuntimeStage.RETRIEVAL]["stage"] == "retrieval"


def test_approval_node_does_not_make_approval_decision() -> None:
    updated_state = run_approval_node(_runtime_state())

    assert (
        updated_state.stage_outputs[RuntimeStage.APPROVAL]["approval_decision_made"]
        is False
    )


def test_email_preparation_node_does_not_send_email() -> None:
    updated_state = run_email_preparation_node(_runtime_state())

    assert (
        updated_state.stage_outputs[RuntimeStage.EMAIL_PREPARATION]["email_sent"]
        is False
    )


def test_deterministic_node_handlers_are_graph_compatible() -> None:
    graph = build_workflow_graph(create_deterministic_node_handlers())

    result = graph.invoke(_runtime_payload())
    stage_outputs = _require_dict(result["stage_outputs"])

    assert result["current_stage"] == RuntimeStage.EMAIL_PREPARATION.value
    assert result["completed_stages"] == [stage.value for stage in RUNTIME_STAGES]
    assert set(stage_outputs) == {stage.value for stage in RUNTIME_STAGES}
    assert result["runtime_context"]["last_completed_stage"] == "email_preparation"
    assert result["runtime_context"]["deterministic_runtime"] is True
    assert stage_outputs["approval"]["approval_decision_made"] is False
    assert stage_outputs["email_preparation"]["email_sent"] is False


def _require_dict(value: Any) -> dict[str, Any]:
    assert isinstance(value, dict)
    return value
