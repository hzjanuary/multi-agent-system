"""Groq LLM client."""

from __future__ import annotations

from typing import Any, Literal

from app.llm.clients.http import AsyncJSONHTTPTransport
from app.llm.clients.openai_compatible import OpenAICompatibleLLMClient
from app.llm.contracts import LLMChatRequest, LLMProvider
from app.llm.errors import LLMConfigurationError


class GroqLLMClient(OpenAICompatibleLLMClient):
    """Groq client using the OpenAI-compatible chat completions API."""

    def __init__(
        self,
        *,
        api_key: str,
        reasoning_effort: Literal["", "low", "medium", "high"] = "",
        model: str,
        endpoint_url: str = "https://api.groq.com/openai/v1/chat/completions",
        transport: AsyncJSONHTTPTransport | None = None,
        default_timeout_seconds: int = 30,
    ) -> None:
        self._reasoning_effort = reasoning_effort
        if reasoning_effort and model not in {
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        }:
            raise LLMConfigurationError(
                "reasoning setting requires a supported Groq GPT-OSS model"
            )
        super().__init__(
            provider=LLMProvider.GROQ,
            api_key=api_key,
            model=model,
            endpoint_url=endpoint_url,
            transport=transport,
            default_timeout_seconds=default_timeout_seconds,
        )

    def _build_payload(self, *, request: LLMChatRequest, model: str) -> dict[str, Any]:
        payload = super()._build_payload(request=request, model=model)
        if "max_tokens" in payload:
            payload["max_completion_tokens"] = payload.pop("max_tokens")
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
            payload["include_reasoning"] = False
        return payload
