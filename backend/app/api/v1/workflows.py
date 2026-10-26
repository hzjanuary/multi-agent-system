"""Authenticated registry and durable run control; never executes provider calls."""

import asyncio
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect

from app.auth.rbac import RoleName, require_any_role
from app.composition import get_registry, get_run_service
from app.db import get_session_factory
from app.definitions import DefinitionError
from app.models import User
from app.services import AuthenticationError, AuthService
from app.workflows.service import RunError, RunService

router = APIRouter(tags=["workflows and runs"])
Reader = Annotated[
    User, Depends(require_any_role(RoleName.ADMIN, RoleName.OPERATOR, RoleName.VIEWER))
]
Writer = Annotated[User, Depends(require_any_role(RoleName.ADMIN, RoleName.OPERATOR))]
Service = Annotated[RunService, Depends(get_run_service)]
Key = Annotated[str | None, Header(alias="Idempotency-Key", max_length=200)]
Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]


class EmptyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=40)
    input: dict[str, Any]


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = Field(pattern="^(approve|reject)$")
    expected_revision: int = Field(ge=1)
    content_revision: int = Field(ge=1)
    content_hash: str = Field(pattern="^[a-f0-9]{64}$")
    comment: str | None = Field(default=None, max_length=2000)


def row(value: Any, *, summary: bool = False) -> dict[str, Any]:
    excluded = (
        {"definition_snapshot", "outputs", "input", "context"} if summary else set()
    )
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                c.key: getattr(value, c.key)
                for c in inspect(type(value)).columns
                if c.key not in excluded
            }
        ),
    )


def definition(value: Any) -> dict[str, Any]:
    snapshot = value.snapshot()
    return {
        "id": value.id,
        "version": value.version,
        "name": value.name,
        "definition_hash": value.definition_hash,
        "input_schema": snapshot["input"]["schema"],
        "output_schema": snapshot["output"]["schema"],
        "nodes": [n.id for n in value.nodes],
        "limits": snapshot["limits"],
        "extension": (
            snapshot["extension"]
            if "extension" in snapshot
            else snapshot.get("extension_identity", {})
        ),
    }


@router.get("/agents")
async def agents(user: Reader) -> list[dict[str, Any]]:
    return [
        {
            "id": a.id,
            "version": a.version,
            "name": a.name,
            "responsibility": a.responsibility,
            "input_schema": a.input_schema.model_json_schema(),
            "output_schema": a.output_schema.model_json_schema(),
        }
        for a in get_registry().agents
    ]


@router.get("/workflows")
async def workflows(user: Reader) -> list[dict[str, Any]]:
    return [definition(w) for w in get_registry().workflows.values()]


@router.get("/workflows/{workflow_id}")
async def workflow(
    workflow_id: str, user: Reader, version: str | None = None
) -> dict[str, Any]:
    try:
        return definition(get_registry().get(workflow_id, version))
    except DefinitionError as error:
        raise HTTPException(404, detail={"code": "definition_unavailable"}) from error


@router.post("/runs", status_code=201)
async def create(
    payload: CreateRequest, user: Writer, service: Service, idempotency_key: Key = None
) -> dict[str, Any]:
    return row(
        await service.create(
            user.id,
            payload.workflow_id,
            payload.version,
            payload.input,
            idempotency_key=idempotency_key,
        ),
        summary=True,
    )


