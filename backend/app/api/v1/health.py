"""Health and service information routes."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.config import Settings
from app.core.dependencies import provide_readiness_checker, provide_settings
from app.core.readiness import ReadinessChecker
from app.schemas import HealthResponse, LiveResponse, ReadyResponse, RootResponse

API_VERSION = "0.2.0"
SettingsDependency = Annotated[Settings, Depends(provide_settings)]
ReadinessCheckerDependency = Annotated[
    ReadinessChecker,
    Depends(provide_readiness_checker),
]

router = APIRouter(tags=["health"])


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


@router.get("/", response_model=RootResponse)
async def root(settings: SettingsDependency) -> RootResponse:
    """Return basic service information."""
    return RootResponse(
        app_name=settings.app_name,
        environment=settings.app_env,
        version=API_VERSION,
        docs_url="/docs",
        health_url="/health",
    )


@router.get("/health", response_model=HealthResponse)
async def health(
    settings: SettingsDependency,
    checker: ReadinessCheckerDependency,
    response: Response,
) -> HealthResponse:
    """Return overall service health."""
    checks = await checker.check_all()
    required_ready = all(check.status == "ok" for check in checks if check.required)
    if not required_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status=(
            "unavailable"
            if not required_ready
            else "ok" if all(check.status == "ok" for check in checks) else "degraded"
        ),
        app_name=settings.app_name,
        environment=settings.app_env,
        version=API_VERSION,
        timestamp=utc_now(),
        checks=checks,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
)
async def ready(
    checker: ReadinessCheckerDependency,
    response: Response,
) -> ReadyResponse:
    """Return dependency readiness for required infrastructure."""
    checks = await checker.check_all()
    is_ready = all(check.status == "ok" for check in checks if check.required)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ready" if is_ready else "not_ready",
        timestamp=utc_now(),
        checks=checks,
    )


@router.get("/live", response_model=LiveResponse)
async def live() -> LiveResponse:
    """Return liveness status."""
    return LiveResponse(status="alive", timestamp=utc_now())
