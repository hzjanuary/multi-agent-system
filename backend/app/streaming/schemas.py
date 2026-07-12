"""Pydantic schemas for workflow event stream messages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import WorkflowEventStatus
from app.workflows.schemas import WorkflowEventRead

WORKFLOW_EVENT_MESSAGE_TYPE = "workflow.event"
MAX_MESSAGE_LENGTH = 500
MAX_PAYLOAD_DEPTH = 4
MAX_PAYLOAD_ITEMS = 50
MAX_LIST_ITEMS = 20
MAX_STRING_LENGTH = 500
SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
)


class WorkflowEventStreamMessage(BaseModel):
    """Safe direct message sent over workflow event streams."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    message_type: str = Field(
        default=WORKFLOW_EVENT_MESSAGE_TYPE,
        serialization_alias="type",
        min_length=1,
        max_length=100,
    )
    workflow_id: UUID
    event_id: UUID
    event_type: str = Field(min_length=1, max_length=100)
    status: WorkflowEventStatus | None = None
    stage: str | None = Field(default=None, min_length=1, max_length=100)
    message: str | None = Field(default=None, min_length=1, max_length=500)
    created_at: datetime
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sequence: int | None = Field(default=None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, value: str) -> str:
        """Reject unknown stream message types in this schema."""
        if value != WORKFLOW_EVENT_MESSAGE_TYPE:
            raise ValueError("Unsupported workflow event stream message type")
        return value

    @field_validator("payload")
    @classmethod
    def sanitize_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Keep stream payloads bounded and safe for client delivery."""
        return sanitize_stream_payload(value)


def workflow_event_to_stream_message(
    event: WorkflowEventRead,
    *,
    sequence: int | None = None,
    emitted_at: datetime | None = None,
) -> WorkflowEventStreamMessage:
    """Convert a persisted workflow event read schema into a stream message."""
    stage = _stage_from_event(event)
    return WorkflowEventStreamMessage(
        workflow_id=event.workflow_id,
        event_id=event.event_id,
        event_type=event.event_type,
        status=event.status,
        stage=stage,
        message=event.message,
        created_at=event.created_at,
        emitted_at=emitted_at or datetime.now(UTC),
        sequence=sequence,
        payload=event.payload,
    )


def sanitize_stream_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a bounded JSON-compatible payload with sensitive keys removed."""
    return _sanitize_mapping(payload, depth=0)


def _stage_from_event(event: WorkflowEventRead) -> str | None:
    payload_stage = event.payload.get("stage")
    if isinstance(payload_stage, str) and payload_stage:
        return payload_stage[:MAX_STRING_LENGTH]
    return event.agent_name


def _sanitize_mapping(payload: dict[str, Any], *, depth: int) -> dict[str, Any]:
    if depth >= MAX_PAYLOAD_DEPTH:
        return {}

    sanitized: dict[str, Any] = {}
    for index, (key, value) in enumerate(payload.items()):
        if index >= MAX_PAYLOAD_ITEMS:
            break
        normalized_key = str(key)[:MAX_STRING_LENGTH]
        if _is_sensitive_key(normalized_key):
            continue
        sanitized[normalized_key] = _sanitize_value(value, depth=depth + 1)
    return sanitized


def _sanitize_sequence(values: list[Any] | tuple[Any, ...], *, depth: int) -> list[Any]:
    if depth >= MAX_PAYLOAD_DEPTH:
        return []
    return [
        _sanitize_value(item, depth=depth + 1) for item in list(values)[:MAX_LIST_ITEMS]
    ]


def _sanitize_value(value: Any, *, depth: int) -> Any:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return value[:MAX_STRING_LENGTH]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return _sanitize_mapping(value, depth=depth)
    if isinstance(value, list | tuple):
        return _sanitize_sequence(value, depth=depth)
    return str(value)[:MAX_STRING_LENGTH]


def _is_sensitive_key(key: str) -> bool:
    normalized_key = key.lower()
    return any(part in normalized_key for part in SENSITIVE_KEY_PARTS)
