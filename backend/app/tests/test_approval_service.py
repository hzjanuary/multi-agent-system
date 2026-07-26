"""Tests for approval decision persistence service."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.approvals import (
    APPROVAL_APPROVED_EVENT,
    APPROVAL_CHANGES_REQUESTED_EVENT,
    APPROVAL_DECISION_AUDIT_ACTION,
    APPROVAL_HISTORY_KEY,
    APPROVAL_REJECTED_EVENT,
    ApprovalDecisionRequest,
    ApprovalDecisionType,
    ApprovalInvalidStateError,
    ApprovalPermissionDeniedError,
    ApprovalService,
    ApprovalTerminalStateError,
    DuplicateFinalApprovalDecisionError,
)
from app.auth import hash_password
from app.auth.rbac import RoleName
from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.models import AuditLog, Role, User, Workflow, WorkflowEvent
from app.models.enums import WorkflowStatus
from app.workflows import WorkflowService, WorkflowStateCreate


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for approval service tests."""
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
    """Create typed workflow input for approval service tests."""
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


@pytest.mark.asyncio
async def test_approval_service_approve_records_state_event_and_audit(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_waiting_workflow(db_session)
    service = ApprovalService(db_session)

    response = await service.submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            comment="Approved for demo purchase.",
            request_id="approval-001",
            metadata={
                "review_notes": "Budget holder confirmed.",
                "api_key": "must-not-be-stored",
            },
        ),
        actor,
    )

    workflow = await db_session.get(Workflow, workflow_id)
    events = await list_workflow_events(db_session, workflow_id)
    audit_logs = await list_audit_logs(db_session, workflow_id)
    history = await service.get_approval_history(workflow_id)

    assert response.next_status is WorkflowStatus.APPROVED
    assert response.can_resume is True
    assert workflow is not None
    assert workflow.status is WorkflowStatus.APPROVED
    assert workflow.state_payload["status"] == "APPROVED"
    approval_payload = cast(dict[str, object], workflow.state_payload["approval"])
    approval_history = cast(
        list[dict[str, object]],
        approval_payload[APPROVAL_HISTORY_KEY],
    )
    assert len(approval_history) == 1
    assert approval_history[0]["decision"] == "approve"
    assert approval_history[0]["metadata"] == {
        "review_notes": "Budget holder confirmed.",
    }
    assert history.has_final_decision is True
    assert history.can_resume is True
    assert [record.decision for record in history.approvals] == [
        ApprovalDecisionType.APPROVE,
    ]
    approval_event = events[-1]
    assert approval_event.event_type == APPROVAL_APPROVED_EVENT
    assert approval_event.actor_id == actor.id
    assert approval_event.payload["decision"] == "approve"
    assert approval_event.payload["can_resume"] is True
    approval_audit = audit_logs[-1]
    assert approval_audit.action == APPROVAL_DECISION_AUDIT_ACTION
    assert approval_audit.actor_id == actor.id
    assert approval_audit.payload["decision"] == "approve"
    serialized = json.dumps(
        {
            "state": workflow.state_payload,
            "event": approval_event.payload,
            "audit": approval_audit.payload,
        },
    )
    assert "must-not-be-stored" not in serialized
    assert "api_key" not in serialized


@pytest.mark.asyncio
async def test_approval_service_reject_records_final_decision(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.ADMIN)
    workflow_id = await create_waiting_workflow(db_session)
    service = ApprovalService(db_session)

    response = await service.submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.REJECT,
            comment="Supplier terms are not acceptable.",
        ),
        actor,
    )
    workflow = await db_session.get(Workflow, workflow_id)
    events = await list_workflow_events(db_session, workflow_id)

    assert response.next_status is WorkflowStatus.REJECTED
    assert response.can_resume is False
    assert workflow is not None
    assert workflow.status is WorkflowStatus.REJECTED
    assert events[-1].event_type == APPROVAL_REJECTED_EVENT
    assert events[-1].payload["decision"] == "reject"


