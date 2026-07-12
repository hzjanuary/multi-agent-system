"""Workflow API request and response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import WorkflowStatus
from app.runtime.schemas import RuntimeWorkflowResult
from app.workflows.schemas import WorkflowEventRead, WorkflowState, WorkflowStateCreate


class WorkflowCreateRequest(WorkflowStateCreate):
    """Request body for creating a workflow."""


class WorkflowResponse(BaseModel):
    """Direct workflow API response model."""

    model_config = ConfigDict(frozen=True)

    workflow: WorkflowState


class WorkflowListResponse(BaseModel):
    """Response model for minimal workflow list endpoints."""

    model_config = ConfigDict(frozen=True)

    workflows: list[WorkflowState]
    count: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    status: WorkflowStatus | None = None


class WorkflowTransitionRequest(BaseModel):
    """Request body for transitioning workflow status."""

    model_config = ConfigDict(frozen=True)

    to_status: WorkflowStatus
    reason: str | None = Field(default=None, min_length=1, max_length=500)


class WorkflowStateUpdateRequest(BaseModel):
    """Request body for replacing a persisted workflow state payload."""

    model_config = ConfigDict(frozen=True)

    state: WorkflowState
    reason: str | None = Field(default=None, min_length=1, max_length=500)


class WorkflowEventResponse(BaseModel):
    """Direct workflow event API response model."""

    model_config = ConfigDict(frozen=True)

    event: WorkflowEventRead


class WorkflowEventListResponse(BaseModel):
    """Response model for minimal workflow event list endpoints."""

    model_config = ConfigDict(frozen=True)

    events: list[WorkflowEventRead]
    count: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class WorkflowRunResponse(BaseModel):
    """Direct response model for runtime workflow execution."""

    model_config = ConfigDict(frozen=True)

    result: RuntimeWorkflowResult
    workflow_id: str
    status: WorkflowStatus
    completed_stages: tuple[str, ...]
    waiting_for_approval: bool
    completed: bool
    failed: bool
    message: str | None = None

    @classmethod
    def from_runtime_result(
        cls,
        result: RuntimeWorkflowResult,
    ) -> "WorkflowRunResponse":
        """Build an API-safe response from a runtime service result."""
        return cls(
            result=result,
            workflow_id=result.state.workflow_id,
            status=result.state.status,
            completed_stages=tuple(
                stage.value for stage in result.state.completed_stages
            ),
            waiting_for_approval=result.state.status is WorkflowStatus.WAITING_APPROVAL,
            completed=result.completed,
            failed=result.failed,
            message=result.message,
        )


class WorkflowApiErrorDetail(BaseModel):
    """Error detail shape for mapped workflow API errors."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
