"""API tests for workflow runtime run endpoint."""

from collections.abc import AsyncIterator, Iterable
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password
from app.auth.rbac import RoleName
from app.config import Settings, get_settings
from app.core.dependencies import provide_db_session, provide_runtime_service
from app.db import create_database_engine, create_session_factory
from app.main import create_app
from app.models import AuditLog, Role, User, Workflow
from app.models.enums import WorkflowStatus
from app.runtime import (
    PRE_APPROVAL_RUNTIME_STAGES,
    RuntimeStage,
    RuntimeWorkflowResult,
    RuntimeWorkflowState,
)
from app.workflows import (
    WorkflowService,
    WorkflowState,
    WorkflowStateCreate,
    WorkflowType,
)

TEST_EMAIL_PREFIX = "workflow-api-run"
TEST_DOMAIN_PREFIX = "workflow-api-run-domain"
TEST_ROLE_DESCRIPTION = "Workflow API runtime run endpoint test role"


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a database session and clean committed runtime API test rows."""
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
    """Provide an HTTP client with the database dependency overridden."""
    app = create_app(Settings())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[provide_db_session] = override_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("role_name", [RoleName.ADMIN, RoleName.MANAGER])
async def test_allowed_roles_can_run_workflow_to_waiting_approval(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-success-{role_name.value}",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/run",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["workflow_id"] == workflow.workflow_id
    assert data["status"] == WorkflowStatus.WAITING_APPROVAL
    assert data["completed_stages"] == [
        stage.value for stage in PRE_APPROVAL_RUNTIME_STAGES
    ]
    assert data["waiting_for_approval"] is True
    assert data["completed"] is False
    assert data["failed"] is False
    assert data["message"] == "Workflow is waiting for approval."
    assert data["result"]["state"]["current_stage"] == "approval"
    assert data["result"]["state"]["status"] == WorkflowStatus.WAITING_APPROVAL
    assert "email_preparation" not in data["completed_stages"]
    assert_no_internal_fields(data)
    assert_no_internal_fields(data["result"]["state"])
    assert not db_session.in_transaction()

    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    assert persisted_workflow.status is WorkflowStatus.WAITING_APPROVAL
    assert persisted_workflow.state_payload["current_step"] == "approval"


@pytest.mark.asyncio
async def test_run_workflow_accepts_created_current_step_marker(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-created-current-step",
    )
    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    persisted_workflow.state_payload = {
        **persisted_workflow.state_payload,
        "current_step": "created",
    }
    await db_session.commit()

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/run",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == WorkflowStatus.WAITING_APPROVAL
    assert data["waiting_for_approval"] is True
    assert data["completed"] is False
    assert "email_preparation" not in data["completed_stages"]
    assert data["result"]["state"]["current_stage"] == RuntimeStage.APPROVAL.value


@pytest.mark.asyncio
async def test_run_workflow_rejects_unknown_current_step_safely(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-invalid-current-step",
    )
    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    persisted_workflow.state_payload = {
        **persisted_workflow.state_payload,
        "current_step": "unknown_runtime_stage",
    }
    await db_session.commit()

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/run",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "workflow_runtime_precondition_failed"
    assert data["detail"]["message"] == (
        "Workflow runtime could not start from persisted state"
    )
    assert "ValueError" not in str(data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [RoleName.SALES, RoleName.LEGAL, RoleName.FINANCE, RoleName.VIEWER],
)
async def test_non_runtime_roles_cannot_run_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-forbidden-{role_name.value}",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/run",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_run_workflow_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(f"/api/v1/workflows/{uuid4()}/run")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_workflow_returns_404_for_missing_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    missing_workflow_id = uuid4()

    response = await client.post(
        f"/api/v1/workflows/{missing_workflow_id}/run",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "workflow_not_found"


@pytest.mark.asyncio
async def test_run_workflow_rejects_non_created_workflow_without_commit(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-precondition",
    )
    workflow_service = WorkflowService(db_session)
    await workflow_service.transition_workflow_status(
        UUID(workflow.workflow_id),
        WorkflowStatus.PLANNING,
    )
    await db_session.commit()

    async def fail_commit() -> None:
        raise AssertionError("Run workflow route committed after runtime failure")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/run",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "workflow_runtime_precondition_failed"


@pytest.mark.asyncio
async def test_run_route_rejects_invalid_workflow_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])

    response = await client.post(
        "/api/v1/workflows/not-a-uuid/run",
        headers=auth_headers(user),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_run_route_commits_only_after_runtime_service_returns(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow_id = uuid4()
    call_order: list[str] = []
    runtime_service = FakeRuntimeService(call_order=call_order)

    async def record_commit() -> None:
        call_order.append("commit")

    monkeypatch.setattr(db_session, "commit", record_commit)

    async with runtime_client(db_session, runtime_service) as client:
        response = await client.post(
            f"/api/v1/workflows/{workflow_id}/run",
            headers=auth_headers(user),
        )

    assert response.status_code == 200
    assert call_order == ["run", "commit"]
    assert runtime_service.actor_type == "user"
    assert runtime_service.actor_id == user.id
    assert response.json()["workflow_id"] == str(workflow_id)


@pytest.mark.asyncio
async def test_run_route_does_not_commit_when_runtime_service_raises(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow_id = uuid4()
    call_order: list[str] = []
    runtime_service = FakeRuntimeService(
        call_order=call_order,
        error=RuntimeError("deterministic runtime failure"),
    )

    async def fail_commit() -> None:
        call_order.append("commit")
        raise AssertionError("Run workflow route committed after runtime exception")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    async with runtime_client(db_session, runtime_service) as client:
        with pytest.raises(RuntimeError, match="deterministic runtime failure"):
            await client.post(
                f"/api/v1/workflows/{workflow_id}/run",
                headers=auth_headers(user),
            )

    assert call_order == ["run"]


def test_run_route_remains_registered_with_resume_boundary_and_stream_route() -> None:
    app = create_app()
    route_paths = route_paths_for(app.routes)

    assert "/api/v1/workflows/{workflow_id}/run" in route_paths
    assert "/api/v1/workflows/{workflow_id}/resume" in route_paths
    assert "/api/v1/workflows/{workflow_id}/stream" in route_paths


class FakeRuntimeService:
    """Runtime service double for route transaction boundary tests."""

    def __init__(
        self,
        *,
        call_order: list[str],
        error: Exception | None = None,
    ) -> None:
        self.call_order = call_order
        self.error = error
        self.actor_type: str | None = None
        self.actor_id: UUID | None = None

    async def run_workflow(
        self,
        workflow_id: UUID,
        *,
        actor_type: str | None = None,
        actor_id: UUID | None = None,
    ) -> RuntimeWorkflowResult:
        self.call_order.append("run")
        self.actor_type = actor_type
        self.actor_id = actor_id
        if self.error is not None:
            raise self.error

        return RuntimeWorkflowResult(
            state=RuntimeWorkflowState(
                workflow_id=str(workflow_id),
                workflow_type=WorkflowType.PROCUREMENT_QUOTATION,
                domain=f"{TEST_DOMAIN_PREFIX}-fake-runtime",
                status=WorkflowStatus.WAITING_APPROVAL,
                request={},
                current_stage=RuntimeStage.APPROVAL,
                completed_stages=PRE_APPROVAL_RUNTIME_STAGES,
            ),
            completed=False,
            failed=False,
            message="Workflow is waiting for approval.",
        )


def runtime_client(
    session: AsyncSession,
    runtime_service: FakeRuntimeService,
) -> AsyncClient:
    """Return an API client with a runtime service dependency override."""
    app = create_app(Settings())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    def override_runtime_service() -> FakeRuntimeService:
        return runtime_service

    app.dependency_overrides[provide_db_session] = override_db_session
    app.dependency_overrides[provide_runtime_service] = override_runtime_service
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


async def create_user_with_roles(
    session: AsyncSession,
    *,
    role_names: list[RoleName],
) -> User:
    """Create and commit a user with the requested exact RBAC role names."""
    roles = [await ensure_role(session, role_name) for role_name in role_names]
    user = User(
        email=f"{TEST_EMAIL_PREFIX}-{uuid4()}@example.test",
        hashed_password=hash_password("not-used-in-runtime-api-tests"),
        full_name="Workflow Runtime API Test User",
        is_active=True,
        roles=roles,
    )
    session.add(user)
    await session.commit()
    return user


async def ensure_role(session: AsyncSession, role_name: RoleName) -> Role:
    """Return an existing role or create one for endpoint tests."""
    result = await session.scalar(select(Role).where(Role.name == role_name.value))
    if result is not None:
        return result

    role = Role(
        name=role_name.value,
        description=TEST_ROLE_DESCRIPTION,
    )
    session.add(role)
    await session.flush()
    return role


def auth_headers(user: User) -> dict[str, str]:
    """Return bearer token authorization headers for a user."""
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def workflow_create_payload(domain: str) -> dict[str, object]:
    """Return a valid workflow creation request payload."""
    return {
        "workflow_type": "procurement_quotation",
        "domain": domain,
        "request": {
            "raw_text": "Need 50 business laptops.",
            "source": "manual_text",
            "uploaded_document_ids": [],
        },
    }


async def create_workflow_directly(
    session: AsyncSession,
    *,
    domain: str,
) -> WorkflowState:
    """Create and commit a workflow through the service for endpoint tests."""
    service = WorkflowService(session)
    workflow = await service.create_workflow(
        WorkflowStateCreate.model_validate(workflow_create_payload(domain)),
    )
    await session.commit()
    return workflow


def assert_no_internal_fields(payload: dict[str, Any]) -> None:
    """Assert API responses expose schema fields, not ORM internals."""
    internal_fields = {
        "id",
        "_sa_instance_state",
        "deleted_at",
        "created_by_id",
        "request_payload",
        "state_payload",
        "workflow",
    }

    assert internal_fields.isdisjoint(payload)


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
    """Remove rows committed by runtime API endpoint tests."""
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
        delete(Workflow).where(Workflow.domain.like(f"{TEST_DOMAIN_PREFIX}%")),
    )
    await session.execute(delete(User).where(User.email.like(f"{TEST_EMAIL_PREFIX}-%")))
    await session.execute(delete(Role).where(Role.description == TEST_ROLE_DESCRIPTION))
    await session.commit()
