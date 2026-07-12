"""WebSocket tests for workflow event streaming."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from app.api.v1 import workflows as workflow_routes
from app.core.dependencies import (
    provide_db_session,
    provide_workflow_event_service,
    provide_workflow_event_subscriber,
)
from app.main import create_app
from app.models import User
from app.models.enums import WorkflowEventStatus
from app.streaming import WorkflowEventStreamMessage
from app.workflows.exceptions import WorkflowNotFoundError
from app.workflows.schemas import WorkflowEventRead


class FakeWorkflowEventService:
    """Workflow event service test double for WebSocket route tests."""

    def __init__(
        self,
        events: list[WorkflowEventRead],
        *,
        missing: bool = False,
    ) -> None:
        self.events = events
        self.missing = missing
        self.calls: list[tuple[UUID, int, int]] = []

    async def list_events_for_workflow(
        self,
        workflow_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WorkflowEventRead]:
        self.calls.append((workflow_id, limit, offset))
        if self.missing:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} was not found")
        return self.events[offset : offset + limit]


class FakeWorkflowEventSubscriber:
    """Finite workflow event subscriber test double."""

    def __init__(self, messages: list[WorkflowEventStreamMessage]) -> None:
        self.messages = messages
        self.subscribed_workflow_ids: list[UUID] = []

    async def subscribe_workflow_events(
        self,
        workflow_id: UUID | str,
    ) -> AsyncIterator[WorkflowEventStreamMessage]:
        self.subscribed_workflow_ids.append(UUID(str(workflow_id)))
        for message in self.messages:
            yield message


def test_workflow_stream_sends_bounded_backlog_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_id = uuid4()
    backlog_event = workflow_event_read(
        workflow_id=workflow_id,
        event_type="workflow.runtime.started",
        payload={"stage": "planner", "secret": "do-not-send"},
    )
    event_service = FakeWorkflowEventService([backlog_event])
    subscriber = FakeWorkflowEventSubscriber([])
    app = create_stream_test_app(event_service, subscriber, monkeypatch=monkeypatch)

    with (
        TestClient(app) as client,
        client.websocket_connect(f"/api/v1/workflows/{workflow_id}/stream") as ws,
    ):
        message = ws.receive_json()

    assert event_service.calls == [
        (workflow_id, workflow_routes.WORKFLOW_STREAM_BACKLOG_LIMIT, 0),
    ]
    assert subscriber.subscribed_workflow_ids == [workflow_id]
    assert message["type"] == "workflow.event"
    assert message["workflow_id"] == str(workflow_id)
    assert message["event_id"] == str(backlog_event.event_id)
    assert message["event_type"] == "workflow.runtime.started"
    assert message["stage"] == "planner"
    assert message["payload"] == {"stage": "planner"}
    assert_internal_fields_absent(message)


def test_workflow_stream_forwards_live_subscriber_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_id = uuid4()
    backlog_event = workflow_event_read(
        workflow_id=workflow_id,
        event_type="workflow.node.started",
        payload={"stage": "planner"},
    )
    live_message = stream_message(
        workflow_id=workflow_id,
        event_type="workflow.node.completed",
        payload={"stage": "planner"},
    )
    event_service = FakeWorkflowEventService([backlog_event])
    subscriber = FakeWorkflowEventSubscriber([live_message])
    app = create_stream_test_app(event_service, subscriber, monkeypatch=monkeypatch)

    with (
        TestClient(app) as client,
        client.websocket_connect(f"/api/v1/workflows/{workflow_id}/stream") as ws,
    ):
        backlog_payload = ws.receive_json()
        live_payload = ws.receive_json()

    assert backlog_payload["event_type"] == "workflow.node.started"
    assert live_payload["event_type"] == "workflow.node.completed"
    assert live_payload["event_id"] == str(live_message.event_id)
    assert live_payload["payload"] == {"stage": "planner"}
    assert_internal_fields_absent(live_payload)


def test_workflow_stream_rejects_missing_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow_id = uuid4()
    event_service = FakeWorkflowEventService([], missing=True)
    subscriber = FakeWorkflowEventSubscriber([])
    app = create_stream_test_app(event_service, subscriber, monkeypatch=monkeypatch)

    with (
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect) as error,
        client.websocket_connect(f"/api/v1/workflows/{workflow_id}/stream"),
    ):
        pass

    assert error.value.code == workflow_routes.WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE
    assert subscriber.subscribed_workflow_ids == []


def test_workflow_stream_rejects_unauthenticated_connection() -> None:
    workflow_id = uuid4()
    event_service = FakeWorkflowEventService([])
    subscriber = FakeWorkflowEventSubscriber([])
    app = create_stream_test_app(event_service, subscriber)

    with (
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect) as error,
        client.websocket_connect(f"/api/v1/workflows/{workflow_id}/stream"),
    ):
        pass

    assert error.value.code == workflow_routes.WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE
    assert event_service.calls == []
    assert subscriber.subscribed_workflow_ids == []


def test_resume_and_sse_stream_routes_remain_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_service = FakeWorkflowEventService([])
    subscriber = FakeWorkflowEventSubscriber([])
    app = create_stream_test_app(event_service, subscriber, monkeypatch=monkeypatch)
    route_paths = route_paths_for(app.routes)

    assert "/api/v1/workflows/{workflow_id}/stream" in route_paths
    assert "/api/v1/workflows/{workflow_id}/resume" not in route_paths
    assert "/api/v1/workflows/{workflow_id}/stream/sse" not in route_paths


def create_stream_test_app(
    event_service: FakeWorkflowEventService,
    subscriber: FakeWorkflowEventSubscriber,
    *,
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> FastAPI:
    """Create a FastAPI app with stream dependencies replaced by fakes."""
    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield cast(AsyncSession, object())

    def override_event_service() -> FakeWorkflowEventService:
        return event_service

    def override_subscriber() -> FakeWorkflowEventSubscriber:
        return subscriber

    app.dependency_overrides[provide_db_session] = override_db_session
    app.dependency_overrides[provide_workflow_event_service] = override_event_service
    app.dependency_overrides[provide_workflow_event_subscriber] = override_subscriber

    if monkeypatch is not None:

        async def allow_stream_access(
            _websocket: object,
            _session: object,
        ) -> User:
            return cast(User, object())

        monkeypatch.setattr(
            workflow_routes,
            "require_workflow_stream_access",
            allow_stream_access,
        )

    return app


def workflow_event_read(
    *,
    workflow_id: UUID,
    event_type: str,
    payload: dict[str, object],
) -> WorkflowEventRead:
    """Build a persisted workflow event read schema for route tests."""
    return WorkflowEventRead(
        workflow_id=workflow_id,
        event_id=uuid4(),
        event_type=event_type,
        agent_name="planner",
        status=WorkflowEventStatus.COMPLETED,
        message="Runtime event.",
        payload=payload,
        created_at=datetime.now(UTC),
    )


def stream_message(
    *,
    workflow_id: UUID,
    event_type: str,
    payload: dict[str, object],
) -> WorkflowEventStreamMessage:
    """Build a live stream message for route tests."""
    return WorkflowEventStreamMessage(
        workflow_id=workflow_id,
        event_id=uuid4(),
        event_type=event_type,
        status=WorkflowEventStatus.COMPLETED,
        stage=cast(str, payload.get("stage")),
        message="Runtime event.",
        created_at=datetime.now(UTC),
        payload=payload,
    )


def assert_internal_fields_absent(message: dict[str, object]) -> None:
    """Assert WebSocket stream messages do not expose ORM internals."""
    internal_fields = {
        "_sa_instance_state",
        "id",
        "workflow",
        "request_payload",
        "state_payload",
        "deleted_at",
    }
    assert internal_fields.isdisjoint(message)


def route_paths_for(routes: Iterable[object]) -> set[str]:
    """Return route paths including nested routers."""
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
