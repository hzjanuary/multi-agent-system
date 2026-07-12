"""Application dependency helpers."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db_session
from app.runtime.service import RuntimeService
from app.streaming import (
    RedisWorkflowEventPublisher,
    RedisWorkflowEventSubscriber,
    WorkflowEventPublisher,
    WorkflowEventSubscriber,
    create_redis_workflow_event_publisher,
    create_redis_workflow_event_subscriber,
)
from app.workflows.events import WorkflowEventService
from app.workflows.service import WorkflowService


def provide_settings() -> Settings:
    """Provide typed application settings for dependency injection."""
    return get_settings()


async def provide_db_session() -> AsyncIterator[AsyncSession]:
    """Provide a request-scoped async database session."""
    async for session in get_db_session():
        yield session


DbSessionDependency = Annotated[AsyncSession, Depends(provide_db_session)]


def provide_workflow_service(session: DbSessionDependency) -> WorkflowService:
    """Provide workflow state service bound to the request session."""
    return WorkflowService(session)


async def provide_workflow_event_publisher(
    settings: Annotated[Settings, Depends(provide_settings)],
) -> AsyncIterator[WorkflowEventPublisher]:
    """Provide a request-scoped workflow event publisher."""
    publisher = create_redis_workflow_event_publisher(settings.redis_url)
    try:
        yield publisher
    finally:
        if isinstance(publisher, RedisWorkflowEventPublisher):
            await publisher.close()


async def provide_workflow_event_subscriber(
    settings: Annotated[Settings, Depends(provide_settings)],
) -> AsyncIterator[WorkflowEventSubscriber]:
    """Provide a request-scoped workflow event subscriber."""
    subscriber = create_redis_workflow_event_subscriber(settings.redis_url)
    try:
        yield subscriber
    finally:
        if isinstance(subscriber, RedisWorkflowEventSubscriber):
            await subscriber.close()


def provide_workflow_event_service(
    session: DbSessionDependency,
    publisher: Annotated[
        WorkflowEventPublisher | None,
        Depends(provide_workflow_event_publisher),
    ] = None,
) -> WorkflowEventService:
    """Provide workflow event service bound to the request session."""
    return WorkflowEventService(session, publisher=publisher)


def provide_runtime_service(
    workflow_service: Annotated[WorkflowService, Depends(provide_workflow_service)],
    workflow_event_service: Annotated[
        WorkflowEventService,
        Depends(provide_workflow_event_service),
    ],
) -> RuntimeService:
    """Provide runtime orchestration service bound to workflow services."""
    return RuntimeService(workflow_service, workflow_event_service)
