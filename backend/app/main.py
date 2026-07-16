"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.v1 import (
    auth_router,
    health_router,
    knowledge_router,
    observability_router,
    workflows_router,
)
from app.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.metrics import InProcessMetrics
from app.exceptions import register_exception_handlers
from app.middleware import RequestIdMiddleware, RequestLoggingMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application instance."""
    app_settings = settings or get_settings()
    configure_logging(
        app_settings.log_level,
        log_format=app_settings.log_format,
        redaction_enabled=app_settings.log_redaction_enabled,
    )

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        debug=False,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.debug = app_settings.debug
    app.state.metrics = InProcessMetrics(
        enabled=app_settings.metrics_enabled,
        max_path_label_length=app_settings.metrics_max_path_label_length,
    )

    register_exception_handlers(app)
    configure_middleware(app, app_settings)
    app.include_router(health_router)
    if app_settings.metrics_route_enabled:
        app.include_router(observability_router, prefix=app_settings.api_v1_prefix)
    app.include_router(auth_router, prefix=app_settings.api_v1_prefix)
    app.include_router(knowledge_router, prefix=app_settings.api_v1_prefix)
    app.include_router(workflows_router, prefix=app_settings.api_v1_prefix)

    return app


def configure_middleware(app: FastAPI, settings: Settings) -> None:
    """Configure core FastAPI middleware."""
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.backend_cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        RequestLoggingMiddleware,
        metrics_collector=app.state.metrics,
        max_path_label_length=settings.metrics_max_path_label_length,
    )
    app.add_middleware(RequestIdMiddleware)


app = create_app()
