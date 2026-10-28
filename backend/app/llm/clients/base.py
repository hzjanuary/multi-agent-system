"""Provider-independent LLM client protocol and shared normalization helpers."""

from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable

from app.llm.contracts import (
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMFinishReason,
    LLMProvider,
    LLMResponseFormat,
    LLMStructuredResponseMetadata,
    LLMUsage,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError


@runtime_checkable
class LLMClient(Protocol):
    """Common async interface implemented by all concrete LLM clients."""

    @property
    def provider(self) -> LLMProvider:
        """Return this client's provider identifier."""
        ...

    @property
    def model(self) -> str:
        """Return this client's configured default model."""
        ...

    def validate_ready(self) -> None:
        """Raise a safe configuration error when the client cannot be used."""
        ...

    async def complete(self, request: LLMChatRequest) -> LLMChatResponse:
        """Complete a provider-independent chat request."""
        ...


def resolve_model(
    *,
    provider: LLMProvider,
    configured_model: str,
    request: LLMChatRequest,
) -> str:
    """Resolve the request model or raise a safe configuration error."""
    model = (request.model or configured_model).strip()
    if not model:
        raise LLMConfigurationError(
            f"{provider.value} provider requires a model",
            provider=provider,
        )
    return model


def request_timeout_seconds(
    request: LLMChatRequest,
    default_timeout_seconds: int,
) -> int:
    """Return the effective request timeout."""
    return request.timeout_seconds or default_timeout_seconds


def normalize_finish_reason(value: object) -> LLMFinishReason:
    """Map provider finish reason strings to the shared enum."""
    normalized = str(value or "").strip().lower()
    if normalized in {"stop", "done", "end_turn"}:
        return LLMFinishReason.STOP
    if normalized in {"length", "max_tokens", "max_output_tokens"}:
        return LLMFinishReason.LENGTH
    if normalized in {"content_filter", "safety", "blocked", "recitation"}:
        return LLMFinishReason.CONTENT_FILTER
    if normalized in {"tool_calls", "function_call"}:
        return LLMFinishReason.TOOL_CALLS
    if normalized == "error":
        return LLMFinishReason.ERROR
    return LLMFinishReason.UNKNOWN


def usage_from_values(
    *,
    prompt_tokens: object = None,
    completion_tokens: object = None,
    total_tokens: object = None,
) -> LLMUsage | None:
    """Build normalized usage metadata from provider token fields."""
    prompt = _coerce_non_negative_int(prompt_tokens)
    completion = _coerce_non_negative_int(completion_tokens)
    total = _coerce_non_negative_int(total_tokens)
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    if prompt is None and completion is None and total is None:
        return None
    return LLMUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
    )


def structured_json_from_content(
    *,
    content: str,
    request: LLMChatRequest,
    provider: LLMProvider,
) -> dict[str, Any] | None:
    """Parse structured JSON content when the request asks for JSON mode."""
    if not request.structured_json:
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            f"{provider.value} provider returned invalid structured JSON",
            category=LLMErrorCategory.INVALID_RESPONSE,
            provider=provider,
            request_id=request.request_id,
        ) from exc
    if not isinstance(parsed, dict):
        raise LLMProviderError(
            f"{provider.value} provider returned non-object structured JSON",
            category=LLMErrorCategory.INVALID_RESPONSE,
            provider=provider,
            request_id=request.request_id,
        )
    return parsed


def build_chat_response(
    *,
    provider: LLMProvider,
    model: str,
    content: str,
    request: LLMChatRequest,
    finish_reason: LLMFinishReason = LLMFinishReason.UNKNOWN,
    usage: LLMUsage | None = None,
    response_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> LLMChatResponse:
    """Build a shared response and parse structured content if requested."""
    structured_json = structured_json_from_content(
        content=content,
        request=request,
        provider=provider,
    )
    structured_metadata = (
        LLMStructuredResponseMetadata(schema_name="json_object")
        if structured_json is not None
        else None
    )
    safe_metadata = dict(metadata or {})
    if response_id:
        safe_metadata["provider_response_id"] = response_id
    return LLMChatResponse(
        provider=provider,
        model=model,
        content=content,
        structured_json=structured_json,
        structured_metadata=structured_metadata,
        finish_reason=finish_reason,
        usage=usage,
        request_id=response_id or request.request_id,
        metadata=safe_metadata,
    )


def wants_json_object(request: LLMChatRequest) -> bool:
    """Return whether a provider request should ask for JSON object output."""
    return request.response_format is LLMResponseFormat.JSON_OBJECT


def _coerce_non_negative_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and value.isdecimal():
        integer = int(value)
        return integer if integer >= 0 else None
    if not isinstance(value, float):
        return None
    if not value.is_integer():
        return None
    integer = int(value)
    return integer if integer >= 0 else None
