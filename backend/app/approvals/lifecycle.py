"""Pure approval lifecycle rule helpers."""

from collections.abc import Iterable

from app.approvals.exceptions import (
    ApprovalInvalidStateError,
    ApprovalTerminalStateError,
    DuplicateFinalApprovalDecisionError,
    ResumeNotAllowedError,
)
from app.approvals.schemas import ApprovalDecisionType, ApprovalRecord
from app.models.enums import WorkflowStatus
from app.workflows.lifecycle import is_terminal_status

APPROVAL_WAITING_STATUS = WorkflowStatus.WAITING_APPROVAL
APPROVAL_APPROVED_STATUS = WorkflowStatus.APPROVED

FINAL_APPROVAL_DECISIONS: frozenset[ApprovalDecisionType] = frozenset(
    {
        ApprovalDecisionType.APPROVE,
        ApprovalDecisionType.REJECT,
    },
)

NON_FINAL_APPROVAL_DECISIONS: frozenset[ApprovalDecisionType] = frozenset(
    {
        ApprovalDecisionType.REQUEST_CHANGES,
    },
)

APPROVAL_DECISION_NEXT_STATUS: dict[ApprovalDecisionType, WorkflowStatus | None] = {
    ApprovalDecisionType.APPROVE: WorkflowStatus.APPROVED,
    ApprovalDecisionType.REJECT: WorkflowStatus.REJECTED,
    ApprovalDecisionType.REQUEST_CHANGES: None,
}


def is_final_approval_decision(decision: ApprovalDecisionType) -> bool:
    """Return whether a decision closes the approval decision window."""
    return decision in FINAL_APPROVAL_DECISIONS


def has_final_approval_decision(records: Iterable[ApprovalRecord]) -> bool:
    """Return whether approval history already contains a final decision."""
    return any(is_final_approval_decision(record.decision) for record in records)


def get_allowed_approval_decisions(
    status: WorkflowStatus,
    records: Iterable[ApprovalRecord] = (),
) -> set[ApprovalDecisionType]:
    """Return currently allowed approval decisions for a workflow."""
    _require_workflow_status(status)
    if status is not APPROVAL_WAITING_STATUS:
        return set()
    if has_final_approval_decision(records):
        return set()
    return set(ApprovalDecisionType)


def get_next_status_for_decision(
    decision: ApprovalDecisionType,
) -> WorkflowStatus | None:
    """Return the lifecycle status implied by a decision, if any."""
    return APPROVAL_DECISION_NEXT_STATUS[decision]


def validate_approval_decision_allowed(
    *,
    status: WorkflowStatus,
    decision: ApprovalDecisionType,
    records: Iterable[ApprovalRecord] = (),
) -> None:
    """Raise if an approval decision is invalid for status/history."""
    _require_workflow_status(status)
    if is_terminal_status(status):
        raise ApprovalTerminalStateError(status=status)
    if status is not APPROVAL_WAITING_STATUS:
        raise ApprovalInvalidStateError(status=status)
    if is_final_approval_decision(decision) and has_final_approval_decision(records):
        raise DuplicateFinalApprovalDecisionError(
            "Workflow already has a final approval decision.",
        )


def get_resume_allowed_after_decision(
    *,
    status: WorkflowStatus,
    records: Iterable[ApprovalRecord] = (),
) -> bool:
    """Return whether bounded workflow resume is allowed."""
    _require_workflow_status(status)
    return status is APPROVAL_APPROVED_STATUS and any(
        record.decision is ApprovalDecisionType.APPROVE for record in records
    )


def validate_resume_allowed(
    *,
    status: WorkflowStatus,
    records: Iterable[ApprovalRecord] = (),
) -> None:
    """Raise if bounded resume is not currently allowed."""
    if not get_resume_allowed_after_decision(status=status, records=records):
        raise ResumeNotAllowedError(status=status)


def _require_workflow_status(status: WorkflowStatus) -> None:
    if not isinstance(status, WorkflowStatus):
        raise TypeError("status must be a WorkflowStatus")