@pytest.mark.asyncio
async def test_request_changes_is_non_final_and_allows_later_approval(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_waiting_workflow(db_session)
    service = ApprovalService(db_session)

    changes_response = await service.submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.REQUEST_CHANGES,
            comment="Add warranty comparison.",
        ),
        actor,
    )
    approve_response = await service.submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            comment="Revision is acceptable.",
        ),
        actor,
    )
    history = await service.get_approval_history(workflow_id)
    events = await list_workflow_events(db_session, workflow_id)

    assert changes_response.next_status is WorkflowStatus.WAITING_APPROVAL
    assert changes_response.can_resume is False
    assert approve_response.next_status is WorkflowStatus.APPROVED
    assert [record.decision for record in history.approvals] == [
        ApprovalDecisionType.REQUEST_CHANGES,
        ApprovalDecisionType.APPROVE,
    ]
    assert events[-2].event_type == APPROVAL_CHANGES_REQUESTED_EVENT
    assert events[-1].event_type == APPROVAL_APPROVED_EVENT


@pytest.mark.asyncio
async def test_duplicate_final_decision_is_rejected(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_waiting_workflow(db_session)
    service = ApprovalService(db_session)
    await service.submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            comment="Approved.",
        ),
        actor,
    )

    with pytest.raises(DuplicateFinalApprovalDecisionError):
        await service.submit_approval_decision(
            workflow_id,
            ApprovalDecisionRequest(
                decision=ApprovalDecisionType.REJECT,
                comment="Changed my mind.",
            ),
            actor,
        )


@pytest.mark.asyncio
async def test_non_waiting_status_decision_is_rejected(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_service = WorkflowService(db_session)
    state = await workflow_service.create_workflow(build_workflow_state_create())
    service = ApprovalService(db_session)

    with pytest.raises(ApprovalInvalidStateError):
        await service.submit_approval_decision(
            UUID(state.workflow_id),
            ApprovalDecisionRequest(
                decision=ApprovalDecisionType.APPROVE,
                comment="Too early.",
            ),
            actor,
        )


@pytest.mark.asyncio
async def test_terminal_workflow_decision_is_rejected(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.MANAGER)
    workflow_id = await create_waiting_workflow(db_session)
    workflow_service = WorkflowService(db_session)
    await workflow_service.transition_workflow_status(
        workflow_id,
        WorkflowStatus.CANCELLED,
    )
    service = ApprovalService(db_session)

    with pytest.raises(ApprovalTerminalStateError):
        await service.submit_approval_decision(
            workflow_id,
            ApprovalDecisionRequest(
                decision=ApprovalDecisionType.APPROVE,
                comment="Too late.",
            ),
            actor,
        )


@pytest.mark.asyncio
async def test_unauthorized_role_is_rejected(
    db_session: AsyncSession,
) -> None:
    actor = await create_user_with_role(db_session, RoleName.VIEWER)
    workflow_id = await create_waiting_workflow(db_session)
    service = ApprovalService(db_session)

    with pytest.raises(ApprovalPermissionDeniedError):
        await service.submit_approval_decision(
            workflow_id,
            ApprovalDecisionRequest(
                decision=ApprovalDecisionType.APPROVE,
                comment="Viewer cannot approve.",
            ),
            actor,
        )

    events = await list_workflow_events(db_session, workflow_id)
    assert events == []


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
        email=f"{role_name.value.lower()}-approval-{uuid4()}@example.test",
        hashed_password=hash_password("not-used-in-approval-tests"),
        roles=[role],
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def ensure_role(session: AsyncSession, role_name: RoleName) -> Role:
    """Create or reuse an RBAC role."""
    role: Role | None = await get_role_by_name(session, role_name)
    if role is not None:
        return role

    try:
        async with session.begin_nested():
            role = Role(name=role_name.value, description=f"{role_name.value} role")
            session.add(role)
            await session.flush()
            return role
    except IntegrityError:
        role = await get_role_by_name(session, role_name)
        if role is not None:
            return role
        raise


async def get_role_by_name(session: AsyncSession, role_name: RoleName) -> Role | None:
    """Return an existing role by stable RBAC name."""
    result = await session.execute(select(Role).where(Role.name == role_name.value))
    return result.scalar_one_or_none()


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
