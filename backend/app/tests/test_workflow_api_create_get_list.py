"""API tests for workflow create/get/list endpoints."""

from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password
from app.auth.rbac import RoleName
from app.config import Settings, get_settings
from app.core.dependencies import provide_db_session
from app.db import create_database_engine, create_session_factory
from app.main import create_app
from app.models import AuditLog, Role, User, Workflow
from app.models.enums import WorkflowEventStatus, WorkflowStatus
from app.workflows import (
    WORKFLOW_STATE_UPDATED_ACTION,
    WORKFLOW_STATUS_TRANSITIONED_ACTION,
    WorkflowEventCreate,
    WorkflowEventService,
    WorkflowService,
    WorkflowState,
    WorkflowStateCreate,
)

TEST_EMAIL_PREFIX = "workflow-api"
TEST_DOMAIN_PREFIX = "workflow-api-domain"
TEST_ROLE_DESCRIPTION = "Workflow API endpoint test role"
SPEC_007_WORKFLOW_ENDPOINTS = {
    "POST /api/v1/workflows",
    "GET /api/v1/workflows",
    "GET /api/v1/workflows/{workflow_id}",
    "POST /api/v1/workflows/{workflow_id}/transition",
    "PATCH /api/v1/workflows/{workflow_id}/state",
    "GET /api/v1/workflows/{workflow_id}/events",
    "POST /api/v1/workflows/{workflow_id}/run",
    "WS /api/v1/workflows/{workflow_id}/stream",
}


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a database session and clean committed workflow API test rows."""
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
async def test_sales_user_can_create_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.SALES])

    response = await client.post(
        "/api/v1/workflows",
        headers=auth_headers(user),
        json=workflow_create_payload(domain=f"{TEST_DOMAIN_PREFIX}-create"),
    )
    data = response.json()

    assert response.status_code == 201
    assert data["workflow"]["status"] == WorkflowStatus.CREATED
    assert data["workflow"]["workflow_type"] == "procurement_quotation"
    assert data["workflow"]["domain"] == f"{TEST_DOMAIN_PREFIX}-create"
    assert data["workflow"]["request"]["source"] == "manual_text"
    assert not db_session.in_transaction()

    persisted_workflow = await db_session.get(
        Workflow,
        UUID(data["workflow"]["workflow_id"]),
    )
    assert persisted_workflow is not None
    assert persisted_workflow.created_by_id == user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [RoleName.ADMIN, RoleName.MANAGER, RoleName.SALES],
)
async def test_allowed_create_roles_can_create_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])

    response = await client.post(
        "/api/v1/workflows",
        headers=auth_headers(user),
        json=workflow_create_payload(domain=f"{TEST_DOMAIN_PREFIX}-{role_name.value}"),
    )

    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [RoleName.LEGAL, RoleName.FINANCE, RoleName.VIEWER],
)
async def test_read_only_roles_cannot_create_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])

    response = await client.post(
        "/api/v1/workflows",
        headers=auth_headers(user),
        json=workflow_create_payload(domain=f"{TEST_DOMAIN_PREFIX}-forbidden"),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_workflow_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/workflows",
        json=workflow_create_payload(domain=f"{TEST_DOMAIN_PREFIX}-unauthorized"),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_workflow_rejects_invalid_payload(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.SALES])
    invalid_payload = workflow_create_payload(domain=f"{TEST_DOMAIN_PREFIX}-invalid")
    invalid_payload["workflow_type"] = "not_supported"

    response = await client.post(
        "/api/v1/workflows",
        headers=auth_headers(user),
        json=invalid_payload,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [
        RoleName.ADMIN,
        RoleName.MANAGER,
        RoleName.SALES,
        RoleName.LEGAL,
        RoleName.FINANCE,
        RoleName.VIEWER,
    ],
)
async def test_allowed_read_roles_can_get_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-get-{role_name.value}",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["workflow"]["workflow_id"] == workflow.workflow_id
    assert data["workflow"]["domain"] == workflow.domain


@pytest.mark.asyncio
async def test_user_without_workflow_read_role_cannot_get_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-get-forbidden",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_workflow_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/workflows/{uuid4()}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_workflow_returns_404_for_missing_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])
    missing_workflow_id = uuid4()

    response = await client.get(
        f"/api/v1/workflows/{missing_workflow_id}",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "workflow_not_found"


@pytest.mark.asyncio
async def test_get_workflow_rejects_invalid_workflow_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])

    response = await client.get(
        "/api/v1/workflows/not-a-uuid",
        headers=auth_headers(user),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_allowed_reader_can_list_workflows_with_pagination_and_status_filter(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.LEGAL])
    first = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-list-a",
    )
    second = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-list-b",
    )

    response = await client.get(
        "/api/v1/workflows",
        headers=auth_headers(user),
        params={"limit": 100, "offset": 0, "status": "CREATED"},
    )
    data = response.json()

    workflow_ids = {workflow["workflow_id"] for workflow in data["workflows"]}
    assert response.status_code == 200
    assert {first.workflow_id, second.workflow_id}.issubset(workflow_ids)
    assert data["count"] == len(data["workflows"])
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert data["status"] == "CREATED"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [
        RoleName.ADMIN,
        RoleName.MANAGER,
        RoleName.SALES,
        RoleName.LEGAL,
        RoleName.FINANCE,
        RoleName.VIEWER,
    ],
)
async def test_all_read_roles_can_list_workflows(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-list-role-{role_name.value}",
    )

    response = await client.get(
        "/api/v1/workflows",
        headers=auth_headers(user),
        params={"status": "CREATED"},
    )
    data = response.json()

    assert response.status_code == 200
    assert workflow.workflow_id in {
        listed_workflow["workflow_id"] for listed_workflow in data["workflows"]
    }


@pytest.mark.asyncio
async def test_user_without_workflow_read_role_cannot_list_workflows(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[])

    response = await client.get(
        "/api/v1/workflows",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_workflows_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/workflows")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_workflows_rejects_invalid_query_params(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])

    response = await client.get(
        "/api/v1/workflows",
        headers=auth_headers(user),
        params={"limit": 0},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_workflow_router_metadata_reports_implemented_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])

    response = await client.get(
        "/api/v1/workflows/_meta",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "workflow-api"
    assert data["status"] == "implemented"
    assert set(data["planned_endpoints"]) == SPEC_007_WORKFLOW_ENDPOINTS


@pytest.mark.asyncio
@pytest.mark.parametrize("role_name", [RoleName.ADMIN, RoleName.MANAGER])
async def test_allowed_transition_roles_can_transition_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-transition-{role_name.value}",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/transition",
        headers=auth_headers(user),
        json={"to_status": WorkflowStatus.PLANNING, "reason": "Begin planning"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["workflow"]["workflow_id"] == workflow.workflow_id
    assert data["workflow"]["status"] == WorkflowStatus.PLANNING
    assert not db_session.in_transaction()

    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    assert persisted_workflow.status is WorkflowStatus.PLANNING

    audit_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.workflow_id == UUID(workflow.workflow_id),
            AuditLog.action == WORKFLOW_STATUS_TRANSITIONED_ACTION,
        ),
    )
    assert audit_log is not None
    assert audit_log.actor_type == "user"
    assert audit_log.actor_id == user.id
    assert audit_log.payload["old_status"] == WorkflowStatus.CREATED
    assert audit_log.payload["new_status"] == WorkflowStatus.PLANNING
    assert audit_log.payload["reason"] == "Begin planning"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [RoleName.SALES, RoleName.LEGAL, RoleName.FINANCE, RoleName.VIEWER],
)
async def test_non_transition_roles_cannot_transition_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-transition-forbidden-{role_name.value}",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/transition",
        headers=auth_headers(user),
        json={"to_status": WorkflowStatus.PLANNING},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_transition_workflow_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.post(
        f"/api/v1/workflows/{uuid4()}/transition",
        json={"to_status": WorkflowStatus.PLANNING},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_transition_workflow_returns_404_for_missing_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    missing_workflow_id = uuid4()

    response = await client.post(
        f"/api/v1/workflows/{missing_workflow_id}/transition",
        headers=auth_headers(user),
        json={"to_status": WorkflowStatus.PLANNING},
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "workflow_not_found"


@pytest.mark.asyncio
async def test_transition_workflow_invalid_transition_returns_409_without_commit(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-transition-invalid",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/transition",
        headers=auth_headers(user),
        json={"to_status": WorkflowStatus.COMPLETED},
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["code"] == "invalid_workflow_transition"
    assert data["detail"]["details"]["from_status"] == WorkflowStatus.CREATED
    assert data["detail"]["details"]["to_status"] == WorkflowStatus.COMPLETED

    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    assert persisted_workflow.status is WorkflowStatus.CREATED

    transition_audit_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.workflow_id == UUID(workflow.workflow_id),
            AuditLog.action == WORKFLOW_STATUS_TRANSITIONED_ACTION,
        ),
    )
    assert transition_audit_log is None


@pytest.mark.asyncio
async def test_transition_workflow_rejects_invalid_payload(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-transition-invalid-payload",
    )

    response = await client.post(
        f"/api/v1/workflows/{workflow.workflow_id}/transition",
        headers=auth_headers(user),
        json={"to_status": "NOT_A_STATUS"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_transition_workflow_rejects_invalid_workflow_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])

    response = await client.post(
        "/api/v1/workflows/not-a-uuid/transition",
        headers=auth_headers(user),
        json={"to_status": WorkflowStatus.PLANNING},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("role_name", [RoleName.ADMIN, RoleName.MANAGER])
async def test_allowed_state_update_roles_can_update_workflow_state(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-update-{role_name.value}",
    )
    state_payload = workflow_state_update_payload(
        workflow,
        customer={"name": "Acme Manufacturing Group"},
        current_step="planner",
    )

    response = await client.patch(
        f"/api/v1/workflows/{workflow.workflow_id}/state",
        headers=auth_headers(user),
        json={"state": state_payload, "reason": "Captured customer details"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["workflow"]["workflow_id"] == workflow.workflow_id
    assert data["workflow"]["status"] == WorkflowStatus.CREATED
    assert data["workflow"]["customer"]["name"] == "Acme Manufacturing Group"
    assert data["workflow"]["current_step"] == "planner"
    assert not db_session.in_transaction()

    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    assert persisted_workflow.status is WorkflowStatus.CREATED
    persisted_payload = cast(dict[str, Any], persisted_workflow.state_payload)
    persisted_customer = cast(dict[str, Any], persisted_payload["customer"])
    assert persisted_customer["name"] == "Acme Manufacturing Group"
    assert persisted_payload["current_step"] == "planner"

    audit_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.workflow_id == UUID(workflow.workflow_id),
            AuditLog.action == WORKFLOW_STATE_UPDATED_ACTION,
        ),
    )
    assert audit_log is not None
    assert audit_log.actor_type == "user"
    assert audit_log.actor_id == user.id
    assert audit_log.payload["status"] == WorkflowStatus.CREATED
    assert audit_log.payload["reason"] == "Captured customer details"
    updated_fields = cast(list[str], audit_log.payload["updated_fields"])
    assert set(updated_fields).issuperset(
        {"customer", "current_step"},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [RoleName.SALES, RoleName.LEGAL, RoleName.FINANCE, RoleName.VIEWER],
)
async def test_non_state_update_roles_cannot_update_workflow_state(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-forbidden-{role_name.value}",
    )

    response = await client.patch(
        f"/api/v1/workflows/{workflow.workflow_id}/state",
        headers=auth_headers(user),
        json={"state": workflow_state_update_payload(workflow)},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_workflow_state_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        f"/api/v1/workflows/{uuid4()}/state",
        json={"state": {}},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_workflow_state_returns_404_for_missing_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-missing-template",
    )
    missing_workflow_id = uuid4()
    state_payload = workflow_state_update_payload(
        workflow,
        workflow_id=str(missing_workflow_id),
    )

    response = await client.patch(
        f"/api/v1/workflows/{missing_workflow_id}/state",
        headers=auth_headers(user),
        json={"state": state_payload},
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "workflow_not_found"


@pytest.mark.asyncio
async def test_update_workflow_state_id_mismatch_returns_400_without_commit(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-id-mismatch",
    )
    state_payload = workflow_state_update_payload(workflow, workflow_id=str(uuid4()))

    response = await client.patch(
        f"/api/v1/workflows/{workflow.workflow_id}/state",
        headers=auth_headers(user),
        json={"state": state_payload},
    )
    data = response.json()

    assert response.status_code == 400
    assert data["detail"]["code"] == "workflow_state_mismatch"

    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    assert persisted_workflow.state_payload["workflow_id"] == workflow.workflow_id

    state_audit_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.workflow_id == UUID(workflow.workflow_id),
            AuditLog.action == WORKFLOW_STATE_UPDATED_ACTION,
        ),
    )
    assert state_audit_log is None


@pytest.mark.asyncio
async def test_update_workflow_state_status_mismatch_returns_400_without_commit(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-status-mismatch",
    )
    state_payload = workflow_state_update_payload(
        workflow,
        status=WorkflowStatus.PLANNING.value,
    )

    response = await client.patch(
        f"/api/v1/workflows/{workflow.workflow_id}/state",
        headers=auth_headers(user),
        json={"state": state_payload},
    )
    data = response.json()

    assert response.status_code == 400
    assert data["detail"]["code"] == "workflow_state_mismatch"

    persisted_workflow = await db_session.get(Workflow, UUID(workflow.workflow_id))
    assert persisted_workflow is not None
    assert persisted_workflow.status is WorkflowStatus.CREATED

    state_audit_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.workflow_id == UUID(workflow.workflow_id),
            AuditLog.action == WORKFLOW_STATE_UPDATED_ACTION,
        ),
    )
    assert state_audit_log is None


@pytest.mark.asyncio
async def test_update_workflow_state_rejects_invalid_payload(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-invalid-payload",
    )
    state_payload = workflow_state_update_payload(workflow)
    state_payload["retry_count"] = -1

    response = await client.patch(
        f"/api/v1/workflows/{workflow.workflow_id}/state",
        headers=auth_headers(user),
        json={"state": state_payload},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_workflow_state_rejects_invalid_workflow_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.MANAGER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-state-invalid-id",
    )

    response = await client.patch(
        "/api/v1/workflows/not-a-uuid/state",
        headers=auth_headers(user),
        json={"state": workflow_state_update_payload(workflow)},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role_name",
    [
        RoleName.ADMIN,
        RoleName.MANAGER,
        RoleName.SALES,
        RoleName.LEGAL,
        RoleName.FINANCE,
        RoleName.VIEWER,
    ],
)
async def test_allowed_read_roles_can_list_workflow_events(
    client: AsyncClient,
    db_session: AsyncSession,
    role_name: RoleName,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[role_name])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-events-{role_name.value}",
    )
    await append_workflow_event_directly(
        db_session,
        workflow_id=UUID(workflow.workflow_id),
        event_type="workflow.created",
        sequence=1,
    )
    await append_workflow_event_directly(
        db_session,
        workflow_id=UUID(workflow.workflow_id),
        event_type="planner.started",
        sequence=2,
        agent_name="planner",
        status=WorkflowEventStatus.STARTED,
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}/events",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["count"] == 2
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert [event["event_type"] for event in data["events"]] == [
        "workflow.created",
        "planner.started",
    ]
    assert [event["payload"]["sequence"] for event in data["events"]] == [1, 2]
    assert data["events"][1]["agent_name"] == "planner"
    assert data["events"][1]["status"] == WorkflowEventStatus.STARTED


@pytest.mark.asyncio
async def test_list_workflow_events_returns_empty_list_for_workflow_without_events(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-events-empty",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}/events",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {
        "events": [],
        "count": 0,
        "limit": 100,
        "offset": 0,
    }


@pytest.mark.asyncio
async def test_list_workflow_events_supports_limit_and_offset(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.SALES])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-events-pagination",
    )
    for sequence in range(3):
        await append_workflow_event_directly(
            db_session,
            workflow_id=UUID(workflow.workflow_id),
            event_type=f"workflow.event.{sequence}",
            sequence=sequence,
        )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}/events",
        headers=auth_headers(user),
        params={"limit": 1, "offset": 1},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["count"] == 1
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert data["events"][0]["event_type"] == "workflow.event.1"
    assert data["events"][0]["payload"]["sequence"] == 1


@pytest.mark.asyncio
async def test_list_workflow_events_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get(f"/api/v1/workflows/{uuid4()}/events")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_without_workflow_read_role_cannot_list_workflow_events(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-events-forbidden",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}/events",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_workflow_events_returns_404_for_missing_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.LEGAL])
    missing_workflow_id = uuid4()

    response = await client.get(
        f"/api/v1/workflows/{missing_workflow_id}/events",
        headers=auth_headers(user),
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"]["code"] == "workflow_not_found"


@pytest.mark.asyncio
async def test_list_workflow_events_rejects_invalid_workflow_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])

    response = await client.get(
        "/api/v1/workflows/not-a-uuid/events",
        headers=auth_headers(user),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_workflow_events_rejects_invalid_query_params(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.FINANCE])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-events-invalid-query",
    )

    response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}/events",
        headers=auth_headers(user),
        params={"limit": 0},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_workflow_api_responses_do_not_expose_internal_orm_fields(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-schema-safety",
    )
    await append_workflow_event_directly(
        db_session,
        workflow_id=UUID(workflow.workflow_id),
        event_type="schema.checked",
        sequence=1,
    )

    workflow_response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}",
        headers=auth_headers(user),
    )
    workflow_payload = workflow_response.json()["workflow"]

    events_response = await client.get(
        f"/api/v1/workflows/{workflow.workflow_id}/events",
        headers=auth_headers(user),
    )
    event_payload = events_response.json()["events"][0]

    assert workflow_response.status_code == 200
    assert events_response.status_code == 200
    assert_no_internal_fields(workflow_payload)
    assert_no_internal_fields(event_payload)
    assert "workflow_id" in workflow_payload
    assert "event_id" in event_payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/workflows",
        "/api/v1/workflows/{workflow_id}",
        "/api/v1/workflows/{workflow_id}/events",
    ],
)
async def test_read_workflow_routes_do_not_commit(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])
    workflow = await create_workflow_directly(
        db_session,
        domain=f"{TEST_DOMAIN_PREFIX}-read-no-commit",
    )
    await append_workflow_event_directly(
        db_session,
        workflow_id=UUID(workflow.workflow_id),
        event_type="read.checked",
        sequence=1,
    )

    async def fail_commit() -> None:
        raise AssertionError("Read-only workflow API route attempted to commit")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    response = await client.get(
        path.format(workflow_id=workflow.workflow_id),
        headers=auth_headers(user),
    )

    assert response.status_code == 200


async def create_user_with_roles(
    session: AsyncSession,
    *,
    role_names: list[RoleName],
) -> User:
    """Create and commit a user with the requested exact RBAC role names."""
    roles = [await ensure_role(session, role_name) for role_name in role_names]
    user = User(
        email=f"{TEST_EMAIL_PREFIX}-{uuid4()}@example.test",
        hashed_password=hash_password("not-used-in-workflow-api-tests"),
        full_name="Workflow API Test User",
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
    """Create and commit a workflow through the service for read endpoint tests."""
    service = WorkflowService(session)
    workflow = await service.create_workflow(
        WorkflowStateCreate.model_validate(workflow_create_payload(domain)),
    )
    await session.commit()
    return workflow


async def append_workflow_event_directly(
    session: AsyncSession,
    *,
    workflow_id: UUID,
    event_type: str,
    sequence: int,
    agent_name: str | None = None,
    status: WorkflowEventStatus | None = WorkflowEventStatus.COMPLETED,
) -> None:
    """Append and commit one workflow event through the event service."""
    service = WorkflowEventService(session)
    await service.append_event(
        WorkflowEventCreate(
            workflow_id=workflow_id,
            event_type=event_type,
            agent_name=agent_name,
            status=status,
            payload={"sequence": sequence},
        ),
    )
    await session.commit()


def workflow_state_update_payload(
    workflow: WorkflowState,
    **overrides: object,
) -> dict[str, object]:
    """Return a JSON-compatible workflow state update payload."""
    payload = workflow.model_dump(mode="json")
    payload.update(overrides)
    return payload


def assert_no_internal_fields(payload: dict[str, object]) -> None:
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


async def cleanup_test_records(session: AsyncSession) -> None:
    """Remove rows committed by workflow API endpoint tests."""
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
