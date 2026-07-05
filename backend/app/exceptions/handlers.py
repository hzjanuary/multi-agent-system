"""Global exception handlers."""

from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.middleware.request_id import get_request_id

logger = structlog.get_logger(__name__)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a consistent JSON response for unexpected errors."""
    request_id = getattr(request.state, "request_id", None) or get_request_id()

    logger.exception(
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
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    app.add_exception_handler(Exception, unhandled_exception_handler)
