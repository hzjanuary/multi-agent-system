"""Pydantic contracts for human approval decisions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import WorkflowStatus

MAX_APPROVAL_METADATA_KEYS = 20
MAX_APPROVAL_METADATA_DEPTH = 4
MAX_APPROVAL_METADATA_LIST_ITEMS = 20
MAX_APPROVAL_METADATA_STRING_LENGTH = 500


class ApprovalDecisionType(StrEnum):
    """Supported human approval decision values."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ApprovalDecisionRequest(BaseModel):
    """Request contract for a future approval decision API."""

    model_config = ConfigDict(frozen=True)

    decision: ApprovalDecisionType
    comment: str | None = Field(default=None, min_length=1, max_length=2000)
    request_id: str | None = Field(default=None, min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata is bounded and JSON-compatible."""
        return _validate_json_object(value, field_name="metadata")

    @model_validator(mode="after")
    def require_rejection_comment(self) -> ApprovalDecisionRequest:
        """Require an explanatory comment for rejections."""
        if self.decision is ApprovalDecisionType.REJECT and not self.comment:
            raise ValueError("reject decisions require a comment")
        return self


class ApprovalRecord(BaseModel):
    """Safe approval history record for workflow state or API readback."""

    model_config = ConfigDict(frozen=True)

    decision_id: UUID
    workflow_id: UUID
    decision: ApprovalDecisionType
    actor_id: UUID
    actor_email: str | None = Field(default=None, min_length=1, max_length=320)
    actor_roles: tuple[str, ...] = Field(default_factory=tuple)
    comment: str | None = Field(default=None, min_length=1, max_length=2000)
    decided_at: datetime
    previous_status: WorkflowStatus
    next_status: WorkflowStatus | None = None
    request_id: str | None = Field(default=None, min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("actor_roles")
    @classmethod
    def validate_actor_roles(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject blank role names and bound the role list."""
        if len(value) > 10:
            raise ValueError("actor_roles cannot contain more than 10 roles")
        for role in value:
            if not role or len(role) > 100:
                raise ValueError("actor_roles must contain bounded role names")
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata is bounded and JSON-compatible."""
        return _validate_json_object(value, field_name="metadata")


class ApprovalDecisionResponse(BaseModel):
    """Response contract for a future approval decision endpoint."""

    model_config = ConfigDict(frozen=True)

    workflow_id: UUID
    approval: ApprovalRecord
    previous_status: WorkflowStatus
    next_status: WorkflowStatus
    can_resume: bool = False
    resume_recommended: bool = False


class ApprovalHistoryResponse(BaseModel):
    """Read contract for workflow approval decision history."""

    model_config = ConfigDict(frozen=True)

    workflow_id: UUID
    approvals: tuple[ApprovalRecord, ...] = Field(default_factory=tuple)
    has_final_decision: bool = False
    can_resume: bool = False


class WorkflowResumeRequest(BaseModel):
    """Request contract for a future bounded workflow resume endpoint."""

    model_config = ConfigDict(frozen=True)

    request_id: str | None = Field(default=None, min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata is bounded and JSON-compatible."""
        return _validate_json_object(value, field_name="metadata")


class WorkflowResumeResponse(BaseModel):
    """Response contract for future post-approval resume behavior."""

    model_config = ConfigDict(frozen=True)

    workflow_id: UUID
    previous_status: WorkflowStatus
    next_status: WorkflowStatus
    resumed: bool = False
    message: str | None = Field(default=None, min_length=1, max_length=500)
    request_id: str | None = Field(default=None, min_length=1, max_length=100)


def _validate_json_object(value: dict[str, Any], *, field_name: str) -> dict[str, Any]:
    if len(value) > MAX_APPROVAL_METADATA_KEYS:
        raise ValueError(f"{field_name} cannot contain more than 20 keys")
    _validate_json_value(value, field_name=field_name, depth=0)
    return value


def _validate_json_value(value: Any, *, field_name: str, depth: int) -> None:
    if depth > MAX_APPROVAL_METADATA_DEPTH:
        raise ValueError(f"{field_name} nesting is too deep")
    if isinstance(value, str):
        if len(value) > MAX_APPROVAL_METADATA_STRING_LENGTH:
            raise ValueError(f"{field_name} string values are too long")
        return
    if isinstance(value, bool | int | float) or value is None:
        return
    if isinstance(value, list):
        if len(value) > MAX_APPROVAL_METADATA_LIST_ITEMS:
            raise ValueError(f"{field_name} lists are too long")
        for item in value:
            _validate_json_value(item, field_name=field_name, depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_APPROVAL_METADATA_KEYS:
            raise ValueError(f"{field_name} objects contain too many keys")
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 100:
                raise ValueError(f"{field_name} keys must be bounded strings")
            _validate_json_value(item, field_name=field_name, depth=depth + 1)
        return
    raise ValueError(f"{field_name} must be JSON-compatible")
