"""Implementation-agnostic event streaming contracts."""

from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from app.streaming.schemas import WorkflowEventStreamMessage

WORKFLOW_EVENTS_CHANNEL_PREFIX = "workflow-events"


class WorkflowEventPublisher(Protocol):
    """Async contract for publishing workflow stream messages."""

    async def publish_workflow_event(
        self,
        message: WorkflowEventStreamMessage,
    ) -> None:
        """Publish one workflow event stream message."""


class WorkflowEventSubscriber(Protocol):
    """Async contract for subscribing to workflow stream messages."""

    def subscribe_workflow_events(
        self,
        workflow_id: UUID | str,
    ) -> AsyncIterator[WorkflowEventStreamMessage]:
        """Subscribe to messages for one workflow."""


def workflow_events_channel(workflow_id: UUID | str) -> str:
    """Return the deterministic pub/sub channel for one workflow."""
    normalized_workflow_id = UUID(str(workflow_id))
    return f"{WORKFLOW_EVENTS_CHANNEL_PREFIX}:{normalized_workflow_id}"
