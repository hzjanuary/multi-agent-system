"""Tests for SPEC-010 demo workflow and event seeding."""

from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.demo import (
    DEMO_WORKFLOW_EVENTS,
    DEMO_WORKFLOWS,
    seed_demo_workflows_and_events,
)
from app.models import User, Workflow, WorkflowEvent
from app.models.enums import WorkflowEventStatus, WorkflowStatus
from app.workflows.events import WorkflowEventService
from app.workflows.schemas import WorkflowState
from app.workflows.service import WorkflowService


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for demo workflow seed tests."""
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


@pytest.mark.asyncio
async def test_seed_demo_workflows_and_events_creates_contract_records(
    db_session: AsyncSession,
) -> None:
    result = await seed_demo_workflows_and_events(db_session)

    workflows = await _demo_workflows(db_session)
    events = await _demo_events(db_session)

    assert result.workflows_created + result.workflows_reused == len(DEMO_WORKFLOWS)
    assert result.events_created + result.events_reused == len(DEMO_WORKFLOW_EVENTS)
    assert {workflow.id for workflow in workflows} == {
        workflow.stable_workflow_id for workflow in DEMO_WORKFLOWS
    }
    assert {event.id for event in events} == {
        event.stable_event_id for event in DEMO_WORKFLOW_EVENTS
    }


@pytest.mark.asyncio
async def test_seeded_workflow_state_and_status_match_contract(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)

    workflows = {
        workflow.id: workflow for workflow in await _demo_workflows(db_session)
    }

    for definition in DEMO_WORKFLOWS:
        workflow = workflows[definition.stable_workflow_id]
        state = WorkflowState.model_validate(workflow.state_payload)
        assert workflow.workflow_type == definition.workflow_type.value
        assert workflow.domain == definition.domain
        assert workflow.status is definition.initial_status
        assert state.status is definition.initial_status
        assert state.workflow_id == str(definition.stable_workflow_id)
        assert state.metadata.attributes["demo_seed_key"] == definition.key
        assert state.metadata.attributes["demo_reference_only"] is True
        request_payload = cast(dict[str, Any], workflow.request_payload)
        demo_payload = cast(dict[str, Any], request_payload["demo"])
        assert demo_payload["seed_key"] == definition.key


@pytest.mark.asyncio
async def test_seeded_workflows_are_readable_through_workflow_service(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)
    service = WorkflowService(db_session)

    seeded = await service.list_workflows(domain="it_equipment", limit=20)
    seeded_by_key = {
        state.metadata.attributes.get("demo_seed_key"): state
        for state in seeded
        if state.metadata.attributes.get("demo_seed") is True
    }

    assert set(seeded_by_key) == {workflow.key for workflow in DEMO_WORKFLOWS}
    assert seeded_by_key["rfq-001-clean-created"].status is WorkflowStatus.CREATED
    assert (
        seeded_by_key["rfq-001-waiting-approval-history"].status
        is WorkflowStatus.WAITING_APPROVAL
    )


@pytest.mark.asyncio
async def test_seeded_event_backlog_is_readable_and_ordered(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)
    event_service = WorkflowEventService(db_session)
    history_workflow = next(
        workflow
        for workflow in DEMO_WORKFLOWS
        if workflow.key == "rfq-001-waiting-approval-history"
    )

    events = await event_service.list_events_for_workflow(
        history_workflow.stable_workflow_id,
    )

    assert [event.event_id for event in events] == [
        event.stable_event_id for event in DEMO_WORKFLOW_EVENTS
    ]
    assert events[0].event_type == "workflow.runtime.started"
    assert events[0].status is WorkflowEventStatus.STARTED
    assert events[-1].event_type == "workflow.runtime.waiting_for_approval"
    assert all(event.payload["demo_reference_only"] is True for event in events)


@pytest.mark.asyncio
async def test_seed_demo_workflows_and_events_is_idempotent(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)
    first_workflow_count = await _demo_workflow_count(db_session)
    first_event_count = await _demo_event_count(db_session)

    result = await seed_demo_workflows_and_events(db_session)
    second_workflow_count = await _demo_workflow_count(db_session)
    second_event_count = await _demo_event_count(db_session)

    assert second_workflow_count == first_workflow_count
    assert second_event_count == first_event_count
    assert result.workflows_created == 0
    assert result.events_created == 0
    assert result.workflows_reused == len(DEMO_WORKFLOWS)
    assert result.events_reused == len(DEMO_WORKFLOW_EVENTS)


@pytest.mark.asyncio
async def test_seed_does_not_delete_or_modify_non_demo_workflow_or_event(
    db_session: AsyncSession,
) -> None:
    user = User(
        email=f"non-demo-{uuid4()}@example.test",
        hashed_password="not-a-real-hash",
        full_name="Non Demo User",
    )
    workflow = Workflow(
        workflow_type="procurement_quotation",
        domain="office_furniture",
        status=WorkflowStatus.CREATED,
        created_by=user,
        request_payload={"source": "non-demo"},
        state_payload={"non_demo": True},
    )
    event = WorkflowEvent(
        workflow=workflow,
        event_type="non.demo.event",
        status=WorkflowEventStatus.STARTED,
        payload={"non_demo": True},
    )
    db_session.add_all([user, workflow, event])
    await db_session.flush()
    workflow_id = workflow.id
    event_id = event.id

    await seed_demo_workflows_and_events(db_session)
    found_workflow = await db_session.get(Workflow, workflow_id)
    found_event = await db_session.get(WorkflowEvent, event_id)

    assert found_workflow is workflow
    assert found_workflow.request_payload == {"source": "non-demo"}
    assert found_workflow.state_payload == {"non_demo": True}
    assert found_event is event
    assert found_event.payload == {"non_demo": True}


@pytest.mark.asyncio
async def test_seed_function_does_not_commit(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_commit() -> None:
        raise AssertionError("workflow seed helper must not commit")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    await seed_demo_workflows_and_events(db_session)


async def _demo_workflows(session: AsyncSession) -> list[Workflow]:
    workflow_ids = [workflow.stable_workflow_id for workflow in DEMO_WORKFLOWS]
    statement = (
        select(Workflow).where(Workflow.id.in_(workflow_ids)).order_by(Workflow.id)
    )
    result = await session.scalars(statement)
    return list(result.all())


async def _demo_events(session: AsyncSession) -> list[WorkflowEvent]:
    event_ids = [event.stable_event_id for event in DEMO_WORKFLOW_EVENTS]
    statement = (
        select(WorkflowEvent)
        .where(WorkflowEvent.id.in_(event_ids))
        .order_by(WorkflowEvent.created_at, WorkflowEvent.id)
    )
    result = await session.scalars(statement)
    return list(result.all())


async def _demo_workflow_count(session: AsyncSession) -> int:
    workflow_ids = [workflow.stable_workflow_id for workflow in DEMO_WORKFLOWS]
    count = await session.scalar(
        select(func.count()).select_from(Workflow).where(Workflow.id.in_(workflow_ids)),
    )
    assert count is not None
    return count


async def _demo_event_count(session: AsyncSession) -> int:
    event_ids = [event.stable_event_id for event in DEMO_WORKFLOW_EVENTS]
    count = await session.scalar(
        select(func.count())
        .select_from(WorkflowEvent)
        .where(
            WorkflowEvent.id.in_(event_ids),
        ),
    )
    assert count is not None
    return count
