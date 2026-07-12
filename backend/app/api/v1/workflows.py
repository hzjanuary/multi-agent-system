"""Workflow API router foundation."""

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from pydantic import BaseModel, ConfigDict

from app.api.v1.workflow_errors import workflow_error_detail, workflow_http_exception
from app.auth.rbac import (
    RoleDependency,
    RoleName,
    get_user_role_names,
    normalize_role_name,
    require_roles,
)
from app.core.dependencies import (
    DbSessionDependency,
    provide_runtime_service,
    provide_workflow_event_service,
    provide_workflow_event_subscriber,
    provide_workflow_service,
)
from app.models import User
from app.models.enums import WorkflowStatus
from app.runtime.service import RuntimeService, WorkflowRuntimePreconditionError
from app.schemas.workflows_api import (
    WorkflowCreateRequest,
    WorkflowEventListResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowStateUpdateRequest,
    WorkflowTransitionRequest,
)
from app.services import AuthenticationError, AuthService
from app.streaming import WorkflowEventStreamMessage, WorkflowEventSubscriber
from app.streaming.schemas import workflow_event_to_stream_message
from app.workflows.events import WorkflowEventService
from app.workflows.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
    WorkflowStateMismatchError,
)
from app.workflows.service import WorkflowService

WorkflowLimitQuery = Annotated[int, Query(ge=1, le=100)]
WorkflowOffsetQuery = Annotated[int, Query(ge=0)]
WorkflowStatusQuery = Annotated[WorkflowStatus | None, Query(alias="status")]

WorkflowServiceDependency = Annotated[
    WorkflowService,
    Depends(provide_workflow_service),
]
WorkflowEventServiceDependency = Annotated[
    WorkflowEventService,
    Depends(provide_workflow_event_service),
]
WorkflowEventSubscriberDependency = Annotated[
    WorkflowEventSubscriber,
    Depends(provide_workflow_event_subscriber),
]
RuntimeServiceDependency = Annotated[
    RuntimeService,
    Depends(provide_runtime_service),
]

WORKFLOW_FULL_ACCESS_ROLES: tuple[RoleName, ...] = (
    RoleName.ADMIN,
    RoleName.MANAGER,
)
WORKFLOW_CREATE_ROLES: tuple[RoleName, ...] = (
    RoleName.ADMIN,
    RoleName.MANAGER,
    RoleName.SALES,
)
WORKFLOW_READ_ROLES: tuple[RoleName, ...] = (
    RoleName.ADMIN,
    RoleName.MANAGER,
    RoleName.SALES,
    RoleName.LEGAL,
    RoleName.FINANCE,
    RoleName.VIEWER,
)

WorkflowFullAccessDependency = Annotated[
    User,
    Depends(require_roles(*WORKFLOW_FULL_ACCESS_ROLES)),
]
WorkflowCreateAccessDependency = Annotated[
    User,
    Depends(require_roles(*WORKFLOW_CREATE_ROLES)),
]
WorkflowReadAccessDependency = Annotated[
    User,
    Depends(require_roles(*WORKFLOW_READ_ROLES)),
]

WORKFLOW_STREAM_BACKLOG_LIMIT = 50
WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE = status.WS_1008_POLICY_VIOLATION

router = APIRouter(prefix="/workflows", tags=["workflows"])

