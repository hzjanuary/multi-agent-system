"""Tests for approval decision contracts."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.approvals import (
    APPROVAL_EVENT_NAMES,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalDecisionType,
    ApprovalHistoryResponse,
    ApprovalRecord,
    WorkflowResumeRequest,
    WorkflowResumeResponse,
)
from app.models.enums import WorkflowStatus


def _approval_record(
    *,
    decision: ApprovalDecisionType = ApprovalDecisionType.APPROVE,
    workflow_id: UUID | None = None,
) -> ApprovalRecord:
    return ApprovalRecord(
        decision_id=uuid4(),
        workflow_id=workflow_id or uuid4(),
        decision=decision,
        actor_id=uuid4(),
        actor_email="manager@example.test",
        actor_roles=("Manager",),
        comment="Reviewed for local demo approval.",
        decided_at=datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
        previous_status=WorkflowStatus.WAITING_APPROVAL,
        next_status=(
            WorkflowStatus.APPROVED
            if decision is ApprovalDecisionType.APPROVE
            else None
        ),
        request_id="approval-test",
        metadata={"source": "unit-test"},
    )


@pytest.mark.parametrize(
    "decision",
    (
        ApprovalDecisionType.APPROVE,
        ApprovalDecisionType.REJECT,
        ApprovalDecisionType.REQUEST_CHANGES,
    ),
)
def test_approval_decision_request_accepts_supported_decisions(
    decision: ApprovalDecisionType,
) -> None:
    request = ApprovalDecisionRequest(
        decision=decision,
        comment="Bounded reviewer comment.",
        request_id="request-001",
        metadata={"stage": "approval", "flags": ["demo"]},
    )

    assert request.decision is decision
    assert request.model_dump(mode="json")["decision"] == decision.value


def test_reject_decision_requires_comment() -> None:
    with pytest.raises(ValidationError, match="reject decisions require a comment"):
        ApprovalDecisionRequest(decision=ApprovalDecisionType.REJECT)


def test_comment_length_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            comment="x" * 2001,
        )


def test_metadata_must_be_json_compatible_and_bounded() -> None:
    with pytest.raises(ValidationError, match="JSON-compatible"):
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            metadata={"unsafe": object()},
        )

    with pytest.raises(ValidationError, match="more than 20 keys"):
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            metadata={f"k{i}": i for i in range(21)},
        )

    with pytest.raises(ValidationError, match="too long"):
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            metadata={"comment": "x" * 501},
        )


def test_approval_record_serializes_to_safe_json() -> None:
    record = _approval_record()
    data = record.model_dump(mode="json")

    assert data["decision"] == "approve"
    assert data["previous_status"] == "WAITING_APPROVAL"
    assert data["next_status"] == "APPROVED"
    assert data["actor_roles"] == ["Manager"]


def test_approval_record_bounds_actor_roles() -> None:
    with pytest.raises(ValidationError, match="more than 10 roles"):
        ApprovalRecord(
            **{
                **_approval_record().model_dump(),
                "actor_roles": tuple(f"Role{i}" for i in range(11)),
            },
        )


def test_approval_history_and_response_contracts_are_json_compatible() -> None:
    workflow_id = uuid4()
    record = _approval_record(workflow_id=workflow_id)

    response = ApprovalDecisionResponse(
        workflow_id=workflow_id,
        approval=record,
        previous_status=WorkflowStatus.WAITING_APPROVAL,
        next_status=WorkflowStatus.APPROVED,
        can_resume=True,
        resume_recommended=True,
    )
    history = ApprovalHistoryResponse(
        workflow_id=workflow_id,
        approvals=(record,),
        has_final_decision=True,
        can_resume=True,
    )

    assert response.model_dump(mode="json")["can_resume"] is True
    assert history.model_dump(mode="json")["approvals"][0]["decision"] == "approve"


def test_resume_contracts_are_bounded_and_serializable() -> None:
    workflow_id = uuid4()

    request = WorkflowResumeRequest(
        request_id="resume-001",
        metadata={"reason": "approved"},
    )
    response = WorkflowResumeResponse(
        workflow_id=workflow_id,
        previous_status=WorkflowStatus.APPROVED,
        next_status=WorkflowStatus.GENERATING_EMAIL,
        resumed=True,
        message="Resume accepted.",
        request_id=request.request_id,
    )

    assert request.model_dump(mode="json")["metadata"]["reason"] == "approved"
    assert response.model_dump(mode="json")["next_status"] == "GENERATING_EMAIL"


def test_approval_event_constants_are_stable_and_non_empty() -> None:
    assert len(APPROVAL_EVENT_NAMES) == len(set(APPROVAL_EVENT_NAMES))
    assert all(name.startswith("workflow.") for name in APPROVAL_EVENT_NAMES)
    assert "workflow.approval.approved" in APPROVAL_EVENT_NAMES
