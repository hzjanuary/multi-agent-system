"""Workflow API router foundation."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict

from app.api.v1.workflow_errors import workflow_http_exception
from app.auth.rbac import RoleDependency, RoleName, require_roles
from app.core.dependencies import (
    DbSessionDependency,
    provide_workflow_event_service,
    provide_workflow_service,
)
from app.models import User
from app.models.enums import WorkflowStatus
from app.schemas.workflows_api import (
    WorkflowCreateRequest,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowTransitionRequest,
)
from app.workflows.events import WorkflowEventService
from app.workflows.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
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

router = APIRouter(prefix="/workflows", tags=["workflows"])

WORKFLOW_PLANNED_ENDPOINTS: tuple[str, ...] = (
    "POST /api/v1/workflows",
    "GET /api/v1/workflows",
    "GET /api/v1/workflows/{workflow_id}",
    "POST /api/v1/workflows/{workflow_id}/transition",
    "PATCH /api/v1/workflows/{workflow_id}/state",
    "GET /api/v1/workflows/{workflow_id}/events",
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
    """Static workflow router metadata for foundation validation."""

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
    """Return static metadata while workflow endpoint logic is deferred."""
    return WorkflowRouterMetadata(
        name="workflow-api",
        status="foundation-only",
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


__all__ = [
    "WORKFLOW_CREATE_ROLES",
    "WORKFLOW_FULL_ACCESS_ROLES",
    "WORKFLOW_PLANNED_ENDPOINTS",
    "WORKFLOW_READ_ROLES",
    "WorkflowCreateAccessDependency",
    "WorkflowEventServiceDependency",
    "WorkflowFullAccessDependency",
    "WorkflowReadAccessDependency",
    "WorkflowRouterMetadata",
    "WorkflowServiceDependency",
    "require_workflow_create_access",
    "require_workflow_full_access",
    "require_workflow_read_access",
    "router",
]
