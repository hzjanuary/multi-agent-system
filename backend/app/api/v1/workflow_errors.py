"""Workflow API error mapping helpers."""

from dataclasses import dataclass
from typing import Any, NoReturn

from fastapi import HTTPException, status

from app.schemas.workflows_api import WorkflowApiErrorDetail
from app.workflows.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowEventNotFoundError,
    WorkflowNotFoundError,
    WorkflowStateMismatchError,
)


@dataclass(frozen=True, slots=True)
class WorkflowApiErrorMapping:
    """HTTP status and safe response detail for a known workflow error."""

    status_code: int
    detail: WorkflowApiErrorDetail


def map_workflow_exception(error: Exception) -> WorkflowApiErrorMapping | None:
    """Map known workflow exceptions to HTTP status/detail data.

    Invalid transitions use 409 Conflict because the requested status can be a
    valid enum value while still conflicting with the workflow's current
    lifecycle state.
    """
    if isinstance(error, WorkflowNotFoundError):
        return WorkflowApiErrorMapping(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WorkflowApiErrorDetail(
                code="workflow_not_found",
                message=str(error),
            ),
        )

    if isinstance(error, WorkflowEventNotFoundError):
        return WorkflowApiErrorMapping(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WorkflowApiErrorDetail(
                code="workflow_event_not_found",
                message=str(error),
            ),
        )

    if isinstance(error, InvalidWorkflowTransitionError):
        return WorkflowApiErrorMapping(
            status_code=status.HTTP_409_CONFLICT,
            detail=WorkflowApiErrorDetail(
                code="invalid_workflow_transition",
                message=str(error),
                details={
                    "from_status": error.from_status.value,
                    "to_status": error.to_status.value,
                    "allowed_statuses": sorted(
                        status_value.value for status_value in error.allowed_statuses
                    ),
                },
            ),
        )

    if isinstance(error, WorkflowStateMismatchError):
        return WorkflowApiErrorMapping(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=WorkflowApiErrorDetail(
                code="workflow_state_mismatch",
                message=str(error),
            ),
        )

    return None


def workflow_http_exception(error: Exception) -> HTTPException:
    """Create an HTTPException for a known workflow error.

    Unknown exceptions are re-raised so callers do not accidentally swallow
    unexpected failures.
    """
    mapping = map_workflow_exception(error)
    if mapping is None:
        raise error

    return HTTPException(
        status_code=mapping.status_code,
        detail=mapping.detail.model_dump(mode="json"),
    )


def raise_workflow_http_exception(error: Exception) -> NoReturn:
    """Raise an HTTPException for a known workflow error."""
    raise workflow_http_exception(error)


def workflow_error_detail(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-compatible workflow error detail payload."""
    return WorkflowApiErrorDetail(
        code=code,
        message=message,
        details=details or {},
    ).model_dump(mode="json")
