"""Tests for in-process metrics collection and metrics API."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.rbac import RoleName
from app.config import Settings
from app.core.metrics import InProcessMetrics, normalize_path_label
from app.main import create_app
from app.models import Role, User


def test_metrics_collector_records_bounded_http_request_labels() -> None:
    metrics = InProcessMetrics(max_path_label_length=40)

    metrics.record_http_request(
        method="get",
        path="/api/v1/workflows/12345678-1234-1234-1234-123456789abc",
        status_code=200,
        duration_ms=12.5,
    )
    metrics.record_http_request(
        method="GET",
        path="/api/v1/workflows/12345678-1234-1234-1234-123456789abc",
        status_code=204,
        duration_ms=8.0,
    )
    snapshot = metrics.snapshot()

    assert snapshot.counters["http_requests_total"] == 2
    assert snapshot.counters["http_requests_2xx_total"] == 2
    assert len(snapshot.request_metrics) == 1
    request_summary = snapshot.request_metrics[0]
    assert request_summary.method == "GET"
    assert request_summary.path == "/api/v1/workflows/{id}"
    assert request_summary.status_class == "2xx"
    assert request_summary.count == 2
    assert request_summary.duration_ms_min == 8.0
    assert request_summary.duration_ms_max == 12.5
    assert request_summary.duration_ms_avg == 10.25


def test_metrics_collector_can_be_disabled() -> None:
    metrics = InProcessMetrics(enabled=False)

    metrics.record_http_request(
        method="GET",
        path="/health",
        status_code=200,
        duration_ms=1.0,
    )

    assert metrics.snapshot().counters == {}
    assert metrics.snapshot().request_metrics == ()


def test_normalize_path_label_removes_high_cardinality_segments() -> None:
    path = "/api/v1/workflows/12345678-1234-1234-1234-123456789abc/events/999"

    assert normalize_path_label(path) == "/api/v1/workflows/{id}/events/{id}"


def test_metrics_endpoint_requires_authentication() -> None:
    client = TestClient(create_app(Settings()))

    response = client.get("/api/v1/observability/metrics")

    assert response.status_code == 401


def test_metrics_endpoint_allows_admin_and_manager_roles() -> None:
    for role_name in (RoleName.ADMIN, RoleName.MANAGER):
        client = metrics_client(role_name)
        client.get("/health")

        response = client.get("/api/v1/observability/metrics")
        data = response.json()

        assert response.status_code == 200
        assert data["uptime_seconds"] >= 0
        assert data["process_start_time"]
        assert data["counters"]["http_requests_total"] >= 1
        assert data["request_metrics"]
        assert "authorization" not in str(data).lower()
        assert "token" not in str(data).lower()


def test_metrics_endpoint_forbids_viewer_role() -> None:
    client = metrics_client(RoleName.VIEWER)

    response = client.get("/api/v1/observability/metrics")

    assert response.status_code == 403


def test_metrics_endpoint_can_be_disabled_by_settings() -> None:
    app = create_app(Settings(METRICS_ROUTE_ENABLED=False))
    route_paths = route_paths_for(app.routes)

    assert "/api/v1/observability/metrics" not in route_paths


def test_create_app_registers_observability_metrics_route() -> None:
    route_paths = route_paths_for(create_app().routes)

    assert "/api/v1/observability/metrics" in route_paths


def metrics_client(role_name: RoleName) -> TestClient:
    """Return a test client with an authenticated user override."""
    app = create_app(Settings())

    async def override_current_user() -> User:
        return User(
            email=f"{role_name.value.lower()}@example.test",
            hashed_password="not-used",
            full_name="Metrics Test User",
            is_active=True,
            roles=[Role(name=role_name.value, description="Metrics test role")],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    return TestClient(app)


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
