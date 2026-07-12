"""Tests for deterministic runtime service orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.models.enums import WorkflowStatus
from app.runtime import (
    PRE_APPROVAL_RUNTIME_STAGES,
    RuntimeNodeHandlers,
    RuntimeService,
    RuntimeStage,
    RuntimeWorkflowState,
    WorkflowRuntimeNodeError,
    WorkflowRuntimePreconditionError,
    create_deterministic_node_handlers,
)
from app.workflows import (
    WorkflowEventService,
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowStateCreate,
)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for runtime service tests."""
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
    """Create typed workflow input for runtime service tests."""
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


def _runtime_service(
    db_session: AsyncSession,
    *,
    node_handlers: RuntimeNodeHandlers | None = None,
) -> RuntimeService:
    workflow_service = WorkflowService(db_session)
    event_service = WorkflowEventService(db_session)
    return RuntimeService(
        workflow_service,
        event_service,
        node_handlers=node_handlers,
    )


@pytest.mark.asyncio
async def test_runtime_service_runs_created_workflow_to_waiting_approval(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    created_state = await workflow_service.create_workflow(
        build_workflow_state_create()
    )
    workflow_id = UUID(created_state.workflow_id)
    runtime_service = RuntimeService(
        workflow_service,
        WorkflowEventService(db_session),
    )

    result = await runtime_service.run_workflow(
        workflow_id,
        actor_type="user",
        actor_id=uuid4(),
    )
    persisted_state = await workflow_service.get_workflow(workflow_id)

    assert result.completed is False
    assert result.failed is False
    assert result.message == "Workflow is waiting for approval."
    assert result.state.status is WorkflowStatus.WAITING_APPROVAL
    assert result.state.current_stage is RuntimeStage.APPROVAL
    assert result.state.completed_stages == PRE_APPROVAL_RUNTIME_STAGES
    assert RuntimeStage.EMAIL_PREPARATION not in result.state.completed_stages
    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.WAITING_APPROVAL
    assert persisted_state.current_step == "approval"
    assert persisted_state.email == {}
    assert persisted_state.approval["approval_decision_made"] is False


@pytest.mark.asyncio
async def test_runtime_service_appends_runtime_and_node_events(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    created_state = await workflow_service.create_workflow(
        build_workflow_state_create()
    )
    workflow_id = UUID(created_state.workflow_id)
    event_service = WorkflowEventService(db_session)
    runtime_service = RuntimeService(workflow_service, event_service)

    await runtime_service.run_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    event_types = [event.event_type for event in events]
    expected_event_types = ["workflow.runtime.started"]
    for _stage in PRE_APPROVAL_RUNTIME_STAGES:
        expected_event_types.extend(
            ["workflow.node.started", "workflow.node.completed"],
        )
    expected_event_types.append("workflow.runtime.waiting_for_approval")

    assert event_types == expected_event_types
    assert events[0].payload == {
        "workflow_id": str(workflow_id),
        "status": WorkflowStatus.CREATED.value,
    }
    assert events[-1].payload == {
        "workflow_id": str(workflow_id),
        "status": WorkflowStatus.WAITING_APPROVAL.value,
        "completed_stages": [stage.value for stage in PRE_APPROVAL_RUNTIME_STAGES],
    }
    for stage in PRE_APPROVAL_RUNTIME_STAGES:
        stage_events = [event for event in events if event.agent_name == stage.value]
        assert [event.event_type for event in stage_events] == [
            "workflow.node.started",
            "workflow.node.completed",
        ]
        assert stage_events[0].payload == {
            "workflow_id": str(workflow_id),
            "stage": stage.value,
            "workflow_status": runtime_stage_status(stage),
        }
        assert stage_events[1].payload["stage_output"] == {
            "stage": stage.value,
            "status": "completed",
            "summary": stage_events[1].payload["stage_output"]["summary"],
            "placeholder": True,
        }
        assert "raw_text" not in stage_events[1].payload["stage_output"]
        assert "request_present" not in stage_events[1].payload["stage_output"]
    assert "email_preparation" not in {
        event.agent_name for event in events if event.agent_name
    }


@pytest.mark.asyncio
async def test_runtime_service_raises_for_missing_workflow(
    db_session: AsyncSession,
) -> None:
    runtime_service = _runtime_service(db_session)

    with pytest.raises(WorkflowNotFoundError):
        await runtime_service.run_workflow(uuid4())


@pytest.mark.asyncio
async def test_runtime_service_rejects_non_created_workflow_without_status_change(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    created_state = await workflow_service.create_workflow(
        build_workflow_state_create()
    )
    workflow_id = UUID(created_state.workflow_id)
    planning_state = await workflow_service.transition_workflow_status(
        workflow_id,
        WorkflowStatus.PLANNING,
    )
    event_service = WorkflowEventService(db_session)
    runtime_service = RuntimeService(workflow_service, event_service)

    with pytest.raises(WorkflowRuntimePreconditionError):
        await runtime_service.run_workflow(workflow_id)

    persisted_state = await workflow_service.get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    assert persisted_state is not None
    assert planning_state.status is WorkflowStatus.PLANNING
    assert persisted_state.status is WorkflowStatus.PLANNING
    assert [event.event_type for event in events][-1] == "workflow.runtime.failed"


@pytest.mark.asyncio
async def test_runtime_service_persists_failure_state_and_events(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    created_state = await workflow_service.create_workflow(
        build_workflow_state_create()
    )
    workflow_id = UUID(created_state.workflow_id)
    handlers = create_deterministic_node_handlers()

    def failing_retrieval_node(
        state: RuntimeWorkflowState,
    ) -> RuntimeWorkflowState:
        raise RuntimeError("deterministic retrieval failure")

    handlers[RuntimeStage.RETRIEVAL] = failing_retrieval_node
    event_service = WorkflowEventService(db_session)
    runtime_service = RuntimeService(
        workflow_service,
        event_service,
        node_handlers=handlers,
    )

    with pytest.raises(WorkflowRuntimeNodeError) as exc_info:
        await runtime_service.run_workflow(workflow_id)

    persisted_state = await workflow_service.get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    event_types = [event.event_type for event in events]

    assert exc_info.value.stage is RuntimeStage.RETRIEVAL
    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.FAILED
    assert persisted_state.current_step == "planner"
    assert persisted_state.runtime_context["failed_stage"] == "retrieval"
    assert persisted_state.error is not None
    assert persisted_state.error.code == "RUNTIME_NODE_FAILED"
    assert persisted_state.error.message == "Runtime stage retrieval failed."
    assert persisted_state.error.details == {"error_type": "RuntimeError"}
    assert "workflow.node.failed" in event_types
    assert "workflow.runtime.failed" in event_types
    node_failed_event = next(
        event for event in events if event.event_type == "workflow.node.failed"
    )
    runtime_failed_event = next(
        event for event in events if event.event_type == "workflow.runtime.failed"
    )
    assert node_failed_event.payload == {
        "workflow_id": str(workflow_id),
        "stage": "retrieval",
        "workflow_status": WorkflowStatus.RETRIEVING.value,
        "error_type": "RuntimeError",
    }
    assert runtime_failed_event.payload == {
        "workflow_id": str(workflow_id),
        "failed_stage": "retrieval",
        "status": WorkflowStatus.RETRIEVING.value,
        "error_type": "RuntimeError",
    }
    assert "deterministic retrieval failure" not in str(node_failed_event.payload)
    assert "deterministic retrieval failure" not in str(runtime_failed_event.payload)


@pytest.mark.asyncio
async def test_runtime_service_does_not_commit(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_service = WorkflowService(db_session)
    created_state = await workflow_service.create_workflow(
        build_workflow_state_create()
    )
    runtime_service = RuntimeService(
        workflow_service,
        WorkflowEventService(db_session),
    )

    async def fail_commit() -> None:
        raise AssertionError("RuntimeService attempted to commit")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    result = await runtime_service.run_workflow(UUID(created_state.workflow_id))

    assert result.state.status is WorkflowStatus.WAITING_APPROVAL


def test_runtime_service_module_imports_without_api_routes() -> None:
    assert RuntimeService is not None


def runtime_stage_status(stage: RuntimeStage) -> str:
    """Return the persisted workflow status value for a runtime stage."""
    return {
        RuntimeStage.PLANNER: WorkflowStatus.PLANNING,
        RuntimeStage.RETRIEVAL: WorkflowStatus.RETRIEVING,
        RuntimeStage.QUOTATION: WorkflowStatus.CALCULATING,
        RuntimeStage.COMPLIANCE: WorkflowStatus.CHECKING_COMPLIANCE,
        RuntimeStage.VALIDATION: WorkflowStatus.VALIDATING,
        RuntimeStage.APPROVAL: WorkflowStatus.WAITING_APPROVAL,
    }[stage].value
