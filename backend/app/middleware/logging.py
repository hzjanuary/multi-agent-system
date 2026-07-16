"""Request logging middleware."""

from time import perf_counter

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.metrics import (
    InProcessMetrics,
    normalize_path_label,
    route_template_for_scope,
)
from app.middleware.request_id import get_request_id

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request completion with duration and status metadata."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        metrics_collector: InProcessMetrics | None = None,
        max_path_label_length: int = 120,
    ) -> None:
        super().__init__(app)
        self._metrics_collector = metrics_collector
        self._max_path_label_length = max_path_label_length

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            request_id = getattr(request.state, "request_id", None) or get_request_id()
            path = route_template_for_scope(request.scope) or normalize_path_label(
                request.url.path,
                max_length=self._max_path_label_length,
            )
            if self._metrics_collector is not None:
                self._metrics_collector.record_http_request(
                    method=request.method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )

            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
