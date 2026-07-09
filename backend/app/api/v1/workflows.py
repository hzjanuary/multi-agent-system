"""Workflow API router foundation."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.auth.rbac import RoleDependency, RoleName, require_roles
from app.core.dependencies import (
    provide_workflow_event_service,
    provide_workflow_service,
)
from app.models import User
from app.workflows.events import WorkflowEventService
from app.workflows.service import WorkflowService

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
