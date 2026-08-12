"""Tests for bounded post-approval runtime resume behavior."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Sequence
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.approvals import (
    WORKFLOW_RESUME_FAILED_EVENT,
    WORKFLOW_RESUME_REQUESTED_EVENT,
    WORKFLOW_RESUMED_EVENT,
    ApprovalDecisionRequest,
    ApprovalDecisionType,
    ApprovalService,
    ResumeNotAllowedError,
    WorkflowResumeRequest,
)
from app.auth import hash_password
from app.auth.rbac import RoleName
from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.models import AuditLog, Role, User, WorkflowEvent
from app.models.enums import WorkflowStatus
from app.runtime import (
    POST_APPROVAL_RUNTIME_STAGES,
    RuntimeNodeHandlers,
    RuntimeService,
    RuntimeStage,
    RuntimeWorkflowState,
    WorkflowRuntimeNodeError,
    create_deterministic_node_handlers,
)
from app.workflows import (
    WorkflowEventService,
    WorkflowNotFoundError,
    WorkflowService,
    WorkflowStateCreate,
)
from app.workflows.audit import WORKFLOW_EVENT_APPENDED_ACTION


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for runtime resume tests."""
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
    """Create typed workflow input for runtime resume tests."""
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
    return RuntimeService(
        WorkflowService(db_session),
        WorkflowEventService(db_session),
        node_handlers=node_handlers,
    )


@pytest.mark.asyncio
async def test_resume_after_approval_completes_email_preparation(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_approved_workflow(db_session, actor)
    runtime_service = _runtime_service(db_session)

    result = await runtime_service.resume_workflow_after_approval(
        workflow_id,
        WorkflowResumeRequest(
            request_id="resume-001",
            metadata={
                "operator_note": "board demo resume",
                "api_key": "must-not-persist",
            },
        ),
        actor_type="user",
        actor_id=actor.id,
    )
    persisted_state = await WorkflowService(db_session).get_workflow(workflow_id)
    events = await list_workflow_events(db_session, workflow_id)
    audit_logs = await list_audit_logs(db_session, workflow_id)
    event_types = [event.event_type for event in events]

    assert result.completed is True
    assert result.failed is False
    assert result.state.status is WorkflowStatus.COMPLETED
    assert result.state.current_stage is RuntimeStage.EMAIL_PREPARATION
    assert result.state.completed_stages == POST_APPROVAL_RUNTIME_STAGES
    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.COMPLETED
    assert persisted_state.current_step == "email_preparation"
    assert persisted_state.email["email_sent"] is False
    assert persisted_state.runtime_context["resume_state"] == {
        "resumed": True,
        "resumed_by": str(actor.id),
        "request_id": "resume-001",
        "completed_stages": ["email_preparation"],
    }
    assert event_types[-4:] == [
        WORKFLOW_RESUME_REQUESTED_EVENT,
        "workflow.node.started",
        "workflow.node.completed",
        WORKFLOW_RESUMED_EVENT,
    ]
    assert events[-4].payload["metadata"] == {"operator_note": "board demo resume"}
    assert audit_logs[-1].action == WORKFLOW_EVENT_APPENDED_ACTION
    serialized = json.dumps(
        {
            "state": persisted_state.model_dump(mode="json"),
            "events": [event.payload for event in events],
            "audit": [audit.payload for audit in audit_logs],
        },
    )
    assert "must-not-persist" not in serialized
    assert "api_key" not in serialized


@pytest.mark.asyncio
async def test_resume_service_does_not_commit(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.ADMIN)
    workflow_id = await create_approved_workflow(db_session, actor)
    runtime_service = _runtime_service(db_session)

    async def fail_commit() -> None:
        raise AssertionError("RuntimeService attempted to commit")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    result = await runtime_service.resume_workflow_after_approval(workflow_id)

    assert result.state.status is WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_resume_rejects_workflow_without_approval(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    state = await workflow_service.create_workflow(build_workflow_state_create())
    workflow_id = UUID(state.workflow_id)
    event_service = WorkflowEventService(db_session)
    runtime_service = RuntimeService(workflow_service, event_service)

    with pytest.raises(ResumeNotAllowedError):
        await runtime_service.resume_workflow_after_approval(workflow_id)

    events = await event_service.list_events_for_workflow(workflow_id)
    assert events[-1].event_type == WORKFLOW_RESUME_FAILED_EVENT


@pytest.mark.asyncio
async def test_resume_rejects_rejected_workflow(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_waiting_workflow(db_session)
    await ApprovalService(db_session).submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.REJECT,
            comment="Not acceptable.",
        ),
        actor,
    )

    with pytest.raises(ResumeNotAllowedError):
        await _runtime_service(db_session).resume_workflow_after_approval(workflow_id)


@pytest.mark.asyncio
async def test_resume_rejects_request_changes_only_workflow(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_waiting_workflow(db_session)
    await ApprovalService(db_session).submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.REQUEST_CHANGES,
            comment="Add more detail.",
        ),
        actor,
    )

    with pytest.raises(ResumeNotAllowedError):
        await _runtime_service(db_session).resume_workflow_after_approval(workflow_id)


