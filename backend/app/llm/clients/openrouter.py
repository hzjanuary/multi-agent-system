"""OpenRouter LLM client."""

from __future__ import annotations

import math
from typing import Any

from app.llm.clients.http import AsyncJSONHTTPTransport, HTTPResponse
from app.llm.clients.openai_compatible import OpenAICompatibleLLMClient
from app.llm.contracts import LLMChatRequest, LLMChatResponse, LLMProvider
from app.llm.diagnostics import ProviderDiagnostics, extract_diagnostics
from app.llm.provider_preferences import OpenRouterProviderPreferences


class OpenRouterLLMClient(OpenAICompatibleLLMClient):
    """OpenRouter client using the OpenAI-like chat completions API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        endpoint_url: str = "https://openrouter.ai/api/v1/chat/completions",
        transport: AsyncJSONHTTPTransport | None = None,
        default_timeout_seconds: int = 30,
        provider_preferences: OpenRouterProviderPreferences | None = None,
    ) -> None:
        self._provider_preferences = (
            provider_preferences or OpenRouterProviderPreferences()
        )
        super().__init__(
            provider=LLMProvider.OPENROUTER,
            api_key=api_key,
            model=model,
            endpoint_url=endpoint_url,
            transport=transport,
            default_timeout_seconds=default_timeout_seconds,
        )

    def _error_diagnostics(
        self, request: LLMChatRequest, response: HTTPResponse
    ) -> ProviderDiagnostics | None:
        return extract_diagnostics(response, request, self._api_key)

    def _build_payload(self, *, request: LLMChatRequest, model: str) -> dict[str, Any]:
        payload = super()._build_payload(request=request, model=model)
        payload["provider"] = self._provider_preferences.request_dict()
        # No optional web/plugin/server-tool definitions are supplied by this client.
        payload["plugins"] = []
        return payload

    def _normalize_response(
        self, payload: dict[str, Any], *, request: LLMChatRequest, model: str
    ) -> LLMChatResponse:
        response = super()._normalize_response(payload, request=request, model=model)
        metadata = dict(response.metadata)
        provider = payload.get("provider")
        if isinstance(provider, str) and len(provider) <= 120:
            metadata["provider_route"] = provider
        usage = payload.get("usage")
        cost = usage.get("cost") if isinstance(usage, dict) else None
        # Record actual provider-reported cost; never derive it from catalog prices.
        if (
            isinstance(cost, (int, float))
            and not isinstance(cost, bool)
            and math.isfinite(cost)
            and cost >= 0
        ):
            metadata["reported_cost"] = cost
            metadata["cost_currency"] = "USD"
        return response.model_copy(update={"metadata": metadata})
