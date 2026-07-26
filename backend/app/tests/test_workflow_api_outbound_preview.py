"""API tests for approved outbound communication preview endpoint."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.approvals.schemas import ApprovalDecisionType, ApprovalRecord
from app.auth import create_access_token, hash_password
from app.auth.rbac import RoleName
from app.config import Settings, get_settings
from app.core.dependencies import provide_db_session, provide_settings
from app.db import create_database_engine, create_session_factory
from app.main import create_app
from app.models import AuditLog, Role, User, Workflow, WorkflowEvent
from app.models.enums import WorkflowStatus

TEST_EMAIL_PREFIX = "workflow-api-outbound-preview"
TEST_DOMAIN_PREFIX = "workflow-api-outbound-preview-domain"
TEST_ROLE_DESCRIPTION = "Workflow API outbound preview endpoint test role"


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a database session and clean committed outbound preview test rows."""
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await cleanup_test_records(session)
    finally:
        await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Provide an API client with enabled outbound preview settings."""
    async with outbound_preview_client(db_session, outbound_enabled=True) as client:
        yield client


@pytest.mark.asyncio
async def test_outbound_preview_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/workflows/{uuid4()}/outbound/preview")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("role_name", [RoleName.ADMIN, RoleName.MANAGER])
async def test_admin_and_manager_can_read_completed_outbound_preview(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_completed_workflow_with_preview(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-allowed-{role_name.value}",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.id}/outbound/preview",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["workflow_id"] == str(workflow.id)
    assert data["channel"] == "email_preview"
    assert data["provider"] == "preview"
    assert data["subject"] == "Approved customer communication preview"
    assert data["body"] == "Dear customer, this preview is ready for manual review."
    assert data["source"] == "email_preview"
    assert data["approval_status"] == "approved_and_resumed"
    assert data["workflow_status"] == WorkflowStatus.COMPLETED
    assert data["is_sendable"] is False
    assert data["is_sent"] is False
    assert data["requires_human_approval"] is False
    assert data["communication_label"] == "approved_outbound_preview"
    assert data["recipients"] == [
        {
            "name": "Demo Customer",
            "email": "customer@example.test",
            "role": "buyer",
        },
    ]
    assert "Preview only; no outbound message was sent." in data["warnings"]
    assert "email sent" not in str(data).lower()
    assert "gmail" not in str(data).lower()
    assert "smtp" not in str(data).lower()
    assert "raw_prompt" not in str(data).lower()


@pytest.mark.asyncio
async def test_viewer_cannot_read_outbound_preview(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])
    workflow = await create_completed_workflow_with_preview(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-viewer-forbidden",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.id}/outbound/preview",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_outbound_preview_returns_404_for_missing_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])

    response = await client.get(
        f"/api/v1/workflows/{uuid4()}/outbound/preview",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "workflow_not_found"


@pytest.mark.asyncio
async def test_outbound_preview_disabled_returns_safe_conflict(
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_completed_workflow_with_preview(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-disabled",
    )

    async with outbound_preview_client(
        db_session,
        outbound_enabled=False,
    ) as disabled_client:
        response = await disabled_client.get(
            f"/api/v1/workflows/{workflow.id}/outbound/preview",
            headers=auth_headers(user),
        )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "outbound_preview_disabled"
    assert "disabled" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_outbound_preview_rejects_non_completed_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_completed_workflow_with_preview(
        db_session,
        status=WorkflowStatus.WAITING_APPROVAL,
        domain=f"{TEST_DOMAIN_PREFIX}-waiting",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.id}/outbound/preview",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "outbound_preview_not_allowed"
    assert "completed workflow" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_outbound_preview_rejects_approved_but_not_resumed_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow_id = uuid4()
    workflow = await create_workflow(
        db_session,
        workflow_id=workflow_id,
        status=WorkflowStatus.APPROVED,
        domain=f"{TEST_DOMAIN_PREFIX}-approved-not-resumed",
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "email_preview": preview_payload(),
        },
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.id}/outbound/preview",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "outbound_preview_not_allowed"


@pytest.mark.asyncio
async def test_outbound_preview_rejects_no_explicit_preview_source(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow_id = uuid4()
    workflow = await create_workflow(
        db_session,
        workflow_id=workflow_id,
        status=WorkflowStatus.COMPLETED,
        domain=f"{TEST_DOMAIN_PREFIX}-no-source",
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "runtime_context": {"resume_state": {"resumed": True}},
            "outputs": {
                "stage_outputs": {
                    "email_preparation": {
                        "status": "completed",
                        "summary": "Email preview stage completed.",
                    },
                },
            },
        },
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.id}/outbound/preview",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "outbound_preview_unavailable"
    assert "No explicit outbound preview source" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_outbound_preview_does_not_mutate_workflow_or_events(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_completed_workflow_with_preview(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-no-mutation",
    )
    original_state_payload = dict(workflow.state_payload)
    original_event_count = await event_count(db_session, workflow.id)

    response = await client.get(
        f"/api/v1/workflows/{workflow.id}/outbound/preview",
        headers=auth_headers(user),
    )
    await db_session.refresh(workflow)

    assert response.status_code == 200
    assert workflow.state_payload == original_state_payload
    assert await event_count(db_session, workflow.id) == original_event_count


@pytest.mark.asyncio
async def test_outbound_send_endpoint_does_not_exist(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow = await create_completed_workflow_with_preview(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-no-send-route",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.id}/outbound/send",
        headers=auth_headers(user),
    )

    assert response.status_code in {404, 405}


def test_outbound_preview_route_registered_without_send_route() -> None:
    route_paths = route_paths_for(create_app().routes)

    assert "/api/v1/workflows/{workflow_id}/outbound/preview" in route_paths
    assert "/api/v1/workflows/{workflow_id}/outbound/send" not in route_paths


def outbound_preview_client(
    session: AsyncSession,
    *,
    outbound_enabled: bool,
) -> AsyncClient:
    """Return an API client with database and settings dependency overrides."""
    app = create_app(Settings())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    def override_settings() -> Settings:
        settings = Settings()
        settings.outbound_communication_enabled = outbound_enabled
        settings.outbound_send_enabled = False
        settings.outbound_provider = "preview"
        settings.outbound_require_approval = True
        return settings

    app.dependency_overrides[provide_db_session] = override_db_session
    app.dependency_overrides[provide_settings] = override_settings
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


async def create_user_with_roles(
    session: AsyncSession,
    *,
    role_names: list[RoleName],
) -> User:
    """Create and commit a user with the requested RBAC role names."""
    roles = [await ensure_role(session, role_name) for role_name in role_names]
    user = User(
        email=f"{TEST_EMAIL_PREFIX}-{uuid4()}@example.test",
        hashed_password=hash_password("not-used-in-outbound-preview-tests"),
        full_name="Workflow Outbound Preview API Test User",
        is_active=True,
        roles=roles,
    )
    session.add(user)
    await session.commit()
    return user


async def ensure_role(session: AsyncSession, role_name: RoleName) -> Role:
    """Return an existing role or create one for endpoint tests."""
    role = await session.scalar(select(Role).where(Role.name == role_name.value))
    if role is not None:
        return role

    role = Role(name=role_name.value, description=TEST_ROLE_DESCRIPTION)
    session.add(role)
    await session.flush()
    return role


def auth_headers(user: User) -> dict[str, str]:
    """Return bearer token authorization headers for a user."""
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


async def create_completed_workflow_with_preview(
    session: AsyncSession,
    *,
    domain: str,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
) -> Workflow:
    workflow_id = uuid4()
    return await create_workflow(
        session,
        workflow_id=workflow_id,
        status=status,
        domain=domain,
        state_payload=completed_approved_state(workflow_id),
    )


async def create_workflow(
    session: AsyncSession,
    *,
    workflow_id: UUID,
    status: WorkflowStatus,
    domain: str,
    state_payload: dict[str, object],
) -> Workflow:
    """Create and commit a workflow row for outbound preview endpoint tests."""
    workflow = Workflow(
        id=workflow_id,
        workflow_type="procurement_quotation",
        domain=domain,
        status=status,
        request_payload={"raw_text": "Need approved communication preview."},
        state_payload=state_payload,
    )
    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return workflow


def completed_approved_state(workflow_id: UUID) -> dict[str, object]:
    """Return completed state with explicit approval, resume, and preview data."""
    return {
        "approval": {
            "approval_history": [_approval_record(workflow_id=workflow_id)],
        },
        "runtime_context": {
            "resume_state": {
                "resumed": True,
                "completed_stages": ["email_preparation"],
            },
        },
        "email_preview": preview_payload(),
    }


def preview_payload() -> dict[str, object]:
    """Return explicit preview content accepted by the outbound service."""
    return {
        "subject": "Approved customer communication preview",
        "body": "Dear customer, this preview is ready for manual review.",
        "recipients": [
            {
                "name": "Demo Customer",
                "email": "customer@example.test",
                "role": "buyer",
            },
        ],
    }


def _approval_record(workflow_id: UUID) -> dict[str, object]:
    return ApprovalRecord(
        decision_id=uuid4(),
        workflow_id=workflow_id,
        decision=ApprovalDecisionType.APPROVE,
        actor_id=uuid4(),
        actor_email="manager@example.test",
        actor_roles=("Manager",),
        comment="Approved for outbound preview.",
        decided_at=datetime(2026, 7, 26, 12, 0, tzinfo=UTC),
        previous_status=WorkflowStatus.WAITING_APPROVAL,
        next_status=WorkflowStatus.APPROVED,
    ).model_dump(mode="json")


async def event_count(session: AsyncSession, workflow_id: UUID) -> int:
    """Return persisted event count for one workflow."""
    result = await session.scalar(
        select(func.count())
        .select_from(WorkflowEvent)
        .where(
            WorkflowEvent.workflow_id == workflow_id,
        ),
    )
    return int(result or 0)


def route_paths_for(routes: Iterable[object]) -> set[str]:
    """Return route paths including nested router paths."""
    paths: set[str] = set()
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)

        nested_prefix = ""
        include_context = getattr(route, "include_context", None)
        if include_context is not None:
            context_prefix = getattr(include_context, "prefix", "")
            if isinstance(context_prefix, str):
                nested_prefix = context_prefix

        nested_router = getattr(route, "original_router", route)
        nested_routes = getattr(nested_router, "routes", None)
        if isinstance(nested_routes, Iterable):
            paths.update(
                f"{nested_prefix}{nested_path}"
                for nested_path in route_paths_for(nested_routes)
            )

    return paths


async def cleanup_test_records(session: AsyncSession) -> None:
    """Remove rows committed by outbound preview API endpoint tests."""
    if session.in_transaction():
        await session.rollback()

    workflow_ids = select(Workflow.id).where(
        Workflow.domain.like(f"{TEST_DOMAIN_PREFIX}%"),
    )
    test_user_ids = select(User.id).where(User.email.like(f"{TEST_EMAIL_PREFIX}-%"))

    await session.execute(
        delete(AuditLog).where(AuditLog.workflow_id.in_(workflow_ids)),
    )
    await session.execute(delete(AuditLog).where(AuditLog.actor_id.in_(test_user_ids)))
    await session.execute(
        delete(WorkflowEvent).where(WorkflowEvent.workflow_id.in_(workflow_ids)),
    )
    await session.execute(
        delete(Workflow).where(Workflow.domain.like(f"{TEST_DOMAIN_PREFIX}%")),
    )
    await session.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}-%")))
    await session.execute(delete(Role).where(Role.description == TEST_ROLE_DESCRIPTION))
    await session.commit()
