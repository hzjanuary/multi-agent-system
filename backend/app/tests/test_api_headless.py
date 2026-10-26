"""Headless HTTP/WS boundaries against a real isolated PostgreSQL schema."""

import asyncio
import os
import threading
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.websockets import WebSocketDisconnect

from app.api.v1 import workflows as routes
from app.auth import create_access_token
from app.composition import get_run_service
from app.core.dependencies import provide_db_session
from app.db import Base
from app.definitions import load_registry
from app.main import create_app
from app.models import Role, User
from app.runtime.service import Worker
from app.workflows.service import RunService

APIContext = tuple[FastAPI, AsyncClient, RunService, dict[str, UUID], dict[str, str]]


@pytest.fixture
async def api(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[APIContext]:
    url = os.getenv("MAOS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("explicit disposable PostgreSQL database not configured")
    schema = "maos_api_" + uuid4().hex
    admin = create_async_engine(url)
    async with admin.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": schema}},
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    users, tokens = {}, {}
    async with factory() as session, session.begin():
        roles = {
            name: Role(id=uuid4(), name=name)
            for name in ("admin", "operator", "viewer")
        }
        session.add_all(roles.values())
        await session.flush()
        for name in (*roles, "none"):
            user = User(
                id=uuid4(),
                email=name + "@example.invalid",
                hashed_password="test-only",
                is_active=True,
                is_superuser=False,
                roles=[roles[name]] if name in roles else [],
            )
            session.add(user)
            users[name] = user.id
            tokens[name] = create_access_token(str(user.id))
    registry = load_registry(["app.tests.runtime_extensions"])
    service = RunService(factory, registry, {})
    app = create_app()

    async def db() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[provide_db_session] = db
    app.dependency_overrides[get_run_service] = lambda: service
    monkeypatch.setattr(routes, "get_registry", lambda: registry)
    monkeypatch.setattr(routes, "get_run_service", lambda: service)
    monkeypatch.setattr(routes, "get_session_factory", lambda: factory)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield app, client, service, users, tokens
    await engine.dispose()
    async with admin.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    await admin.dispose()


def bearer(tokens: dict[str, str], role: str = "operator") -> dict[str, str]:
    return {"Authorization": "Bearer " + tokens[role]}


async def make_run(
    api: APIContext, workflow: str = "approval", key: str | None = None
) -> dict[str, Any]:
    _, client, _, _, tokens = api
    headers = bearer(tokens)
    if key:
        headers["Idempotency-Key"] = key
    response = await client.post(
        "/api/v1/runs",
        headers=headers,
        json={
            "workflow_id": workflow,
            "version": "1",
            "input": {"text": "real caller input"},
        },
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert isinstance(result, dict)
    return result


async def test_every_http_surface_requires_role_and_no_patch_bypass(
    api: APIContext,
) -> None:
    app, client, service, _, tokens = api
    run = await make_run(api)
    run_id = run["id"]
    await client.post(f"/api/v1/runs/{run_id}/start", headers=bearer(tokens))
    await Worker(service, None).tick()
    approval = (await service.approvals(UUID(run_id)))[0]
    read_paths = [
        "/agents",
        "/workflows",
        "/workflows/approval",
        "/runs",
        f"/runs/{run_id}",
        f"/runs/{run_id}/nodes",
        f"/runs/{run_id}/approvals",
        f"/runs/{run_id}/events",
    ]
    decision = {
        "decision": "approve",
        "expected_revision": (await service.get(UUID(run_id))).revision,
        "content_revision": approval.content_revision,
        "content_hash": approval.content_hash,
    }
    mutations = [
        ("/runs", {"workflow_id": "approval", "version": "1", "input": {"text": "x"}}),
        (f"/runs/{run_id}/start", {}),
        (f"/runs/{run_id}/resume", {}),
        (f"/runs/{run_id}/cancel", {}),
        (f"/runs/{run_id}/approvals/{approval.id}/decision", decision),
    ]
    for path in read_paths:
        assert (await client.get("/api/v1" + path)).status_code == 401
        assert (
            await client.get("/api/v1" + path, headers=bearer(tokens, "none"))
        ).status_code == 403
        for role in ("admin", "operator", "viewer"):
            assert (
                await client.get("/api/v1" + path, headers=bearer(tokens, role))
            ).status_code == 200
    for path, payload in mutations:
        assert (await client.post("/api/v1" + path, json=payload)).status_code == 401
        assert (
            await client.post(
                "/api/v1" + path, json=payload, headers=bearer(tokens, "viewer")
            )
        ).status_code == 403
    assert (await service.get(UUID(run_id))).status == "WAITING_APPROVAL"
    assert (
        await client.patch(
            f"/api/v1/runs/{run_id}",
            headers=bearer(tokens),
            json={"status": "COMPLETED"},
        )
    ).status_code == 405
    paths = app.openapi()["paths"]
    assert not any(
        "knowledge" in path or "state" in path or "quotation" in path for path in paths
    )


async def test_api_durable_job_idempotency_approval_and_explicit_resume(
    api: APIContext,
) -> None:
    _, client, service, _, tokens = api
    run = await make_run(api, key="create")
    assert (await make_run(api, key="create"))["id"] == run["id"]
    changed = await client.post(
        "/api/v1/runs",
        headers={**bearer(tokens), "Idempotency-Key": "create"},
        json={"workflow_id": "approval", "version": "1", "input": {"text": "changed"}},
    )
    assert changed.status_code == 409
    run_id = run["id"]
    start_headers = {**bearer(tokens), "Idempotency-Key": "start"}
    starts = await asyncio.gather(
        *(
            client.post(f"/api/v1/runs/{run_id}/start", headers=start_headers)
            for _ in range(2)
        )
    )
    assert [response.status_code for response in starts] == [202, 202]
    assert await service.nodes(UUID(run_id)) == []  # HTTP only enqueues work.
    second = await make_run(api)
    assert (
        await client.post(f"/api/v1/runs/{second['id']}/start", headers=start_headers)
    ).status_code == 409
    await Worker(service, None).tick()
    paused = (await client.get(f"/api/v1/runs/{run_id}", headers=bearer(tokens))).json()
    approval = (
        await client.get(f"/api/v1/runs/{run_id}/approvals", headers=bearer(tokens))
    ).json()[0]
    data = {
        "decision": "approve",
        "expected_revision": paused["revision"],
        "content_revision": approval["content_revision"],
        "content_hash": approval["content_hash"],
    }
    stale = await client.post(
        f"/api/v1/runs/{run_id}/approvals/{approval['id']}/decision",
        headers=bearer(tokens),
        json={**data, "content_hash": "0" * 64},
    )
    assert stale.status_code == 409
    decided = await client.post(
        f"/api/v1/runs/{run_id}/approvals/{approval['id']}/decision",
        headers=bearer(tokens, "admin"),
        json=data,
    )
    assert decided.status_code == 200 and decided.json()["status"] == "APPROVED"
    assert not await Worker(service, None).tick()
    assert len(await service.nodes(UUID(run_id))) == 2
    headers = {**bearer(tokens), "Idempotency-Key": "resume"}
    resumed = await client.post(f"/api/v1/runs/{run_id}/resume", headers=headers)
    assert resumed.status_code == 202
    assert (
        await client.post(f"/api/v1/runs/{run_id}/resume", headers=headers)
    ).status_code == 202
    await Worker(service, None).tick()
    completed = await client.get(
        f"/api/v1/runs/{run_id}", headers=bearer(tokens, "viewer")
    )
    assert completed.json()["final_output"] == {"text": "REAL CALLER INPUT!"}
    assert (
        "outputs" not in completed.json()
        and "definition_snapshot" not in completed.json()
    )
    # A paginated node detail exposes actual validated output separately.
    details = await client.get(
        f"/api/v1/runs/{run_id}/nodes?limit=1", headers=bearer(tokens, "viewer")
    )
    assert len(details.json()) == 1 and details.json()[0]["output"] == {
        "text": "REAL CALLER INPUT"
    }


async def test_api_cancel_input_limits_and_missing_resources(api: APIContext) -> None:
    _, client, service, _, tokens = api
    run = await make_run(api)
    response = await client.post(
        f"/api/v1/runs/{run['id']}/cancel", headers=bearer(tokens)
    )
    assert response.status_code == 202 and response.json()["status"] == "CANCELLED"
    assert not await Worker(service, None).tick()
    for suffix in ("", "/nodes", "/events", "/approvals"):
        assert (
            await client.get(f"/api/v1/runs/{uuid4()}{suffix}", headers=bearer(tokens))
        ).status_code == 404
    for query in ("limit=501", "offset=-1"):
        assert (
            await client.get("/api/v1/runs?" + query, headers=bearer(tokens))
        ).status_code == 422
    huge = await client.post(
        "/api/v1/runs",
        headers=bearer(tokens),
        json={
            "workflow_id": "approval",
            "version": "1",
            "input": {"text": "x" * 65537},
        },
    )
    assert huge.status_code == 422
    assert len(await service.list()) == 1
    missing = await client.post(
        "/api/v1/runs",
        headers=bearer(tokens),
        json={"workflow_id": "missing", "version": "1", "input": {}},
    )
    assert missing.status_code == 404


async def test_websocket_header_auth_reconnect_and_missed_notifications(
    api: APIContext,
) -> None:
    app, client, service, _, tokens = api
    run = await make_run(api, workflow="checkpoint")
    run_id = UUID(run["id"])

    def denied() -> dict[str, Any]:
        with TestClient(app) as browser:
            for query, headers, code in [
                ("?token=" + tokens["viewer"], {}, 4401),
                ("", bearer(tokens, "none"), 4403),
                ("", {"Authorization": "Bearer invalid"}, 4401),
            ]:
                with (
                    pytest.raises(WebSocketDisconnect) as exc,
                    browser.websocket_connect(
                        f"/api/v1/runs/{run_id}/stream" + query, headers=headers
                    ),
                ):
                    pass
                assert exc.value.code == code
            with browser.websocket_connect(
                f"/api/v1/runs/{run_id}/stream", headers=bearer(tokens, "viewer")
            ) as ws:
                data = ws.receive_json()
                assert isinstance(data, dict)
                return data

    first = await asyncio.to_thread(denied)
    assert first["sequence"] == 1 and first["event_type"] == "run.created"
    entered = threading.Event()

    def follow() -> list[dict[str, Any]]:
        seen: list[dict[str, Any]] = []
        with (
            TestClient(app) as browser,
            browser.websocket_connect(
                f"/api/v1/runs/{run_id}/stream?after_sequence=1",
                headers=bearer(tokens, "viewer"),
            ) as ws,
        ):
            entered.set()
            while True:
                event = ws.receive_json()
                seen.append(event)
                if event["event_type"] == "run.completed":
                    return seen

    following = asyncio.create_task(asyncio.to_thread(follow))
    assert await asyncio.to_thread(entered.wait, 5)
    # No notification publisher is attached. Live DB catch-up must discover writes.
    assert (
        await client.post(f"/api/v1/runs/{run_id}/start", headers=bearer(tokens))
    ).status_code == 202
    await Worker(service, None).tick()
    seen = await asyncio.wait_for(following, 10)
    durable = await service.events(run_id, after_sequence=1)
    assert [event["id"] for event in seen] == [str(event.id) for event in durable]
    assert [event["sequence"] for event in seen] == list(range(2, len(durable) + 2))


async def test_concurrent_resume_idempotency_target_and_empty_body_contract(
    api: APIContext,
) -> None:
    """AC14/15: resume has the same fenced/idempotent boundary as start."""
    _, client, service, _, tokens = api
    first = await make_run(api)
    second = await make_run(api)
    first_id, second_id = first["id"], second["id"]
    bad_start = await client.post(
        f"/api/v1/runs/{first_id}/start",
        headers={**bearer(tokens), "Idempotency-Key": "control-body"},
        json={"unexpected": "must not be silently ignored"},
    )
    assert bad_start.status_code == 422
    assert (await service.get(UUID(first_id))).status == "CREATED"

    for run_id in (first_id, second_id):
        queued = await client.post(
            f"/api/v1/runs/{run_id}/start", headers=bearer(tokens), json={}
        )
        assert queued.status_code == 202
        assert await Worker(service, None).tick()
        current = await service.get(UUID(run_id))
        pending = (await service.approvals(UUID(run_id)))[0]
        decided = await client.post(
            f"/api/v1/runs/{run_id}/approvals/{pending.id}/decision",
            headers=bearer(tokens),
            json={
                "decision": "approve",
                "expected_revision": current.revision,
                "content_revision": pending.content_revision,
                "content_hash": pending.content_hash,
            },
        )
        assert decided.status_code == 200 and decided.json()["status"] == "APPROVED"

    bad_resume = await client.post(
        f"/api/v1/runs/{first_id}/resume",
        headers={**bearer(tokens), "Idempotency-Key": "resume-race"},
        json={"unexpected": "different body"},
    )
    assert bad_resume.status_code == 422
    assert (await service.get(UUID(first_id))).status == "APPROVED"
    headers = {**bearer(tokens), "Idempotency-Key": "resume-race"}
    outcomes = await asyncio.gather(
        *(
            client.post(f"/api/v1/runs/{first_id}/resume", headers=headers, json={})
            for _ in range(4)
        )
    )
    assert [response.status_code for response in outcomes] == [202] * 4
    assert {response.json()["id"] for response in outcomes} == {first_id}
    changed_target = await client.post(
        f"/api/v1/runs/{second_id}/resume", headers=headers, json={}
    )
    assert changed_target.status_code == 409
    assert changed_target.json()["detail"]["code"] == "idempotency_conflict"
    assert (await service.get(UUID(second_id))).status == "APPROVED"
    # Competing workers can obtain only one current execution owner.
    claims = await asyncio.gather(
        Worker(service, None).claim(), Worker(service, None).claim()
    )
    assert sum(claim is not None for claim in claims) == 1
