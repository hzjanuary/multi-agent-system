"""Tests for the workflow service foundation."""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.models import Workflow
from app.models.enums import WorkflowStatus
from app.workflows import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowStateCreate,
    WorkflowStateMismatchError,
)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for workflow service tests."""
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


def build_workflow_state_create(
    *,
    domain: str | None = "it_equipment",
    raw_text: str = "Need 50 business laptops.",
) -> WorkflowStateCreate:
    """Create typed workflow input for service tests."""
    return WorkflowStateCreate.model_validate(
        {
            "workflow_type": "procurement_quotation",
            "domain": domain,
            "request": {
                "raw_text": raw_text,
                "source": "manual_text",
                "uploaded_document_ids": [],
            },
        },
    )


@pytest.mark.asyncio
async def test_workflow_service_create_persists_workflow_record(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)

    state = await service.create_workflow(build_workflow_state_create())

    workflow_id = UUID(state.workflow_id)
    workflow = await db_session.get(Workflow, workflow_id)

    assert workflow is not None
    assert workflow.workflow_type == "procurement_quotation"
    assert workflow.domain == "it_equipment"
    assert workflow.status is WorkflowStatus.CREATED
    assert workflow.request_payload["raw_text"] == "Need 50 business laptops."
    assert workflow.state_payload["workflow_id"] == state.workflow_id
    assert state.status is WorkflowStatus.CREATED


@pytest.mark.asyncio
async def test_workflow_service_get_reads_typed_state(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    created_state = await service.create_workflow(build_workflow_state_create())

    found_state = await service.get_workflow(UUID(created_state.workflow_id))

    assert found_state is not None
    assert found_state.workflow_id == created_state.workflow_id
    assert found_state.workflow_type == created_state.workflow_type
    assert found_state.request["source"] == "manual_text"


@pytest.mark.asyncio
async def test_workflow_service_get_returns_none_for_missing_workflow(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)

    assert await service.get_workflow(uuid4()) is None


@pytest.mark.asyncio
async def test_workflow_service_lists_workflows_with_filters(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    first_domain = f"it_equipment_test_{uuid4().hex}"
    second_domain = f"software_subscription_test_{uuid4().hex}"
    first = await service.create_workflow(
        build_workflow_state_create(domain=first_domain),
    )
    second = await service.create_workflow(
        build_workflow_state_create(domain=second_domain),
    )
    await service.transition_workflow_status(
        UUID(second.workflow_id),
        WorkflowStatus.PLANNING,
    )

    it_workflows = await service.list_workflows(domain=first_domain)
    planning_workflows = await service.list_workflows(status=WorkflowStatus.PLANNING)

    assert {workflow.workflow_id for workflow in it_workflows} == {first.workflow_id}
    assert {workflow.workflow_id for workflow in planning_workflows} == {
        second.workflow_id,
    }


@pytest.mark.asyncio
async def test_workflow_service_transitions_status_with_validation(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    created_state = await service.create_workflow(build_workflow_state_create())

    transitioned_state = await service.transition_workflow_status(
        UUID(created_state.workflow_id),
        WorkflowStatus.PLANNING,
    )
    workflow = await db_session.get(Workflow, UUID(created_state.workflow_id))

    assert transitioned_state.status is WorkflowStatus.PLANNING
    assert workflow is not None
    assert workflow.status is WorkflowStatus.PLANNING
    assert workflow.state_payload["status"] == "PLANNING"


@pytest.mark.asyncio
async def test_workflow_service_rejects_invalid_transition(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    created_state = await service.create_workflow(build_workflow_state_create())

    with pytest.raises(InvalidWorkflowTransitionError):
        await service.transition_workflow_status(
            UUID(created_state.workflow_id),
            WorkflowStatus.COMPLETED,
        )

    workflow = await db_session.get(Workflow, UUID(created_state.workflow_id))
    assert workflow is not None
    assert workflow.status is WorkflowStatus.CREATED


@pytest.mark.asyncio
async def test_workflow_service_rejects_terminal_status_transition(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    created_state = await service.create_workflow(build_workflow_state_create())
    cancelled_state = await service.transition_workflow_status(
        UUID(created_state.workflow_id),
        WorkflowStatus.CANCELLED,
    )

    with pytest.raises(InvalidWorkflowTransitionError):
        await service.transition_workflow_status(
            UUID(cancelled_state.workflow_id),
            WorkflowStatus.PLANNING,
        )


@pytest.mark.asyncio
async def test_workflow_service_updates_state_payload(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    created_state = await service.create_workflow(build_workflow_state_create())
    updated_input = created_state.model_copy(
        update={
            "current_step": "planner",
            "planner": {"plan_id": "plan-001"},
            "runtime_context": {"correlation_id": "workflow-test"},
        },
    )

    updated_state = await service.update_workflow_state(
        UUID(created_state.workflow_id),
        updated_input,
    )

    assert updated_state.current_step == "planner"
    assert updated_state.planner == {"plan_id": "plan-001"}
    assert updated_state.runtime_context == {"correlation_id": "workflow-test"}


@pytest.mark.asyncio
async def test_workflow_service_rejects_state_id_mismatch(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)
    created_state = await service.create_workflow(build_workflow_state_create())
    mismatched_state = created_state.model_copy(update={"workflow_id": str(uuid4())})

    with pytest.raises(WorkflowStateMismatchError):
        await service.update_workflow_state(
            UUID(created_state.workflow_id),
            mismatched_state,
        )


@pytest.mark.asyncio
async def test_workflow_service_raises_for_missing_workflow_transition(
    db_session: AsyncSession,
) -> None:
    service = WorkflowService(db_session)

    with pytest.raises(WorkflowNotFoundError):
        await service.transition_workflow_status(uuid4(), WorkflowStatus.PLANNING)