@router.get("/runs")
async def runs(
    user: Reader,
    service: Service,
    status: str | None = None,
    workflow_id: str | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[dict[str, Any]]:
    return [
        row(r, summary=True)
        for r in await service.list(
            status=status, workflow_id=workflow_id, limit=limit, offset=offset
        )
    ]


@router.get("/runs/{run_id}")
async def show(run_id: UUID, user: Reader, service: Service) -> dict[str, Any]:
    return row(await service.get(run_id), summary=True)


@router.get("/runs/{run_id}/nodes")
async def nodes(
    run_id: UUID, user: Reader, service: Service, limit: Limit = 100, offset: Offset = 0
) -> list[dict[str, Any]]:
    await service.get(run_id)
    return [row(r) for r in await service.nodes(run_id, limit=limit, offset=offset)]


@router.post("/runs/{run_id}/start", status_code=202)
async def start(
    run_id: UUID,
    user: Writer,
    service: Service,
    idempotency_key: Key = None,
    payload: EmptyRequest | None = None,
) -> dict[str, Any]:
    return row(
        await service.start(run_id, user.id, idempotency_key=idempotency_key),
        summary=True,
    )


@router.post("/runs/{run_id}/resume", status_code=202)
async def resume(
    run_id: UUID,
    user: Writer,
    service: Service,
    idempotency_key: Key = None,
    payload: EmptyRequest | None = None,
) -> dict[str, Any]:
    return row(
        await service.resume(run_id, user.id, idempotency_key=idempotency_key),
        summary=True,
    )


@router.post("/runs/{run_id}/cancel", status_code=202)
async def cancel(run_id: UUID, user: Writer, service: Service) -> dict[str, Any]:
    return row(await service.cancel(run_id, user.id), summary=True)


@router.get("/runs/{run_id}/approvals")
async def approvals(
    run_id: UUID, user: Reader, service: Service, limit: Limit = 100, offset: Offset = 0
) -> list[dict[str, Any]]:
    await service.get(run_id)
    return [row(r) for r in await service.approvals(run_id, limit=limit, offset=offset)]


@router.post("/runs/{run_id}/approvals/{approval_id}/decision")
async def decide(
    run_id: UUID,
    approval_id: UUID,
    payload: DecisionRequest,
    user: Writer,
    service: Service,
) -> dict[str, Any]:
    return row(
        await service.decide(
            run_id,
            approval_id,
            user.id,
            **{
                **payload.model_dump(),
                "decision": {"approve": "approved", "reject": "rejected"}[
                    payload.decision
                ],
            },
        ),
        summary=True,
    )


@router.get("/runs/{run_id}/events")
async def events(
    run_id: UUID,
    user: Reader,
    service: Service,
    after_sequence: int = Query(default=0, ge=0),
    limit: Limit = 100,
) -> list[dict[str, Any]]:
    await service.get(run_id)
    return [
        row(r)
        for r in await service.events(
            run_id, after_sequence=after_sequence, limit=limit
        )
    ]


@router.websocket("/runs/{run_id}/stream")
async def stream(websocket: WebSocket, run_id: UUID, after_sequence: int = 0) -> None:
    # Authorization only in header, never query parameters. Polling closes both
    # notification gaps and the backlog/live handoff race.
    header = websocket.headers.get("authorization", "")
    if not header.startswith("Bearer ") or after_sequence < 0:
        await websocket.close(code=4401)
        return
    try:
        async with get_session_factory()() as session:
            user = await AuthService(session).get_current_user(header[7:])
            if not {r.name for r in user.roles} & {"admin", "operator", "viewer"}:
                await websocket.close(code=4403)
                return
        service = get_run_service()
        await service.get(run_id)
    except (AuthenticationError, RunError):
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        cursor = after_sequence
        while True:
            # Also reject expired access tokens during long-lived streams.
            async with get_session_factory()() as session:
                current = await AuthService(session).get_current_user(header[7:])
                if not {r.name for r in current.roles} & {
                    "admin",
                    "operator",
                    "viewer",
                }:
                    await websocket.close(code=4403)
                    return
            batch = await service.events(run_id, after_sequence=cursor, limit=100)
            for event in batch:
                await websocket.send_json(row(event))
                cursor = event.sequence
            if not batch:
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=0.5)
                    if message["type"] == "websocket.disconnect":
                        return
                except TimeoutError:
                    pass
    except (WebSocketDisconnect, AuthenticationError):
        return
