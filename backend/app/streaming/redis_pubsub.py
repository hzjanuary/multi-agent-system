"""Redis-backed workflow event pub/sub adapter."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Protocol
from uuid import UUID

from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings
from app.streaming.contracts import workflow_events_channel
from app.streaming.schemas import WorkflowEventStreamMessage


class RedisEventStreamError(RuntimeError):
    """Base error for Redis event stream adapter failures."""


class RedisEventStreamPublishError(RedisEventStreamError):
    """Raised when publishing a workflow stream message fails."""


class RedisEventStreamSubscribeError(RedisEventStreamError):
    """Raised when subscribing to workflow stream messages fails."""


class RedisPublishClient(Protocol):
    """Minimal Redis publish client surface used by the publisher."""

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a Redis channel."""

    async def aclose(self) -> None:
        """Close the Redis client."""


class RedisPubSubConnection(Protocol):
    """Minimal Redis pub/sub connection surface used by the subscriber."""

    async def subscribe(self, *channels: str) -> None:
        """Subscribe to Redis channels."""

    async def unsubscribe(self, *channels: str) -> None:
        """Unsubscribe from Redis channels."""

    async def get_message(
        self,
        ignore_subscribe_messages: bool = True,
        timeout: float | None = None,
    ) -> Any:
        """Return the next Redis pub/sub message, if available."""

    async def aclose(self) -> None:
        """Close the pub/sub connection."""


class RedisSubscriberClient(Protocol):
    """Minimal Redis client surface used to create pub/sub connections."""

    def pubsub(self) -> RedisPubSubConnection:
        """Create a Redis pub/sub connection."""

    async def aclose(self) -> None:
        """Close the Redis client."""


class RedisWorkflowEventPublisher:
    """Workflow event publisher backed by Redis pub/sub."""

    def __init__(self, redis_client: RedisPublishClient) -> None:
        self._redis_client = redis_client

    @classmethod
    def from_url(cls, redis_url: str) -> RedisWorkflowEventPublisher:
        """Create a publisher from a Redis URL."""
        return cls(Redis.from_url(redis_url, decode_responses=True))

    async def publish_workflow_event(
        self,
        message: WorkflowEventStreamMessage,
    ) -> None:
        """Publish one typed workflow event message to its workflow channel."""
        channel = workflow_events_channel(message.workflow_id)
        serialized_message = message.model_dump_json(by_alias=True)

        try:
            await self._redis_client.publish(channel, serialized_message)
        except RedisError as error:
            raise RedisEventStreamPublishError(
                "Redis workflow event publish failed",
            ) from error

    async def close(self) -> None:
        """Close the underlying Redis client."""
        try:
            await self._redis_client.aclose()
        except RedisError as error:
            raise RedisEventStreamPublishError(
                "Redis workflow event publisher close failed",
            ) from error


class RedisWorkflowEventSubscriber:
    """Workflow event subscriber backed by Redis pub/sub."""

    def __init__(
        self,
        redis_client: RedisSubscriberClient,
        *,
        poll_timeout_seconds: float = 1.0,
    ) -> None:
        self._redis_client = redis_client
        self._poll_timeout_seconds = poll_timeout_seconds

    @classmethod
    def from_url(cls, redis_url: str) -> RedisWorkflowEventSubscriber:
        """Create a subscriber from a Redis URL."""
        return cls(Redis.from_url(redis_url, decode_responses=True))

    async def subscribe_workflow_events(
        self,
        workflow_id: UUID | str,
    ) -> AsyncGenerator[WorkflowEventStreamMessage, None]:
        """Yield typed stream messages from one workflow-scoped Redis channel."""
        channel = workflow_events_channel(workflow_id)
        pubsub = self._redis_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            while True:
                raw_message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=self._poll_timeout_seconds,
                )
                message = _decode_stream_message(raw_message)
                if message is not None:
                    yield message
        except RedisError as error:
            raise RedisEventStreamSubscribeError(
                "Redis workflow event subscription failed",
            ) from error
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
            except RedisError as error:
                raise RedisEventStreamSubscribeError(
                    "Redis workflow event subscription cleanup failed",
                ) from error

    async def close(self) -> None:
        """Close the underlying Redis client."""
        try:
            await self._redis_client.aclose()
        except RedisError as error:
            raise RedisEventStreamSubscribeError(
                "Redis workflow event subscriber close failed",
            ) from error


def create_redis_workflow_event_publisher(
    redis_url: str | None = None,
) -> RedisWorkflowEventPublisher:
    """Create a Redis workflow event publisher from settings or an explicit URL."""
    settings = get_settings()
    return RedisWorkflowEventPublisher.from_url(redis_url or str(settings.redis_url))


def create_redis_workflow_event_subscriber(
    redis_url: str | None = None,
) -> RedisWorkflowEventSubscriber:
    """Create a Redis workflow event subscriber from settings or an explicit URL."""
    settings = get_settings()
    return RedisWorkflowEventSubscriber.from_url(redis_url or str(settings.redis_url))


def _decode_stream_message(raw_message: Any) -> WorkflowEventStreamMessage | None:
    """Decode one Redis pub/sub payload into a stream message when valid."""
    if raw_message is None:
        return None

    message_payload = raw_message
    if isinstance(raw_message, dict):
        message_type = raw_message.get("type")
        if message_type not in {"message", "pmessage", b"message", b"pmessage"}:
            return None
        message_payload = raw_message.get("data")

    try:
        if isinstance(message_payload, bytes | bytearray | str):
            return WorkflowEventStreamMessage.model_validate_json(message_payload)
        if isinstance(message_payload, dict):
            return WorkflowEventStreamMessage.model_validate(message_payload)
    except (TypeError, UnicodeDecodeError, ValidationError, ValueError):
        return None

    return None
