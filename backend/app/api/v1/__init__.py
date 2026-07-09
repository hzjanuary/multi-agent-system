"""Version 1 API package."""

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.workflows import router as workflows_router

__all__ = ["auth_router", "health_router", "workflows_router"]
