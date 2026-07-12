"""Tests for workflow event stream schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.enums import WorkflowEventStatus
from app.streaming import (
    WORKFLOW_EVENT_MESSAGE_TYPE,
    WorkflowEventStreamMessage,
    workflow_event_to_stream_message,
)
from app.streaming.schemas import MAX_LIST_ITEMS, MAX_PAYLOAD_ITEMS, MAX_STRING_LENGTH
from app.workflows.schemas import WorkflowEventRead


def test_workflow_event_stream_message_validates_and_serializes_json() -> None:
    workflow_id = uuid4()
    event_id = uuid4()
    created_at = datetime.now(UTC)

    message = WorkflowEventStreamMessage(
        workflow_id=workflow_id,
        event_id=event_id,
        event_type="workflow.node.started",
        status=WorkflowEventStatus.STARTED,
        stage="planner",
        message="Runtime stage planner started.",
        created_at=created_at,
        sequence=1,
        payload={"stage": "planner", "workflow_status": "PLANNING"},
    )

    serialized = message.model_dump(mode="json", by_alias=True)

    assert serialized["type"] == WORKFLOW_EVENT_MESSAGE_TYPE
    assert serialized["workflow_id"] == str(workflow_id)
    assert serialized["event_id"] == str(event_id)
    assert serialized["status"] == WorkflowEventStatus.STARTED.value
    assert serialized["payload"] == {
        "stage": "planner",
        "workflow_status": "PLANNING",
    }


def test_workflow_event_stream_message_rejects_unknown_message_type() -> None:
    with pytest.raises(ValidationError):
        WorkflowEventStreamMessage(
            message_type="workflow.unknown",
            workflow_id=uuid4(),
            event_id=uuid4(),
            event_type="workflow.node.started",
            created_at=datetime.now(UTC),
        )


def test_workflow_event_stream_message_rejects_invalid_workflow_id() -> None:
    with pytest.raises(ValidationError):
        WorkflowEventStreamMessage.model_validate(
            {
                "workflow_id": "not-a-uuid",
                "event_id": uuid4(),
                "event_type": "workflow.node.started",
                "created_at": datetime.now(UTC),
            },
        )


def test_payload_sanitization_removes_sensitive_keys_and_bounds_values() -> None:
    long_text = "x" * (MAX_STRING_LENGTH + 25)
    message = WorkflowEventStreamMessage(
        workflow_id=uuid4(),
        event_id=uuid4(),
        event_type="workflow.node.completed",
        created_at=datetime.now(UTC),
        payload={
            "stage": "planner",
            "api_key": "secret-value",
            "nested": {"access_token": "secret-token", "safe": "value"},
            "long_text": long_text,
            "values": list(range(MAX_LIST_ITEMS + 5)),
            "object_value": object(),
        },
    )

    assert "api_key" not in message.payload
    assert "access_token" not in message.payload["nested"]
    assert message.payload["nested"] == {"safe": "value"}
    assert message.payload["long_text"] == long_text[:MAX_STRING_LENGTH]
    assert len(message.payload["values"]) == MAX_LIST_ITEMS
    assert isinstance(message.payload["object_value"], str)


def test_payload_sanitization_bounds_number_of_keys() -> None:
    payload = {f"key_{index}": index for index in range(MAX_PAYLOAD_ITEMS + 10)}

    message = WorkflowEventStreamMessage(
        workflow_id=uuid4(),
        event_id=uuid4(),
        event_type="workflow.node.completed",
        created_at=datetime.now(UTC),
        payload=payload,
    )

    assert len(message.payload) == MAX_PAYLOAD_ITEMS


def test_workflow_event_read_converts_to_stream_message() -> None:
    workflow_id = uuid4()
    event_id = uuid4()
    created_at = datetime.now(UTC)
    emitted_at = datetime.now(UTC)
    event = WorkflowEventRead(
        workflow_id=workflow_id,
        event_id=event_id,
        event_type="workflow.node.completed",
        actor_type="user",
        actor_id=uuid4(),
        agent_name="planner",
        status=WorkflowEventStatus.COMPLETED,
        message="Runtime stage planner completed.",
        payload={
            "stage": "planner",
            "workflow_status": "PLANNING",
            "password": "redacted",
        },
        created_at=created_at,
    )

    message = workflow_event_to_stream_message(
        event,
        sequence=3,
        emitted_at=emitted_at,
    )

    assert message.workflow_id == workflow_id
    assert message.event_id == event_id
    assert message.event_type == event.event_type
    assert message.status is WorkflowEventStatus.COMPLETED
    assert message.stage == "planner"
    assert message.sequence == 3
    assert message.emitted_at == emitted_at
    assert message.payload == {
        "stage": "planner",
        "workflow_status": "PLANNING",
    }


def test_workflow_event_read_conversion_uses_agent_name_as_stage_fallback() -> None:
    event = WorkflowEventRead(
        workflow_id=uuid4(),
        event_id=uuid4(),
        event_type="workflow.runtime.started",
        agent_name="planner",
        payload={},
        created_at=datetime.now(UTC),
    )

    message = workflow_event_to_stream_message(event)

    assert message.stage == "planner"
