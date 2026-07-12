"""Workflow event append/read service."""

from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowEvent
from app.repositories.workflow_events import WorkflowEventRepository
from app.repositories.workflows import WorkflowRepository
from app.streaming.contracts import WorkflowEventPublisher
from app.streaming.schemas import workflow_event_to_stream_message
from app.workflows.audit import WorkflowAuditLogger
from app.workflows.exceptions import WorkflowEventNotFoundError, WorkflowNotFoundError
from app.workflows.schemas import WorkflowEventCreate, WorkflowEventRead

logger = structlog.get_logger(__name__)


class WorkflowEventService:
    """Workflow event use cases backed by workflow event repositories."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        publisher: WorkflowEventPublisher | None = None,
    ) -> None:
        self.workflow_repository = WorkflowRepository(session)
        self.workflow_event_repository = WorkflowEventRepository(session)
        self.workflow_audit_logger = WorkflowAuditLogger(session)
        self.publisher = publisher

    async def append_event(self, event: WorkflowEventCreate) -> WorkflowEventRead:
        """Append an event for an existing workflow."""
        workflow = await self.workflow_repository.get_by_id(event.workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(f"Workflow {event.workflow_id} was not found")

        event_data = event.model_dump(mode="json")
        persisted_event = self.workflow_event_repository.create_event(
            workflow_id=event.workflow_id,
            event_type=event.event_type,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            agent_name=event.agent_name,
            status=event.status,
            message=event.message,
            payload=dict(event_data["payload"]),
        )
        await self.workflow_event_repository.session.flush()
        self.workflow_audit_logger.audit_workflow_event_appended(
            workflow_id=persisted_event.workflow_id,
            event_id=persisted_event.id,
            event_type=persisted_event.event_type,
            actor_type=persisted_event.actor_type,
            actor_id=persisted_event.actor_id,
            agent_name=persisted_event.agent_name,
        )
        await self.workflow_event_repository.session.flush()
        event_read = self._event_to_read(persisted_event)
        await self._publish_event(event_read)
        return event_read

    async def list_events_for_workflow(
        self,
        workflow_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WorkflowEventRead]:
        """Return events for one workflow in deterministic creation order."""
        workflow = await self.workflow_repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} was not found")

        events = await self.workflow_event_repository.list_by_workflow_id(
            workflow_id,
            limit=limit,
            offset=offset,
        )
        return [self._event_to_read(event) for event in events]

    async def get_event(self, event_id: UUID) -> WorkflowEventRead | None:
        """Return one workflow event by id, or None when not found."""
        event = await self.workflow_event_repository.get_by_id(event_id)
        if event is None:
            return None
        return self._event_to_read(event)

    async def get_required_event(self, event_id: UUID) -> WorkflowEventRead:
        """Return one workflow event by id, raising when missing."""
        event = await self.get_event(event_id)
        if event is None:
            raise WorkflowEventNotFoundError(f"Workflow event {event_id} was not found")
        return event

    def _event_to_read(self, event: WorkflowEvent) -> WorkflowEventRead:
        payload: dict[str, Any] = {
            "event_id": event.id,
            "workflow_id": event.workflow_id,
            "event_type": event.event_type,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "agent_name": event.agent_name,
            "status": event.status,
            "message": event.message,
            "payload": dict(event.payload),
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }
        return WorkflowEventRead.model_validate(payload)

    async def _publish_event(self, event: WorkflowEventRead) -> None:
        """Best-effort publish of a persisted workflow event stream message."""
        if self.publisher is None:
            return

        try:
            message = workflow_event_to_stream_message(event)
            await self.publisher.publish_workflow_event(message)
        except Exception as error:
            logger.warning(
                "workflow_event_publish_failed",
                workflow_id=str(event.workflow_id),
                event_id=str(event.event_id),
                event_type=event.event_type,
                error_type=type(error).__name__,
            )
