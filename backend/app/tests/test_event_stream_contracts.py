"""Tests for event streaming publisher contracts."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.models.enums import WorkflowEventStatus
from app.streaming import (
    WorkflowEventPublisher,
    WorkflowEventStreamMessage,
    WorkflowEventSubscriber,
    workflow_events_channel,
)


class InMemoryPublisher:
    """Small contract test double for publisher protocol compatibility."""

    def __init__(self) -> None:
        self.messages: list[WorkflowEventStreamMessage] = []

    async def publish_workflow_event(
        self,
        message: WorkflowEventStreamMessage,
    ) -> None:
        self.messages.append(message)


class InMemorySubscriber:
    """Small contract test double for subscriber protocol compatibility."""

    def __init__(self, messages: list[WorkflowEventStreamMessage]) -> None:
        self.messages = messages

    async def subscribe_workflow_events(
        self,
        workflow_id: UUID | str,
    ) -> AsyncIterator[WorkflowEventStreamMessage]:
        for message in self.messages:
            if message.workflow_id == UUID(str(workflow_id)):
                yield message


def _message(workflow_id: UUID) -> WorkflowEventStreamMessage:
    return WorkflowEventStreamMessage(
        workflow_id=workflow_id,
        event_id=uuid4(),
        event_type="workflow.node.completed",
        status=WorkflowEventStatus.COMPLETED,
        stage="planner",
        created_at=datetime.now(UTC),
        payload={"stage": "planner"},
    )


@pytest.mark.asyncio
async def test_publisher_protocol_import_and_usage() -> None:
    publisher: WorkflowEventPublisher = InMemoryPublisher()
    message = _message(uuid4())

    await publisher.publish_workflow_event(message)

    assert isinstance(publisher, InMemoryPublisher)
    assert publisher.messages == [message]


@pytest.mark.asyncio
async def test_subscriber_protocol_import_and_usage() -> None:
    workflow_id = uuid4()
    other_workflow_id = uuid4()
    messages = [_message(workflow_id), _message(other_workflow_id)]
    subscriber: WorkflowEventSubscriber = InMemorySubscriber(messages)

    received = [
        message async for message in subscriber.subscribe_workflow_events(workflow_id)
    ]

    assert received == [messages[0]]


def test_workflow_events_channel_is_deterministic_and_workflow_scoped() -> None:
    workflow_id = uuid4()

    assert workflow_events_channel(workflow_id) == f"workflow-events:{workflow_id}"
    assert workflow_events_channel(str(workflow_id)) == f"workflow-events:{workflow_id}"


def test_workflow_events_channel_rejects_unsafe_identifier() -> None:
    with pytest.raises(ValueError):
        workflow_events_channel("../not-a-uuid")
