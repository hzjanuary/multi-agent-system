"""Approval lifecycle exceptions."""

from app.models.enums import WorkflowStatus


class ApprovalLifecycleError(Exception):
    """Base class for approval lifecycle errors."""


class ApprovalInvalidStateError(ApprovalLifecycleError):
    """Raised when an approval decision is not allowed for a status."""

    def __init__(self, *, status: WorkflowStatus) -> None:
        message = f"Approval decisions require WAITING_APPROVAL, got {status.value}."
        super().__init__(message)
        self.status = status


class ApprovalTerminalStateError(ApprovalLifecycleError):
    """Raised when approval mutation is attempted for a terminal workflow."""

    def __init__(self, *, status: WorkflowStatus) -> None:
        message = (
            f"Approval decisions are not allowed for terminal status {status.value}."
        )
        super().__init__(message)
        self.status = status


class DuplicateFinalApprovalDecisionError(ApprovalLifecycleError):
    """Raised when a workflow already has a final approval decision."""


class ResumeNotAllowedError(ApprovalLifecycleError):
    """Raised when workflow resume is not allowed for the current status."""

    def __init__(self, *, status: WorkflowStatus) -> None:
        message = f"Workflow resume requires APPROVED, got {status.value}."
        super().__init__(message)
        self.status = status
