"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.config import Settings, get_settings
from app.core.logging import configure_logging
from app.exceptions import register_exception_handlers
from app.middleware import RequestIdMiddleware, RequestLoggingMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application instance."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        debug=False,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.debug = app_settings.debug

    register_exception_handlers(app)
    configure_middleware(app, app_settings)

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
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)


app = create_app()
