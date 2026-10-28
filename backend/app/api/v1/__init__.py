"""Versioned routes for the headless runtime."""

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router

__all__ = ["auth_router", "health_router"]
