"""Tests for Redis-backed workflow event stream pub/sub adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from redis.exceptions import RedisError

from app.models.enums import WorkflowEventStatus
from app.streaming import (
    RedisEventStreamPublishError,
    RedisWorkflowEventPublisher,
    RedisWorkflowEventSubscriber,
    WorkflowEventPublisher,
    WorkflowEventStreamMessage,
    WorkflowEventSubscriber,
    workflow_events_channel,
)


class FakeRedisPublisher:
    """Fake Redis publish client for unit tests."""

    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self.closed = False

    async def publish(self, channel: str, message: str) -> int:
        self.published.append((channel, message))
        return 1

    async def aclose(self) -> None:
        self.closed = True


class FailingRedisPublisher(FakeRedisPublisher):
    """Fake Redis publisher that raises Redis errors."""

    async def publish(self, channel: str, message: str) -> int:
        raise RedisError("publish failed")


class FakeRedisClient:
    """Fake Redis client that provides pub/sub connections."""

    def __init__(self, messages: list[Any]) -> None:
        self.pubsub_connection = FakePubSub(messages)
        self.closed = False

    def pubsub(self) -> FakePubSub:
        return self.pubsub_connection

    async def aclose(self) -> None:
        self.closed = True


class FakePubSub:
    """Fake Redis pub/sub connection for subscriber unit tests."""

    def __init__(self, messages: list[Any]) -> None:
        self._messages = messages
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []
        self.closed = False

    async def subscribe(self, *channels: str) -> None:
        self.subscribed.extend(channels)

    async def unsubscribe(self, *channels: str) -> None:
        self.unsubscribed.extend(channels)

    async def get_message(
        self,
        ignore_subscribe_messages: bool = True,
        timeout: float | None = None,
    ) -> Any:
        if self._messages:
            return self._messages.pop(0)
        return None

    async def aclose(self) -> None:
        self.closed = True


def _message(workflow_id: UUID) -> WorkflowEventStreamMessage:
    return WorkflowEventStreamMessage(
        workflow_id=workflow_id,
        event_id=uuid4(),
        event_type="workflow.node.completed",
        status=WorkflowEventStatus.COMPLETED,
        stage="planner",
        message="Runtime stage planner completed.",
        created_at=datetime.now(UTC),
        sequence=1,
        payload={"stage": "planner", "workflow_status": "PLANNING"},
    )


@pytest.mark.asyncio
async def test_redis_publisher_conforms_to_workflow_event_publisher() -> None:
    publisher: WorkflowEventPublisher = RedisWorkflowEventPublisher(
        FakeRedisPublisher(),
    )

    await publisher.publish_workflow_event(_message(uuid4()))


@pytest.mark.asyncio
async def test_redis_publisher_publishes_json_to_workflow_channel() -> None:
    workflow_id = uuid4()
    message = _message(workflow_id)
    redis_client = FakeRedisPublisher()
    publisher = RedisWorkflowEventPublisher(redis_client)

    await publisher.publish_workflow_event(message)

    assert len(redis_client.published) == 1
    channel, serialized = redis_client.published[0]
    assert channel == workflow_events_channel(workflow_id)

    decoded = WorkflowEventStreamMessage.model_validate_json(serialized)
    assert decoded.workflow_id == workflow_id
    assert decoded.event_id == message.event_id
    assert decoded.event_type == message.event_type
    assert decoded.payload == message.payload


@pytest.mark.asyncio
async def test_redis_publisher_wraps_redis_publish_errors() -> None:
    publisher = RedisWorkflowEventPublisher(FailingRedisPublisher())

    with pytest.raises(RedisEventStreamPublishError):
        await publisher.publish_workflow_event(_message(uuid4()))


@pytest.mark.asyncio
async def test_redis_publisher_close_closes_redis_client() -> None:
    redis_client = FakeRedisPublisher()
    publisher = RedisWorkflowEventPublisher(redis_client)

    await publisher.close()

    assert redis_client.closed is True


@pytest.mark.asyncio
async def test_redis_subscriber_conforms_to_workflow_event_subscriber() -> None:
    subscriber: WorkflowEventSubscriber = RedisWorkflowEventSubscriber(
        FakeRedisClient([]),
    )

    assert isinstance(subscriber, RedisWorkflowEventSubscriber)


@pytest.mark.asyncio
async def test_redis_subscriber_yields_valid_stream_messages() -> None:
    workflow_id = uuid4()
    message = _message(workflow_id)
    redis_client = FakeRedisClient(
        [
            {
                "type": "message",
                "data": message.model_dump_json(by_alias=True).encode(),
            },
        ],
    )
    subscriber = RedisWorkflowEventSubscriber(redis_client, poll_timeout_seconds=0.01)

    iterator = subscriber.subscribe_workflow_events(workflow_id)
    received = await anext(iterator)
    await iterator.aclose()

    assert received.workflow_id == workflow_id
    assert received.event_id == message.event_id
    assert redis_client.pubsub_connection.subscribed == [
        workflow_events_channel(workflow_id),
    ]
    assert redis_client.pubsub_connection.unsubscribed == [
        workflow_events_channel(workflow_id),
    ]
    assert redis_client.pubsub_connection.closed is True


@pytest.mark.asyncio
async def test_redis_subscriber_ignores_malformed_messages() -> None:
    workflow_id = uuid4()
    message = _message(workflow_id)
    redis_client = FakeRedisClient(
        [
            {"type": "subscribe", "data": 1},
            {"type": "message", "data": "not-json"},
            {"type": "message", "data": message.model_dump_json(by_alias=True)},
        ],
    )
    subscriber = RedisWorkflowEventSubscriber(redis_client, poll_timeout_seconds=0.01)

    iterator = subscriber.subscribe_workflow_events(workflow_id)
    received = await anext(iterator)
    await iterator.aclose()

    assert received.event_id == message.event_id


@pytest.mark.asyncio
async def test_redis_subscriber_rejects_invalid_workflow_channel_id() -> None:
    subscriber = RedisWorkflowEventSubscriber(FakeRedisClient([]))

    with pytest.raises(ValueError):
        await anext(subscriber.subscribe_workflow_events("../bad-id"))


@pytest.mark.asyncio
async def test_redis_subscriber_close_closes_redis_client() -> None:
    redis_client = FakeRedisClient([])
    subscriber = RedisWorkflowEventSubscriber(redis_client)

    await subscriber.close()

    assert redis_client.closed is True
