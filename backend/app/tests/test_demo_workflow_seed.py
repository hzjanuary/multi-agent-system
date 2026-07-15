"""Tests for SPEC-010 demo workflow and event seeding."""

from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.approvals import (
    APPROVAL_APPROVED_EVENT,
    APPROVAL_CHANGES_REQUESTED_EVENT,
    APPROVAL_HISTORY_KEY,
    APPROVAL_REJECTED_EVENT,
    APPROVAL_STATE_KEY,
    WORKFLOW_RESUME_REQUESTED_EVENT,
    WORKFLOW_RESUMED_EVENT,
)
from app.approvals.schemas import ApprovalDecisionType, ApprovalRecord
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
    assert (
        seeded_by_key["rfq-001-approved-ready-to-resume"].status
        is WorkflowStatus.APPROVED
    )
    assert (
        seeded_by_key["rfq-001-completed-resumed-history"].status
        is WorkflowStatus.COMPLETED
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

    expected_event_ids = [
        event.stable_event_id
        for event in DEMO_WORKFLOW_EVENTS
        if event.workflow_key == history_workflow.key
    ]
    assert [event.event_id for event in events] == expected_event_ids
    assert events[0].event_type == "workflow.runtime.started"
    assert events[0].status is WorkflowEventStatus.STARTED
    assert events[-1].event_type == "workflow.runtime.waiting_for_approval"
    assert all(event.payload["demo_reference_only"] is True for event in events)


@pytest.mark.asyncio
async def test_seeded_approval_examples_match_approval_contracts(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)
    workflows_by_key = {
        definition.key: await db_session.get(Workflow, definition.stable_workflow_id)
        for definition in DEMO_WORKFLOWS
    }

    waiting = workflows_by_key["rfq-001-waiting-approval-history"]
    approved = workflows_by_key["rfq-001-approved-ready-to-resume"]
    completed = workflows_by_key["rfq-001-completed-resumed-history"]
    rejected = workflows_by_key["rfq-001-rejected-history"]

    assert waiting is not None
    waiting_state = WorkflowState.model_validate(waiting.state_payload)
    assert waiting_state.status is WorkflowStatus.WAITING_APPROVAL
    assert waiting_state.approval[APPROVAL_HISTORY_KEY] == []
    assert waiting_state.approval[APPROVAL_STATE_KEY]["can_resume"] is False

    assert approved is not None
    approved_state = WorkflowState.model_validate(approved.state_payload)
    approved_records = _approval_records(approved_state)
    assert approved_state.status is WorkflowStatus.APPROVED
    assert [record.decision for record in approved_records] == [
        ApprovalDecisionType.APPROVE,
    ]
    assert approved_state.approval[APPROVAL_STATE_KEY]["can_resume"] is True

    assert completed is not None
    completed_state = WorkflowState.model_validate(completed.state_payload)
    completed_records = _approval_records(completed_state)
    assert completed_state.status is WorkflowStatus.COMPLETED
    assert [record.decision for record in completed_records] == [
        ApprovalDecisionType.REQUEST_CHANGES,
        ApprovalDecisionType.APPROVE,
    ]
    assert completed_state.runtime_context["resume_state"] == {
        "resumed": True,
        "resumed_by": str(completed_records[-1].actor_id),
        "request_id": "demo-resume-completed",
        "completed_stages": ["email_preparation"],
    }
    assert completed_state.email["email_sent"] is False

    assert rejected is not None
    rejected_state = WorkflowState.model_validate(rejected.state_payload)
    rejected_records = _approval_records(rejected_state)
    assert rejected_state.status is WorkflowStatus.REJECTED
    assert [record.decision for record in rejected_records] == [
        ApprovalDecisionType.REJECT,
    ]
    assert rejected_state.approval[APPROVAL_STATE_KEY]["can_resume"] is False


@pytest.mark.asyncio
async def test_seeded_approval_resume_events_use_known_constants(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)
    events = await _demo_events(db_session)
    events_by_workflow_key: dict[str, list[WorkflowEvent]] = {}
    workflow_key_by_id = {
        definition.stable_workflow_id: definition.key for definition in DEMO_WORKFLOWS
    }
    for event in events:
        workflow_key = workflow_key_by_id[event.workflow_id]
        events_by_workflow_key.setdefault(workflow_key, []).append(event)

    approved_events = events_by_workflow_key["rfq-001-approved-ready-to-resume"]
    assert [event.event_type for event in approved_events] == [
        "workflow.runtime.waiting_for_approval",
        APPROVAL_APPROVED_EVENT,
    ]

    completed_events = events_by_workflow_key["rfq-001-completed-resumed-history"]
    assert [event.event_type for event in completed_events] == [
        APPROVAL_CHANGES_REQUESTED_EVENT,
        APPROVAL_APPROVED_EVENT,
        WORKFLOW_RESUME_REQUESTED_EVENT,
        "workflow.node.started",
        "workflow.node.completed",
        WORKFLOW_RESUMED_EVENT,
    ]
    assert completed_events[-2].payload["email_sent"] is False

    rejected_events = events_by_workflow_key["rfq-001-rejected-history"]
    assert [event.event_type for event in rejected_events] == [
        APPROVAL_REJECTED_EVENT,
    ]


@pytest.mark.asyncio
async def test_seeded_approval_resume_payloads_do_not_include_secrets(
    db_session: AsyncSession,
) -> None:
    await seed_demo_workflows_and_events(db_session)
    workflows = await _demo_workflows(db_session)
    events = await _demo_events(db_session)
    combined_payload_text = " ".join(
        [
            *(str(workflow.state_payload) for workflow in workflows),
            *(str(event.payload) for event in events),
        ],
    ).lower()

    assert "api_key" not in combined_payload_text
    assert "authorization" not in combined_payload_text
    assert "password" not in combined_payload_text
    assert "provider_payload" not in combined_payload_text
    assert "raw_prompt" not in combined_payload_text


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


def _approval_records(state: WorkflowState) -> list[ApprovalRecord]:
    raw_records = state.approval.get(APPROVAL_HISTORY_KEY, [])
    assert isinstance(raw_records, list)
    return [ApprovalRecord.model_validate(record) for record in raw_records]
