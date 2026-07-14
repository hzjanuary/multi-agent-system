"""Tests for pure approval lifecycle rules."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

import pytest

from app.approvals import (
    ApprovalDecisionType,
    ApprovalInvalidStateError,
    ApprovalRecord,
    ApprovalTerminalStateError,
    DuplicateFinalApprovalDecisionError,
    ResumeNotAllowedError,
    get_allowed_approval_decisions,
    get_next_status_for_decision,
    get_resume_allowed_after_decision,
    has_final_approval_decision,
    is_final_approval_decision,
    validate_approval_decision_allowed,
    validate_resume_allowed,
)
from app.models.enums import WorkflowStatus


def _record(decision: ApprovalDecisionType) -> ApprovalRecord:
    next_status = {
        ApprovalDecisionType.APPROVE: WorkflowStatus.APPROVED,
        ApprovalDecisionType.REJECT: WorkflowStatus.REJECTED,
        ApprovalDecisionType.REQUEST_CHANGES: None,
    }[decision]
    return ApprovalRecord(
        decision_id=uuid4(),
        workflow_id=uuid4(),
        decision=decision,
        actor_id=uuid4(),
        actor_roles=("Manager",),
        comment="Decision comment.",
        decided_at=datetime(2026, 7, 14, tzinfo=UTC),
        previous_status=WorkflowStatus.WAITING_APPROVAL,
        next_status=next_status,
    )


@pytest.mark.parametrize(
    "decision",
    (ApprovalDecisionType.APPROVE, ApprovalDecisionType.REJECT),
)
def test_approve_and_reject_are_final(decision: ApprovalDecisionType) -> None:
    assert is_final_approval_decision(decision) is True
    assert has_final_approval_decision([_record(decision)]) is True


def test_request_changes_is_non_final() -> None:
    assert is_final_approval_decision(ApprovalDecisionType.REQUEST_CHANGES) is False
    assert (
        has_final_approval_decision(
            [_record(ApprovalDecisionType.REQUEST_CHANGES)],
        )
        is False
    )


def test_approval_decisions_allowed_only_while_waiting_approval() -> None:
    allowed = get_allowed_approval_decisions(WorkflowStatus.WAITING_APPROVAL)

    assert allowed == set(ApprovalDecisionType)
    validate_approval_decision_allowed(
        status=WorkflowStatus.WAITING_APPROVAL,
        decision=ApprovalDecisionType.APPROVE,
    )


@pytest.mark.parametrize(
    "status",
    (
        WorkflowStatus.CREATED,
        WorkflowStatus.PLANNING,
        WorkflowStatus.APPROVED,
        WorkflowStatus.GENERATING_EMAIL,
    ),
)
def test_non_waiting_status_rejects_approval_decisions(
    status: WorkflowStatus,
) -> None:
    assert get_allowed_approval_decisions(status) == set()

    with pytest.raises(ApprovalInvalidStateError) as exc_info:
        validate_approval_decision_allowed(
            status=status,
            decision=ApprovalDecisionType.APPROVE,
        )

    assert exc_info.value.status is status


@pytest.mark.parametrize(
    "status",
    (
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
        WorkflowStatus.REJECTED,
    ),
)
def test_terminal_status_rejects_approval_mutations(status: WorkflowStatus) -> None:
    with pytest.raises(ApprovalTerminalStateError) as exc_info:
        validate_approval_decision_allowed(
            status=status,
            decision=ApprovalDecisionType.APPROVE,
        )

    assert exc_info.value.status is status


def test_duplicate_final_decision_is_rejected() -> None:
    records = [_record(ApprovalDecisionType.APPROVE)]

    with pytest.raises(DuplicateFinalApprovalDecisionError):
        validate_approval_decision_allowed(
            status=WorkflowStatus.WAITING_APPROVAL,
            decision=ApprovalDecisionType.REJECT,
            records=records,
        )

    assert (
        get_allowed_approval_decisions(
            WorkflowStatus.WAITING_APPROVAL,
            records,
        )
        == set()
    )


def test_request_changes_does_not_block_later_final_decision() -> None:
    records = [_record(ApprovalDecisionType.REQUEST_CHANGES)]

    validate_approval_decision_allowed(
        status=WorkflowStatus.WAITING_APPROVAL,
        decision=ApprovalDecisionType.APPROVE,
        records=records,
    )


def test_next_status_mapping_matches_current_lifecycle() -> None:
    assert (
        get_next_status_for_decision(ApprovalDecisionType.APPROVE)
        is WorkflowStatus.APPROVED
    )
    assert (
        get_next_status_for_decision(ApprovalDecisionType.REJECT)
        is WorkflowStatus.REJECTED
    )
    assert get_next_status_for_decision(ApprovalDecisionType.REQUEST_CHANGES) is None


def test_resume_requires_approved_status_and_approval_record() -> None:
    approved_record = _record(ApprovalDecisionType.APPROVE)

    assert (
        get_resume_allowed_after_decision(
            status=WorkflowStatus.APPROVED,
            records=[approved_record],
        )
        is True
    )
    validate_resume_allowed(
        status=WorkflowStatus.APPROVED,
        records=[approved_record],
    )


@pytest.mark.parametrize(
    "status",
    (
        WorkflowStatus.WAITING_APPROVAL,
        WorkflowStatus.REJECTED,
        WorkflowStatus.COMPLETED,
    ),
)
def test_resume_rejects_non_approved_or_terminal_statuses(
    status: WorkflowStatus,
) -> None:
    with pytest.raises(ResumeNotAllowedError):
        validate_resume_allowed(
            status=status,
            records=[_record(ApprovalDecisionType.APPROVE)],
        )


def test_unknown_status_inputs_are_rejected() -> None:
    invalid_status = cast(WorkflowStatus, "WAITING_APPROVAL")

    with pytest.raises(TypeError, match="status must be a WorkflowStatus"):
        get_allowed_approval_decisions(invalid_status)