WORKFLOW_PLANNED_ENDPOINTS: tuple[str, ...] = (
    "POST /api/v1/workflows",
    "GET /api/v1/workflows",
    "GET /api/v1/workflows/{workflow_id}",
    "POST /api/v1/workflows/{workflow_id}/transition",
    "PATCH /api/v1/workflows/{workflow_id}/state",
    "GET /api/v1/workflows/{workflow_id}/events",
    "POST /api/v1/workflows/{workflow_id}/run",
    "WS /api/v1/workflows/{workflow_id}/stream",
)


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
)
async def create_workflow(
    payload: WorkflowCreateRequest,
    workflow_service: WorkflowServiceDependency,
    session: DbSessionDependency,
    current_user: WorkflowCreateAccessDependency,
) -> WorkflowResponse:
    """Create a workflow state record through the workflow service."""
    workflow = await workflow_service.create_workflow(
        payload,
        created_by_id=current_user.id,
    )
    await session.commit()
    return WorkflowResponse(workflow=workflow)


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List workflows",
)
async def list_workflows(
    _current_user: WorkflowReadAccessDependency,
    workflow_service: WorkflowServiceDependency,
    limit: WorkflowLimitQuery = 100,
    offset: WorkflowOffsetQuery = 0,
    status_filter: WorkflowStatusQuery = None,
) -> WorkflowListResponse:
    """List workflow states with minimal pagination and optional status filter."""
    workflows = await workflow_service.list_workflows(
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return WorkflowListResponse(
        workflows=workflows,
        count=len(workflows),
        limit=limit,
        offset=offset,
        status=status_filter,
    )


class WorkflowRouterMetadata(BaseModel):
    """Static workflow router metadata for API validation."""

    model_config = ConfigDict(frozen=True)

    name: str
    status: str
    planned_endpoints: tuple[str, ...]


@router.get(
    "/_meta",
    response_model=WorkflowRouterMetadata,
    summary="Workflow API router metadata",
)
async def workflow_router_metadata(
    _current_user: WorkflowReadAccessDependency,
) -> WorkflowRouterMetadata:
    """Return static workflow API metadata."""
    return WorkflowRouterMetadata(
        name="workflow-api",
        status="implemented",
        planned_endpoints=WORKFLOW_PLANNED_ENDPOINTS,
    )


@router.post(
    "/{workflow_id}/transition",
    response_model=WorkflowResponse,
    summary="Transition workflow status",
)
async def transition_workflow_status(
    workflow_id: UUID,
    payload: WorkflowTransitionRequest,
    workflow_service: WorkflowServiceDependency,
    session: DbSessionDependency,
    current_user: WorkflowFullAccessDependency,
) -> WorkflowResponse:
    """Transition one workflow status through the workflow service."""
    try:
        workflow = await workflow_service.transition_workflow_status(
            workflow_id,
            payload.to_status,
            actor_type="user",
            actor_id=current_user.id,
            reason=payload.reason,
        )
    except (InvalidWorkflowTransitionError, WorkflowNotFoundError) as error:
        raise workflow_http_exception(error) from error

    await session.commit()
    return WorkflowResponse(workflow=workflow)


@router.patch(
    "/{workflow_id}/state",
    response_model=WorkflowResponse,
    summary="Update workflow state",
)
async def update_workflow_state(
    workflow_id: UUID,
    payload: WorkflowStateUpdateRequest,
    workflow_service: WorkflowServiceDependency,
    session: DbSessionDependency,
    current_user: WorkflowFullAccessDependency,
) -> WorkflowResponse:
    """Update one workflow state payload through the workflow service."""
    try:
        workflow = await workflow_service.update_workflow_state(
            workflow_id,
            payload.state,
            actor_type="user",
            actor_id=current_user.id,
            reason=payload.reason,
        )
    except (WorkflowNotFoundError, WorkflowStateMismatchError) as error:
        raise workflow_http_exception(error) from error

    await session.commit()
    return WorkflowResponse(workflow=workflow)


@router.get(
    "/{workflow_id}/events",
    response_model=WorkflowEventListResponse,
    summary="List workflow events",
)
async def list_workflow_events(
    workflow_id: UUID,
    _current_user: WorkflowReadAccessDependency,
    workflow_event_service: WorkflowEventServiceDependency,
    limit: WorkflowLimitQuery = 100,
    offset: WorkflowOffsetQuery = 0,
) -> WorkflowEventListResponse:
    """List workflow events in deterministic chronological order."""
    try:
        events = await workflow_event_service.list_events_for_workflow(
            workflow_id,
            limit=limit,
            offset=offset,
        )
    except WorkflowNotFoundError as error:
        raise workflow_http_exception(error) from error

    return WorkflowEventListResponse(
        events=events,
        count=len(events),
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{workflow_id}/run",
    response_model=WorkflowRunResponse,
    summary="Run workflow",
)
async def run_workflow(
    workflow_id: UUID,
    runtime_service: RuntimeServiceDependency,
    session: DbSessionDependency,
    current_user: WorkflowFullAccessDependency,
) -> WorkflowRunResponse:
    """Run one workflow through the deterministic runtime service."""
    try:
        result = await runtime_service.run_workflow(
            workflow_id,
            actor_type="user",
            actor_id=current_user.id,
        )
    except WorkflowNotFoundError as error:
        raise workflow_http_exception(error) from error
    except WorkflowRuntimePreconditionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=workflow_error_detail(
                code="workflow_runtime_precondition_failed",
                message=str(error),
            ),
        ) from error

    await session.commit()
    return WorkflowRunResponse.from_runtime_result(result)


