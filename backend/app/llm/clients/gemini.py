"""Gemini REST LLM client."""

from __future__ import annotations

from typing import Any

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
    LLMMessageRole,
    LLMProvider,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError


class GeminiLLMClient:
    """Gemini client using the non-streaming generateContent REST endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        endpoint_base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        transport: AsyncJSONHTTPTransport | None = None,
        default_timeout_seconds: int = 30,
    ) -> None:
        self._api_key = api_key.strip()
        self._model = model.strip()
        self._endpoint_base_url = endpoint_base_url.strip().rstrip("/")
        self._transport = transport or HTTPXAsyncJSONHTTPTransport()
        self._default_timeout_seconds = default_timeout_seconds

    @property
    def provider(self) -> LLMProvider:
        """Return this client's provider identifier."""
        return LLMProvider.GEMINI

    @property
    def model(self) -> str:
        """Return this client's configured default model."""
        return self._model

    def validate_ready(self) -> None:
        """Validate remote provider configuration without exposing secrets."""
        if not self._api_key:
            raise LLMConfigurationError(
                "gemini provider requires an API key",
                provider=self.provider,
            )
        if not self._endpoint_base_url.startswith(("http://", "https://")):
            raise LLMConfigurationError(
                "gemini provider requires a valid endpoint URL",
                provider=self.provider,
            )

    async def complete(self, request: LLMChatRequest) -> LLMChatResponse:
        """Complete a request using Gemini generateContent."""
        self.validate_ready()
        model = resolve_model(
            provider=self.provider,
            configured_model=self.model,
            request=request,
        )
        payload = self._build_payload(request=request)
        try:
            response = await self._transport.post_json(
                url=f"{self._endpoint_base_url}/models/{model}:generateContent",
                headers=self._headers(request),
                payload=payload,
                timeout_seconds=request_timeout_seconds(
                    request,
                    self._default_timeout_seconds,
                ),
            )
        except HTTPTimeoutError as exc:
            raise _gemini_error(
                request=request,
                category=LLMErrorCategory.TIMEOUT,
                message="provider request timed out",
            ) from exc
        except HTTPTransportError as exc:
            raise _gemini_error(
                request=request,
                category=LLMErrorCategory.UNAVAILABLE,
                message="provider is unavailable",
            ) from exc
        _raise_for_http_status(request, response)
        return self._normalize_response(response.payload, request=request, model=model)

    def _headers(self, request: LLMChatRequest) -> dict[str, str]:
        headers = {"x-goog-api-key": self._api_key}
        if request.request_id:
            headers["X-Request-ID"] = request.request_id
        return headers

    def _build_payload(self, *, request: LLMChatRequest) -> dict[str, Any]:
        system_parts: list[dict[str, str]] = []
        contents: list[dict[str, Any]] = []
        for message in request.messages:
            if message.role is LLMMessageRole.SYSTEM:
                system_parts.append({"text": message.content})
                continue
            role = "model" if message.role is LLMMessageRole.ASSISTANT else "user"
            contents.append({"role": role, "parts": [{"text": message.content}]})
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": request.temperature},
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        if request.max_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
        if wants_json_object(request):
            payload["generationConfig"]["responseMimeType"] = "application/json"
        return payload

    def _normalize_response(
        self,
        payload: dict[str, Any],
        *,
        request: LLMChatRequest,
        model: str,
    ) -> LLMChatResponse:
        try:
            candidate = payload["candidates"][0]
            parts = candidate["content"]["parts"]
            content = "".join(
                part.get("text", "") for part in parts if isinstance(part, dict)
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise _gemini_error(
                request=request,
                category=LLMErrorCategory.INVALID_RESPONSE,
                message="provider returned malformed generateContent response",
            ) from exc
        if not content:
            raise _gemini_error(
                request=request,
                category=LLMErrorCategory.INVALID_RESPONSE,
                message="provider returned empty text content",
            )
        usage_payload = payload.get("usageMetadata")
        usage: dict[str, Any] = usage_payload if isinstance(usage_payload, dict) else {}
        return build_chat_response(
            provider=self.provider,
            model=str(payload.get("modelVersion") or model),
            content=content,
            request=request,
            finish_reason=normalize_finish_reason(candidate.get("finishReason")),
            usage=usage_from_values(
                prompt_tokens=usage.get("promptTokenCount"),
                completion_tokens=usage.get("candidatesTokenCount"),
                total_tokens=usage.get("totalTokenCount"),
            ),
            response_id=request.request_id,
            metadata={"provider_api": "gemini_generate_content"},
        )


def _raise_for_http_status(request: LLMChatRequest, response: HTTPResponse) -> None:
    if response.status_code < 400:
        return
    raise _gemini_error(
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


def _gemini_error(
    *,
    request: LLMChatRequest,
    category: LLMErrorCategory,
    message: str,
    details: dict[str, Any] | None = None,
) -> LLMProviderError:
    return LLMProviderError(
        f"gemini {message}",
        category=category,
        provider=LLMProvider.GEMINI,
        request_id=request.request_id,
        details=details,
    )
