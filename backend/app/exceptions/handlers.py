"""Global exception handlers."""

from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.middleware.request_id import REQUEST_ID_HEADER, get_request_id

logger = structlog.get_logger(__name__)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a consistent JSON response for unexpected errors."""
    request_id = getattr(request.state, "request_id", None) or get_request_id()

    logger.error(
        "unhandled_exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
    )

    content: dict[str, Any] = {
        "success": False,
        "data": None,
        "error": {
            "code": "internal_server_error",
            "message": "Internal server error",
            "details": {},
        },
        "request_id": request_id,
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
        headers={REQUEST_ID_HEADER: request_id} if request_id else None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    from app.definitions import DefinitionError
    from app.llm.errors import LLMConfigurationError
    from app.workflows.service import RunError

    async def run_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RunError)
        return JSONResponse(
            status_code=exc.status_code, content={"detail": {"code": exc.code}}
        )

    async def definition_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=422, content={"detail": {"code": "invalid_definition"}}
        )

    async def configuration_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": {"code": "provider_configuration"}}
        )

    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import SQLAlchemyError

    async def request_validation_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Omit raw rejected input; expose only bounded issue types.
        assert isinstance(exc, RequestValidationError)
        issues = [{"type": e["type"]} for e in exc.errors()[:20]]
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": "invalid_input", "issues": issues}},
        )

    async def storage_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": {"code": "storage_unavailable"}}
        )

    app.add_exception_handler(RequestValidationError, request_validation_error)
    app.add_exception_handler(SQLAlchemyError, storage_error)
    app.add_exception_handler(RunError, run_error)
    app.add_exception_handler(DefinitionError, definition_error)
    app.add_exception_handler(LLMConfigurationError, configuration_error)
    app.add_exception_handler(Exception, unhandled_exception_handler)