@pytest.mark.asyncio
async def test_duplicate_resume_is_rejected_after_completion(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.ADMIN)
    workflow_id = await create_approved_workflow(db_session, actor)
    runtime_service = _runtime_service(db_session)
    await runtime_service.resume_workflow_after_approval(workflow_id)

    with pytest.raises(ResumeNotAllowedError):
        await runtime_service.resume_workflow_after_approval(workflow_id)


@pytest.mark.asyncio
async def test_resume_missing_workflow_raises_not_found(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(WorkflowNotFoundError):
        await _runtime_service(db_session).resume_workflow_after_approval(UUID(int=1))


@pytest.mark.asyncio
async def test_resume_failure_persists_safe_failure_state_and_events(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_approved_workflow(db_session, actor)
    handlers = create_deterministic_node_handlers()

    def failing_email_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
        raise RuntimeError("smtp secret should not leak")

    handlers[RuntimeStage.EMAIL_PREPARATION] = failing_email_node
    event_service = WorkflowEventService(db_session)
    runtime_service = RuntimeService(
        WorkflowService(db_session),
        event_service,
        node_handlers=handlers,
    )

    with pytest.raises(WorkflowRuntimeNodeError):
        await runtime_service.resume_workflow_after_approval(workflow_id)

    persisted_state = await WorkflowService(db_session).get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    payload_text = json.dumps([event.payload for event in events])

    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.FAILED
    assert persisted_state.error is not None
    assert persisted_state.error.code == "RUNTIME_NODE_FAILED"
    assert WORKFLOW_RESUME_FAILED_EVENT in [event.event_type for event in events]
    assert "smtp secret should not leak" not in payload_text


@pytest.mark.asyncio
async def test_resume_cancellation_persists_safe_cancellation_event(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_approved_workflow(db_session, actor)
    handlers = create_deterministic_node_handlers()

    def cancelling_email_node(state: RuntimeWorkflowState) -> RuntimeWorkflowState:
        raise asyncio.CancelledError()

    handlers[RuntimeStage.EMAIL_PREPARATION] = cancelling_email_node
    event_service = WorkflowEventService(db_session)
    runtime_service = RuntimeService(
        WorkflowService(db_session),
        event_service,
        node_handlers=handlers,
    )

    with pytest.raises(asyncio.CancelledError):
        await runtime_service.resume_workflow_after_approval(workflow_id)

    persisted_state = await WorkflowService(db_session).get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    event_types = [event.event_type for event in events]

    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.GENERATING_EMAIL
    assert persisted_state.error is None
    assert "workflow.runtime.cancelled" in event_types
    assert WORKFLOW_RESUME_FAILED_EVENT not in event_types
    assert "workflow.node.failed" not in event_types
    assert "workflow.runtime.failed" not in event_types


async def create_approved_workflow(
    db_session: AsyncSession,
    actor: User,
) -> UUID:
    """Create a waiting workflow and approve it."""
    workflow_id = await create_waiting_workflow(db_session)
    await ApprovalService(db_session).submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            comment="Approved for resume.",
        ),
        actor,
    )
    return workflow_id


async def create_waiting_workflow(db_session: AsyncSession) -> UUID:
    """Create a workflow and transition it to WAITING_APPROVAL."""
    workflow_service = WorkflowService(db_session)
    state = await workflow_service.create_workflow(build_workflow_state_create())
    workflow_id = UUID(state.workflow_id)
    for status in (
        WorkflowStatus.PLANNING,
        WorkflowStatus.RETRIEVING,
        WorkflowStatus.CALCULATING,
        WorkflowStatus.CHECKING_COMPLIANCE,
        WorkflowStatus.VALIDATING,
        WorkflowStatus.WAITING_APPROVAL,
    ):
        await workflow_service.transition_workflow_status(workflow_id, status)
    return workflow_id


async def create_user_with_role(
    db_session: AsyncSession,
    role_name: RoleName,
) -> User:
    """Create an actor with one role."""
    role = await ensure_role(db_session, role_name)
    user = User(
        email=f"{role_name.value.lower()}-resume@example.test",
        hashed_password=hash_password("not-used-in-resume-tests"),
        roles=[role],
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def ensure_role(session: AsyncSession, role_name: RoleName) -> Role:
    """Create or reuse an RBAC role."""
    role = await session.scalar(select(Role).where(Role.name == role_name.value))
    if role is not None:
        return role
    role = Role(name=role_name.value, description=f"{role_name.value} role")
    session.add(role)
    await session.flush()
    return role


async def list_workflow_events(
    db_session: AsyncSession,
    workflow_id: UUID,
) -> Sequence[WorkflowEvent]:
    """Return workflow events in deterministic order."""
    statement = (
        select(WorkflowEvent)
        .where(WorkflowEvent.workflow_id == workflow_id)
        .order_by(WorkflowEvent.created_at, WorkflowEvent.id)
    )
    return (await db_session.scalars(statement)).all()


async def list_audit_logs(
    db_session: AsyncSession,
    workflow_id: UUID,
) -> Sequence[AuditLog]:
    """Return workflow audit logs in deterministic order."""
    statement = (
        select(AuditLog)
        .where(AuditLog.workflow_id == workflow_id)
        .order_by(AuditLog.created_at, AuditLog.id)
    )
    return (await db_session.scalars(statement)).all()
