"""Tests for workflow event stream publish integration."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.models import WorkflowEvent
from app.models.enums import WorkflowEventStatus, WorkflowStatus
from app.runtime import PRE_APPROVAL_RUNTIME_STAGES, RuntimeService
from app.streaming import WorkflowEventStreamMessage
from app.workflows import (
    WorkflowEventCreate,
    WorkflowEventService,
    WorkflowService,
    WorkflowStateCreate,
)


class CapturingPublisher:
    """Workflow event publisher test double."""

    def __init__(
        self,
        *,
        session: AsyncSession | None = None,
        fail: bool = False,
    ) -> None:
        self.session = session
        self.fail = fail
        self.messages: list[WorkflowEventStreamMessage] = []
        self.persisted_before_publish: list[bool] = []

    async def publish_workflow_event(
        self,
        message: WorkflowEventStreamMessage,
    ) -> None:
        if self.session is not None:
            persisted_event = await self.session.get(WorkflowEvent, message.event_id)
            self.persisted_before_publish.append(persisted_event is not None)
        if self.fail:
            raise RuntimeError("publish unavailable")
        self.messages.append(message)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for publish integration tests."""
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            transaction = await session.begin()
            try:
                yield session
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()


def build_workflow_state_create() -> WorkflowStateCreate:
    """Create typed workflow input for publish integration tests."""
    return WorkflowStateCreate.model_validate(
        {
            "workflow_type": "procurement_quotation",
            "domain": "it_equipment",
            "request": {
                "raw_text": "Need 50 business laptops.",
                "source": "manual_text",
            },
        },
    )


async def create_workflow(db_session: AsyncSession) -> UUID:
    """Create a workflow and return its id."""
    workflow_service = WorkflowService(db_session)
    state = await workflow_service.create_workflow(build_workflow_state_create())
    return UUID(state.workflow_id)


@pytest.mark.asyncio
async def test_append_event_publishes_after_event_is_persisted(
    db_session: AsyncSession,
) -> None:
    workflow_id = await create_workflow(db_session)
    publisher = CapturingPublisher(session=db_session)
    service = WorkflowEventService(db_session, publisher=publisher)

    event = await service.append_event(
        WorkflowEventCreate(
            workflow_id=workflow_id,
            event_type="workflow.node.completed",
            agent_name="planner",
            status=WorkflowEventStatus.COMPLETED,
            message="Planner completed.",
            payload={"stage": "planner", "workflow_status": "PLANNING"},
        ),
    )

    assert len(publisher.messages) == 1
    assert publisher.persisted_before_publish == [True]
    assert publisher.messages[0].event_id == event.event_id
    assert publisher.messages[0].workflow_id == workflow_id
    assert publisher.messages[0].event_type == "workflow.node.completed"
    assert publisher.messages[0].stage == "planner"


@pytest.mark.asyncio
async def test_append_event_works_unchanged_without_publisher(
    db_session: AsyncSession,
) -> None:
    workflow_id = await create_workflow(db_session)
    service = WorkflowEventService(db_session)

    event = await service.append_event(
        WorkflowEventCreate(
            workflow_id=workflow_id,
            event_type="workflow.runtime.started",
        ),
    )
    persisted_event = await db_session.get(WorkflowEvent, event.event_id)

    assert persisted_event is not None
    assert persisted_event.event_type == "workflow.runtime.started"


@pytest.mark.asyncio
async def test_append_event_publish_failure_preserves_persisted_event(
    db_session: AsyncSession,
) -> None:
    workflow_id = await create_workflow(db_session)
    publisher = CapturingPublisher(session=db_session, fail=True)
    service = WorkflowEventService(db_session, publisher=publisher)

    event = await service.append_event(
        WorkflowEventCreate(
            workflow_id=workflow_id,
            event_type="workflow.runtime.started",
            payload={"stage": "planner"},
        ),
    )
    persisted_event = await db_session.get(WorkflowEvent, event.event_id)

    assert publisher.persisted_before_publish == [True]
    assert publisher.messages == []
    assert persisted_event is not None
    assert persisted_event.event_type == "workflow.runtime.started"
    assert persisted_event.payload == {"stage": "planner"}


@pytest.mark.asyncio
async def test_append_event_publishes_sanitized_stream_message(
    db_session: AsyncSession,
) -> None:
    workflow_id = await create_workflow(db_session)
    publisher = CapturingPublisher()
    service = WorkflowEventService(db_session, publisher=publisher)

    await service.append_event(
        WorkflowEventCreate(
            workflow_id=workflow_id,
            event_type="workflow.node.completed",
            agent_name="planner",
            status=WorkflowEventStatus.COMPLETED,
            payload={
                "stage": "planner",
                "password": "do-not-stream",
                "nested": {"api_key": "secret", "safe": "value"},
                "raw_request": "x" * 800,
            },
        ),
    )

    [message] = publisher.messages
    assert "password" not in message.payload
    assert message.payload["nested"] == {"safe": "value"}
    assert len(message.payload["raw_request"]) == 500
    assert message.model_dump(mode="json", by_alias=True)["type"] == "workflow.event"


@pytest.mark.asyncio
async def test_runtime_service_events_publish_through_workflow_event_service(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    created_state = await workflow_service.create_workflow(
        build_workflow_state_create()
    )
    workflow_id = UUID(created_state.workflow_id)
    publisher = CapturingPublisher()
    event_service = WorkflowEventService(db_session, publisher=publisher)
    runtime_service = RuntimeService(workflow_service, event_service)

    result = await runtime_service.run_workflow(workflow_id)
    event_types = [message.event_type for message in publisher.messages]

    assert result.state.status is WorkflowStatus.WAITING_APPROVAL
    assert event_types[0] == "workflow.runtime.started"
    assert event_types[-1] == "workflow.runtime.waiting_for_approval"
    assert event_types.count("workflow.node.started") == len(
        PRE_APPROVAL_RUNTIME_STAGES,
    )
    assert event_types.count("workflow.node.completed") == len(
        PRE_APPROVAL_RUNTIME_STAGES,
    )
    assert {
        message.stage for message in publisher.messages if message.stage is not None
    } == {stage.value for stage in PRE_APPROVAL_RUNTIME_STAGES}


@pytest.mark.asyncio
async def test_append_event_does_not_commit(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_id = await create_workflow(db_session)
    service = WorkflowEventService(db_session, publisher=CapturingPublisher())

    async def fail_commit() -> None:
        raise AssertionError("WorkflowEventService attempted to commit")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    event = await service.append_event(
        WorkflowEventCreate(
            workflow_id=workflow_id,
            event_type="workflow.runtime.started",
        ),
    )

    assert event.workflow_id == workflow_id
