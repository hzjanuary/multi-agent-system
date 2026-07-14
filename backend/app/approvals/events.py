"""Approval and resume event names for future WorkflowEvent persistence."""

APPROVAL_REQUESTED_EVENT = "workflow.approval.requested"
APPROVAL_APPROVED_EVENT = "workflow.approval.approved"
APPROVAL_REJECTED_EVENT = "workflow.approval.rejected"
APPROVAL_CHANGES_REQUESTED_EVENT = "workflow.approval.changes_requested"
WORKFLOW_RESUME_REQUESTED_EVENT = "workflow.resume_requested"
WORKFLOW_RESUMED_EVENT = "workflow.resumed"
WORKFLOW_RESUME_FAILED_EVENT = "workflow.resume_failed"

APPROVAL_EVENT_NAMES: tuple[str, ...] = (
    APPROVAL_REQUESTED_EVENT,
    APPROVAL_APPROVED_EVENT,
    APPROVAL_REJECTED_EVENT,
    APPROVAL_CHANGES_REQUESTED_EVENT,
    WORKFLOW_RESUME_REQUESTED_EVENT,
    WORKFLOW_RESUMED_EVENT,
    WORKFLOW_RESUME_FAILED_EVENT,
)
