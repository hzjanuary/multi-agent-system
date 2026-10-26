"""Ollama local HTTP LLM client."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.llm.clients.base import (
    build_chat_response,
    normalize_finish_reason,
    request_timeout_seconds,
    resolve_model,
    usage_from_values,
    wants_json_object,
)
from app.llm.clients.http import (
    AsyncJSONHTTPTransport,
    HTTPResponse,
    HTTPTimeoutError,
    HTTPTransportError,
    HTTPXAsyncJSONHTTPTransport,
    retry_after_seconds,
)
from app.llm.contracts import (
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMProvider,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError


class OllamaLLMClient:
    """Ollama client using the local `/api/chat` endpoint."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str,
        transport: AsyncJSONHTTPTransport | None = None,
        default_timeout_seconds: int = 30,
    ) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._model = model.strip()
        self._transport = transport or HTTPXAsyncJSONHTTPTransport()
        self._default_timeout_seconds = default_timeout_seconds

    @property
    def provider(self) -> LLMProvider:
        """Return this client's provider identifier."""
        return LLMProvider.OLLAMA

    @property
    def model(self) -> str:
        """Return this client's configured default model."""
        return self._model

    def validate_ready(self) -> None:
        """Validate local provider configuration."""
        parsed = urlparse(self._base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise LLMConfigurationError(
                "ollama provider requires a valid HTTP base URL",
                provider=self.provider,
            )

    async def complete(self, request: LLMChatRequest) -> LLMChatResponse:
        """Complete a request using Ollama's chat endpoint."""
        self.validate_ready()
        model = resolve_model(
            provider=self.provider,
            configured_model=self.model,
            request=request,
        )
        payload = self._build_payload(request=request, model=model)
        try:
            response = await self._transport.post_json(
                url=f"{self._base_url}/api/chat",
                headers=self._headers(request),
                payload=payload,
                timeout_seconds=request_timeout_seconds(
                    request,
                    self._default_timeout_seconds,
                ),
            )
        except HTTPTimeoutError as exc:
            raise _ollama_error(
                request=request,
                category=LLMErrorCategory.TIMEOUT,
                message="provider request timed out",
            ) from exc
        except HTTPTransportError as exc:
            raise _ollama_error(
                request=request,
                category=LLMErrorCategory.UNAVAILABLE,
                message="provider is unavailable",
            ) from exc
        _raise_for_http_status(request, response)
        return self._normalize_response(response.payload, request=request, model=model)

    def _headers(self, request: LLMChatRequest) -> dict[str, str]:
        return {"X-Request-ID": request.request_id} if request.request_id else {}

    def _build_payload(
        self,
        *,
        request: LLMChatRequest,
        model: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens
        if wants_json_object(request):
            payload["format"] = "json"
        return payload

    def _normalize_response(
        self,
        payload: dict[str, Any],
        *,
        request: LLMChatRequest,
        model: str,
    ) -> LLMChatResponse:
        try:
            message = payload["message"]
            content = message["content"]
        except (KeyError, TypeError) as exc:
            raise _ollama_error(
                request=request,
                category=LLMErrorCategory.INVALID_RESPONSE,
                message="provider returned malformed chat response",
            ) from exc
        if not isinstance(content, str):
            raise _ollama_error(
                request=request,
                category=LLMErrorCategory.INVALID_RESPONSE,
                message="provider returned non-text chat content",
            )
        return build_chat_response(
            provider=self.provider,
            model=str(payload.get("model") or model),
            content=content,
            request=request,
            finish_reason=normalize_finish_reason(
                payload.get("done_reason") or ("stop" if payload.get("done") else None),
            ),
            usage=usage_from_values(
                prompt_tokens=payload.get("prompt_eval_count"),
                completion_tokens=payload.get("eval_count"),
            ),
            response_id=request.request_id,
            metadata={"provider_api": "ollama_chat"},
        )


def _raise_for_http_status(request: LLMChatRequest, response: HTTPResponse) -> None:
    if response.status_code < 400:
        return
    raise _ollama_error(
        request=request,
        category=_category_for_status(response.status_code),
        message=f"provider returned HTTP {response.status_code}",
        details={
            "http_status": response.status_code,
            "retry_after_seconds": retry_after_seconds(response),
        },
    )


def _category_for_status(status_code: int) -> LLMErrorCategory:
    if status_code in {401, 403}:
        return LLMErrorCategory.AUTHENTICATION
    if status_code == 408:
        return LLMErrorCategory.TIMEOUT
    if status_code == 429:
        return LLMErrorCategory.RATE_LIMIT
    if status_code in {400, 409, 422}:
        return LLMErrorCategory.INVALID_RESPONSE
    if status_code in {500, 502, 503, 504}:
        return LLMErrorCategory.UNAVAILABLE
    return LLMErrorCategory.UNKNOWN


def _ollama_error(
    *,
    request: LLMChatRequest,
    category: LLMErrorCategory,
    message: str,
    details: dict[str, Any] | None = None,
) -> LLMProviderError:
    return LLMProviderError(
        f"ollama {message}",
        category=category,
        provider=LLMProvider.OLLAMA,
        request_id=request.request_id,
        details=details,
    )
