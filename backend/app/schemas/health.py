"""Health endpoint response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.config import AppEnvironment


class RootResponse(BaseModel):
    """Root service information response."""

    app_name: str
    environment: AppEnvironment
    version: str
    docs_url: str
    health_url: str


class HealthResponse(BaseModel):
    """Overall health response."""

    app_name: str
    environment: AppEnvironment
    version: str
    status: Literal["ok", "degraded", "unavailable"]
    timestamp: datetime
    checks: list["ReadinessDependencyStatus"]


class ReadyResponse(BaseModel):
    """Readiness response."""

    status: Literal["ready", "not_ready"]
    timestamp: datetime
    checks: list["ReadinessDependencyStatus"]


ReadinessDependencyStatusValue = Literal["ok", "failed", "skipped"]


class ReadinessDependencyStatus(BaseModel):
    """Per-dependency readiness check result."""

    name: str
    status: ReadinessDependencyStatusValue
    required: bool
    latency_ms: float | None = None
    message: str | None = None


class LiveResponse(BaseModel):
    """Liveness response."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "alive"}]})

    status: Literal["alive"]
    timestamp: datetime
