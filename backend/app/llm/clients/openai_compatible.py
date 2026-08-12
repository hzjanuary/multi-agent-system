"""OpenAI-compatible chat client shared by Groq and OpenRouter."""

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
    UrllibAsyncJSONHTTPTransport,
)
from app.llm.contracts import (
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMMessageRole,
    LLMProvider,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError


class OpenAICompatibleLLMClient:
    """Base client for providers exposing OpenAI-compatible chat completions."""

    def __init__(
        self,
        *,
        provider: LLMProvider,
        api_key: str,
        model: str,
        endpoint_url: str,
        transport: AsyncJSONHTTPTransport | None = None,
        default_timeout_seconds: int = 30,
    ) -> None:
        self._provider = provider
        self._api_key = api_key.strip()
        self._model = model.strip()
        self._endpoint_url = endpoint_url.strip()
        self._transport = transport or UrllibAsyncJSONHTTPTransport()
        self._default_timeout_seconds = default_timeout_seconds

    @property
    def provider(self) -> LLMProvider:
        """Return this client's provider identifier."""
        return self._provider

    @property
    def model(self) -> str:
        """Return this client's configured default model."""
        return self._model

    def validate_ready(self) -> None:
        """Validate remote provider configuration without exposing secrets."""
        if not self._api_key:
            raise LLMConfigurationError(
                f"{self.provider.value} provider requires an API key",
                provider=self.provider,
            )
        if not self._endpoint_url:
            raise LLMConfigurationError(
                f"{self.provider.value} provider requires an endpoint URL",
                provider=self.provider,
            )

    async def complete(self, request: LLMChatRequest) -> LLMChatResponse:
        """Complete a request using an OpenAI-compatible chat endpoint."""
        self.validate_ready()
        model = resolve_model(
            provider=self.provider,
            configured_model=self.model,
            request=request,
        )
        payload = self._build_payload(request=request, model=model)
        try:
            response = await self._transport.post_json(
                url=self._endpoint_url,
                headers=self._headers(request),
                payload=payload,
                timeout_seconds=request_timeout_seconds(
                    request,
                    self._default_timeout_seconds,
                ),
            )
        except HTTPTimeoutError as exc:
            raise _provider_error(
                provider=self.provider,
                request=request,
                category=LLMErrorCategory.TIMEOUT,
                message="provider request timed out",
            ) from exc
        except HTTPTransportError as exc:
            raise _provider_error(
                provider=self.provider,
                request=request,
                category=LLMErrorCategory.UNAVAILABLE,
                message="provider is unavailable",
            ) from exc
        _raise_for_http_status(self.provider, request, response)
        return self._normalize_response(response.payload, request=request, model=model)

    def _headers(self, request: LLMChatRequest) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "enterprise-os-backend/1.0",
        }
        if request.request_id:
            headers["X-Request-ID"] = request.request_id
        return headers

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
            "temperature": request.temperature,
            "stream": False,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if wants_json_object(request):
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _normalize_response(
        self,
        payload: dict[str, Any],
        *,
        request: LLMChatRequest,
        model: str,
    ) -> LLMChatResponse:
        try:
            choices = payload["choices"]
            first_choice = choices[0]
            message = first_choice["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise _provider_error(
                provider=self.provider,
                request=request,
                category=LLMErrorCategory.INVALID_RESPONSE,
                message="provider returned malformed chat response",
            ) from exc
        if not isinstance(content, str):
            raise _provider_error(
                provider=self.provider,
                request=request,
                category=LLMErrorCategory.INVALID_RESPONSE,
                message="provider returned non-text chat content",
            )
        usage_payload = payload.get("usage")
        usage: dict[str, Any] = usage_payload if isinstance(usage_payload, dict) else {}
        return build_chat_response(
            provider=self.provider,
            model=str(payload.get("model") or model),
            content=content,
            request=request,
            finish_reason=normalize_finish_reason(first_choice.get("finish_reason")),
            usage=usage_from_values(
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
            response_id=_optional_string(payload.get("id")),
            metadata={"provider_api": "openai_compatible"},
        )


def _raise_for_http_status(
    provider: LLMProvider,
    request: LLMChatRequest,
    response: HTTPResponse,
) -> None:
    if response.status_code < 400:
        return
    raise _provider_error(
        provider=provider,
        request=request,
        category=_category_for_status(response.status_code),
        message=f"provider returned HTTP {response.status_code}",
        details={"http_status": response.status_code},
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


def _provider_error(
    *,
    provider: LLMProvider,
    request: LLMChatRequest,
    category: LLMErrorCategory,
    message: str,
    details: dict[str, Any] | None = None,
) -> LLMProviderError:
    return LLMProviderError(
        f"{provider.value} {message}",
        category=category,
        provider=provider,
        request_id=request.request_id,
        details=details,
    )


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def openai_message_role(role: LLMMessageRole) -> str:
    """Return OpenAI-compatible role string."""
    return role.value
