"""Workflow API router foundation tests."""

from collections.abc import Iterable
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import auth_router, health_router, workflows_router
from app.api.v1.workflows import (
    WORKFLOW_CREATE_ROLES,
    WORKFLOW_FULL_ACCESS_ROLES,
    WORKFLOW_PLANNED_ENDPOINTS,
    WORKFLOW_READ_ROLES,
    WorkflowRouterMetadata,
    require_workflow_create_access,
    require_workflow_full_access,
    require_workflow_read_access,
    router,
)
from app.auth.rbac import RoleName
from app.core.dependencies import (
    provide_runtime_service,
    provide_workflow_event_service,
    provide_workflow_service,
)
from app.main import create_app
from app.runtime import RuntimeService
from app.workflows.events import WorkflowEventService
from app.workflows.service import WorkflowService


def test_workflow_router_imports_with_prefix_and_tag() -> None:
    assert router is workflows_router
    assert router.prefix == "/workflows"
    assert "workflows" in router.tags


def test_api_v1_exports_existing_and_workflow_routers() -> None:
    assert health_router.prefix == ""
    assert auth_router.prefix == "/auth"
    assert workflows_router.prefix == "/workflows"


def test_create_app_registers_workflow_router_under_api_v1() -> None:
    app = create_app()
    route_paths = _route_paths(app.routes)

    assert "/api/v1/workflows/_meta" in route_paths

    openapi = app.openapi()
    workflow_meta = openapi["paths"]["/api/v1/workflows/_meta"]["get"]
    assert workflow_meta["tags"] == ["workflows"]
    assert workflow_meta["summary"] == "Workflow API router metadata"


def test_create_app_registers_completed_spec_007_workflow_routes() -> None:
    app = create_app()
    route_paths = _route_paths(app.routes)

    expected_paths = {
        "/api/v1/workflows",
        "/api/v1/workflows/{workflow_id}",
        "/api/v1/workflows/{workflow_id}/transition",
        "/api/v1/workflows/{workflow_id}/state",
        "/api/v1/workflows/{workflow_id}/events",
        "/api/v1/workflows/{workflow_id}/run",
        "/api/v1/workflows/_meta",
    }

    assert expected_paths.issubset(route_paths)


def test_workflow_openapi_metadata_for_completed_spec_007_routes() -> None:
    app = create_app()
    openapi_paths = app.openapi()["paths"]

    expected_operations = {
        ("/api/v1/workflows", "post", "Create workflow"),
        ("/api/v1/workflows", "get", "List workflows"),
        ("/api/v1/workflows/{workflow_id}", "get", "Get workflow"),
        (
            "/api/v1/workflows/{workflow_id}/transition",
            "post",
            "Transition workflow status",
        ),
        ("/api/v1/workflows/{workflow_id}/state", "patch", "Update workflow state"),
        ("/api/v1/workflows/{workflow_id}/events", "get", "List workflow events"),
        ("/api/v1/workflows/{workflow_id}/run", "post", "Run workflow"),
    }

    for path, method, summary in expected_operations:
        operation = openapi_paths[path][method]
        assert operation["tags"] == ["workflows"]
        assert operation["summary"] == summary


def test_deferred_workflow_operation_routes_are_not_registered_yet() -> None:
    app = create_app()
    route_paths = _route_paths(app.routes)

    deferred_paths = {
        "/api/v1/workflows/{workflow_id}/resume",
        "/api/v1/workflows/{workflow_id}/stream",
    }

    assert route_paths.isdisjoint(deferred_paths)


def test_workflow_service_dependency_providers_return_services() -> None:
    session = cast(AsyncSession, object())

    assert isinstance(provide_workflow_service(session), WorkflowService)
    assert isinstance(
        provide_workflow_event_service(session),
        WorkflowEventService,
    )
    assert isinstance(
        provide_runtime_service(
            provide_workflow_service(session),
            provide_workflow_event_service(session),
        ),
        RuntimeService,
    )


def test_workflow_rbac_role_sets_match_spec_baseline() -> None:
    assert WORKFLOW_FULL_ACCESS_ROLES == (
        RoleName.ADMIN,
        RoleName.MANAGER,
    )
    assert WORKFLOW_CREATE_ROLES == (
        RoleName.ADMIN,
        RoleName.MANAGER,
        RoleName.SALES,
    )
    assert WORKFLOW_READ_ROLES == (
        RoleName.ADMIN,
        RoleName.MANAGER,
        RoleName.SALES,
        RoleName.LEGAL,
        RoleName.FINANCE,
        RoleName.VIEWER,
    )


def test_workflow_rbac_dependency_helpers_are_callable() -> None:
    assert callable(require_workflow_full_access())
    assert callable(require_workflow_create_access())
    assert callable(require_workflow_read_access())


def test_workflow_router_metadata_schema_is_static_and_typed() -> None:
    metadata = WorkflowRouterMetadata(
        name="workflow-api",
        status="implemented",
        planned_endpoints=WORKFLOW_PLANNED_ENDPOINTS,
    )

    assert metadata.name == "workflow-api"
    assert metadata.status == "implemented"
    assert metadata.planned_endpoints == WORKFLOW_PLANNED_ENDPOINTS


def _route_paths(routes: Iterable[object]) -> set[str]:
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
                for nested_path in _route_paths(nested_routes)
            )

    return paths
