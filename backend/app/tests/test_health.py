"""Tests for health endpoints."""

from typing import Any

from fastapi.testclient import TestClient

from app.config import AppEnvironment, Settings
from app.core.dependencies import provide_readiness_checker
from app.main import create_app
from app.middleware import REQUEST_ID_HEADER
from app.schemas import ReadinessDependencyStatus, ReadinessDependencyStatusValue


def build_client() -> TestClient:
    settings = Settings()
    app = create_app(settings)
    app.dependency_overrides[provide_readiness_checker] = lambda: FakeReadinessChecker(
        [dependency_status("postgres_schema"), dependency_status("configuration")]
    )
    return TestClient(app)


def response_json(response: Any) -> dict[str, Any]:
    data = response.json()
    assert isinstance(data, dict)
    return data


def test_root_returns_service_information() -> None:
    client = build_client()

    response = client.get("/")
    data = response_json(response)

    assert response.status_code == 200
    assert data == {
        "app_name": "Multi-Agent OS",
        "environment": AppEnvironment.TESTING,
        "version": "0.2.0",
        "docs_url": "/docs",
        "health_url": "/health",
    }


def test_health_returns_ok_status() -> None:
    client = build_client()

    response = client.get("/health")
    data = response_json(response)

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["app_name"] == "Multi-Agent OS"
    assert data["environment"] == AppEnvironment.TESTING
    assert data["version"] == "0.2.0"
    assert isinstance(data["timestamp"], str)


class FakeReadinessChecker:
    """Readiness checker stub for health route tests."""

    def __init__(self, checks: list[ReadinessDependencyStatus]) -> None:
        self.checks = checks
        self.called = False

    async def check_all(self) -> list[ReadinessDependencyStatus]:
        self.called = True
        return self.checks


class FailingReadinessChecker:
    """Checker that fails if lightweight health routes call readiness checks."""

    async def check_all(self) -> list[ReadinessDependencyStatus]:
        raise AssertionError("readiness checker should not be called")


def dependency_status(
    name: str,
    status: ReadinessDependencyStatusValue = "ok",
) -> ReadinessDependencyStatus:
    return ReadinessDependencyStatus(
        name=name,
        status=status,
        required=True,
        latency_ms=1.0,
        message="ready" if status == "ok" else "dependency check failed",
    )


def test_ready_returns_dependency_readiness() -> None:
    app = create_app(Settings())
    checker = FakeReadinessChecker(
        [
            dependency_status("postgres"),
            dependency_status("redis"),
            dependency_status("configuration"),
        ],
    )
    app.dependency_overrides[provide_readiness_checker] = lambda: checker
    client = TestClient(app)

    response = client.get("/ready")
    data = response_json(response)

    assert response.status_code == 200
    assert data["status"] == "ready"
    assert isinstance(data["timestamp"], str)
    assert [check["name"] for check in data["checks"]] == [
        "postgres",
        "redis",
        "configuration",
    ]
    assert {check["status"] for check in data["checks"]} == {"ok"}
    assert checker.called is True


def test_ready_returns_503_when_dependency_fails() -> None:
    app = create_app(Settings())
    checker = FakeReadinessChecker(
        [
            dependency_status("postgres", "failed"),
            dependency_status("redis"),
            dependency_status("configuration"),
        ],
    )
    app.dependency_overrides[provide_readiness_checker] = lambda: checker
    client = TestClient(app)

    response = client.get("/ready")
    data = response_json(response)

    assert response.status_code == 503
    assert data["status"] == "not_ready"
    assert data["checks"][0]["name"] == "postgres"
    assert data["checks"][0]["status"] == "failed"


def test_live_does_not_call_readiness_checker() -> None:
    app = create_app(Settings())
    app.dependency_overrides[provide_readiness_checker] = FailingReadinessChecker
    client = TestClient(app)

    live_response = client.get("/live")

    assert live_response.status_code == 200


def test_live_returns_alive_status() -> None:
    client = build_client()

    response = client.get("/live")
    data = response_json(response)

    assert response.status_code == 200
    assert data["status"] == "alive"
    assert isinstance(data["timestamp"], str)


def test_health_response_includes_request_id_header() -> None:
    client = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]


def test_app_has_no_retired_product_routes() -> None:
    paths = build_client().get("/openapi.json").json()["paths"]
    retired = ("knowledge", "quotation", "outbound", "/state", "/transition")
    assert not any(any(word in path for word in retired) for path in paths)
    assert "/api/v1/runs" in paths


def test_health_aggregates_optional_notification_degradation() -> None:
    app = create_app(Settings())
    checker = FakeReadinessChecker(
        [
            dependency_status("postgres_schema"),
            ReadinessDependencyStatus(
                name="redis_notifications",
                status="failed",
                required=False,
                message="notification delivery degraded",
            ),
        ]
    )
    app.dependency_overrides[provide_readiness_checker] = lambda: checker
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"][1]["required"] is False
    assert client.get("/ready").status_code == 200
    assert checker.called


def test_health_required_storage_failure_is_unavailable() -> None:
    app = create_app(Settings())
    checker = FakeReadinessChecker([dependency_status("postgres_schema", "failed")])
    app.dependency_overrides[provide_readiness_checker] = lambda: checker
    response = TestClient(app).get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert checker.called