@router.websocket("/{workflow_id}/stream")
async def stream_workflow_events(
    websocket: WebSocket,
    workflow_id: UUID,
    session: DbSessionDependency,
    workflow_event_service: WorkflowEventServiceDependency,
    subscriber: WorkflowEventSubscriberDependency,
) -> None:
    """Stream backlog and live workflow events over a WebSocket connection."""
    await require_workflow_stream_access(websocket, session)
    try:
        backlog_messages = await _workflow_event_backlog_messages(
            workflow_id,
            workflow_event_service,
        )
    except WorkflowNotFoundError as error:
        raise WebSocketException(
            code=WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE,
            reason="Workflow not found",
        ) from error

    await websocket.accept()
    try:
        for message in backlog_messages:
            await send_workflow_stream_message(websocket, message)

        async for message in subscriber.subscribe_workflow_events(workflow_id):
            await send_workflow_stream_message(websocket, message)
    except WebSocketDisconnect:
        return


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow",
)
async def get_workflow(
    workflow_id: UUID,
    _current_user: WorkflowReadAccessDependency,
    workflow_service: WorkflowServiceDependency,
) -> WorkflowResponse:
    """Return one workflow state by id."""
    workflow = await workflow_service.get_workflow(workflow_id)
    if workflow is None:
        raise workflow_http_exception(
            WorkflowNotFoundError(f"Workflow {workflow_id} was not found"),
        )
    return WorkflowResponse(workflow=workflow)


def require_workflow_full_access() -> RoleDependency:
    """Require Admin or Manager workflow API access."""
    return require_roles(*WORKFLOW_FULL_ACCESS_ROLES)


def require_workflow_create_access() -> RoleDependency:
    """Require workflow creation access."""
    return require_roles(*WORKFLOW_CREATE_ROLES)


def require_workflow_read_access() -> RoleDependency:
    """Require workflow read/event access."""
    return require_roles(*WORKFLOW_READ_ROLES)


async def require_workflow_stream_access(
    websocket: WebSocket,
    session: DbSessionDependency,
) -> User:
    """Authenticate and authorize a workflow stream WebSocket connection."""
    token = _websocket_bearer_token(websocket)
    if token is None:
        raise WebSocketException(
            code=WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE,
            reason="Authentication required",
        )

    auth_service = AuthService(session)
    try:
        current_user = await auth_service.get_current_user(token)
    except AuthenticationError as error:
        raise WebSocketException(
            code=WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE,
            reason="Authentication required",
        ) from error

    allowed_role_names = {normalize_role_name(role) for role in WORKFLOW_READ_ROLES}
    if get_user_role_names(current_user).isdisjoint(allowed_role_names):
        raise WebSocketException(
            code=WORKFLOW_WEBSOCKET_POLICY_CLOSE_CODE,
            reason="Insufficient permissions",
        )
    return current_user


async def send_workflow_stream_message(
    websocket: WebSocket,
    message: WorkflowEventStreamMessage,
) -> None:
    """Send one schema-safe workflow event stream message as JSON."""
    await websocket.send_json(message.model_dump(mode="json", by_alias=True))


async def _workflow_event_backlog_messages(
    workflow_id: UUID,
    workflow_event_service: WorkflowEventService,
) -> list[WorkflowEventStreamMessage]:
    events = await workflow_event_service.list_events_for_workflow(
        workflow_id,
        limit=WORKFLOW_STREAM_BACKLOG_LIMIT,
        offset=0,
    )
    return [
        workflow_event_to_stream_message(event, sequence=sequence)
        for sequence, event in enumerate(events)
    ]


def _websocket_bearer_token(websocket: WebSocket) -> str | None:
    authorization = websocket.headers.get("authorization")
    if authorization is not None:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials:
            return credentials

    query_token = websocket.query_params.get("access_token")
    if query_token:
        return query_token

    return None


__all__ = [
    "WORKFLOW_CREATE_ROLES",
    "WORKFLOW_FULL_ACCESS_ROLES",
    "WORKFLOW_PLANNED_ENDPOINTS",
    "WORKFLOW_READ_ROLES",
    "WORKFLOW_STREAM_BACKLOG_LIMIT",
    "RuntimeServiceDependency",
    "WorkflowCreateAccessDependency",
    "WorkflowEventServiceDependency",
    "WorkflowEventSubscriberDependency",
    "WorkflowFullAccessDependency",
    "WorkflowReadAccessDependency",
    "WorkflowRouterMetadata",
    "WorkflowServiceDependency",
    "require_workflow_create_access",
    "require_workflow_full_access",
    "require_workflow_read_access",
    "require_workflow_stream_access",
    "router",
    "send_workflow_stream_message",
]
