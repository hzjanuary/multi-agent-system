"""Workflow API request and response schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import WorkflowStatus
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


class WorkflowApiErrorDetail(BaseModel):
    """Error detail shape for mapped workflow API errors."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
