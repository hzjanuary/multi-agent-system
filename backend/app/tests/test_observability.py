"""Tests for structured observability and redaction helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import pytest
import structlog
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.logging import configure_logging
from app.core.observability import (
    REDACTED_VALUE,
    redact_value,
    redacted_log_event,
)
from app.main import create_app


def test_redaction_masks_sensitive_keys_recursively() -> None:
    payload = {
        "authorization": "Bearer secret-token",
        "nested": {
            "api_key": "provider-key",
            "safe": "visible",
            "items": [{"password": "secret-password"}],
        },
        "embedding": [0.1, 0.2],
    }

    redacted = redact_value(payload)

    assert redacted["authorization"] == REDACTED_VALUE
    assert redacted["nested"]["api_key"] == REDACTED_VALUE
    assert redacted["nested"]["safe"] == "visible"
    assert redacted["nested"]["items"][0]["password"] == REDACTED_VALUE
    assert redacted["embedding"] == REDACTED_VALUE
    assert "secret-token" not in str(redacted)
    assert "provider-key" not in str(redacted)


def test_redaction_bounds_long_values_and_collections() -> None:
    payload = {
        "message": "x" * 700,
        "items": list(range(100)),
    }

    redacted = redact_value(payload, max_string_length=80, max_collection_items=5)

    assert len(redacted["message"]) == 80
    assert redacted["message"].endswith("[truncated]")
    assert redacted["items"] == [0, 1, 2, 3, 4]


def test_structured_log_processor_redacts_sensitive_event_fields() -> None:
    event = redacted_log_event(
        None,
        "info",
        {"event": "test", "jwt": "token-value", "path": "/health"},
    )

    assert event == {"event": "test", "jwt": REDACTED_VALUE, "path": "/health"}


def test_configure_logging_emits_json_with_redaction(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO", log_format="json", redaction_enabled=True)

    structlog.get_logger("observability-test").info(
        "structured_event",
        api_key="secret-value",
        request_id="request-123",
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["event"] == "structured_event"
    assert data["api_key"] == REDACTED_VALUE
    assert data["request_id"] == "request-123"
    assert data["level"] == "info"
    assert "timestamp" in data
    assert "secret-value" not in captured.out


def test_request_logging_includes_request_id_and_safe_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged_events: list[dict[str, Any]] = []

    def capture_log(event: str, **kwargs: Any) -> None:
        logged_events.append({"event": event, **kwargs})

    monkeypatch.setattr("app.middleware.logging.logger.info", capture_log)
    client = TestClient(create_app(Settings()))

    response = client.get(
        "/health?token=secret",
        headers={
            "X-Request-ID": "request-abc",
            "Authorization": "Bearer should-not-appear",
            "Cookie": "session=secret-cookie",
        },
    )

    assert response.status_code == 200
    assert logged_events
    event = logged_events[-1]
    assert event["event"] == "request_completed"
    assert event["request_id"] == "request-abc"
    assert event["method"] == "GET"
    assert event["path"] == "/health"
    assert event["status_code"] == 200
    assert "duration_ms" in event
    assert "should-not-appear" not in str(logged_events)
    assert "secret-cookie" not in str(logged_events)


def test_health_live_ready_routes_still_register() -> None:
    route_paths = route_paths_for(create_app().routes)

    assert "/health" in route_paths
    assert "/live" in route_paths
    assert "/ready" in route_paths


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
