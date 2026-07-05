"""Request ID middleware."""

from contextvars import ContextVar, Token
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

_request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def get_request_id() -> str | None:
    """Return the current request ID from context."""
    return _request_id_context.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to request state, context, and response headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        token: Token[str | None] = _request_id_context.set(request_id)
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id_context.reset(token)
