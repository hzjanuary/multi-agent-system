"""Operational observability API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.auth.rbac import RoleName, require_roles
from app.core.metrics import InProcessMetrics, MetricsSnapshot
from app.models import User

OBSERVABILITY_READ_ROLES: tuple[RoleName, ...] = (
    RoleName.ADMIN,
    RoleName.MANAGER,
)

ObservabilityReadAccessDependency = Annotated[
    User,
    Depends(require_roles(*OBSERVABILITY_READ_ROLES)),
]

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get(
    "/metrics",
    response_model=MetricsSnapshot,
    summary="Get in-process operational metrics",
)
async def get_metrics(
    request: Request,
    _current_user: ObservabilityReadAccessDependency,
) -> MetricsSnapshot:
    """Return a bounded safe in-process metrics snapshot."""
    metrics = getattr(request.app.state, "metrics", None)
    if not isinstance(metrics, InProcessMetrics):
        metrics = InProcessMetrics(enabled=False)
    return metrics.snapshot()


__all__ = [
    "OBSERVABILITY_READ_ROLES",
    "ObservabilityReadAccessDependency",
    "router",
]
