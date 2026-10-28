"""Validated configuration for one explicitly selected real provider profile."""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from app.llm.contracts import LLMProvider
from app.llm.errors import LLMConfigurationError
from app.llm.provider_preferences import OpenRouterProviderPreferences


class LLMSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = Field(default="", max_length=200)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_output_tokens: int = Field(default=1024, ge=1, le=32768)
    groq_api_key: str = Field(default="", repr=False)
    groq_reasoning_effort: Literal["", "low", "medium", "high"] = ""
    openrouter_api_key: str = Field(default="", repr=False)
    openrouter_provider_preferences: OpenRouterProviderPreferences = Field(
        default_factory=OpenRouterProviderPreferences
    )
    gemini_api_key: str = Field(default="", repr=False)
    ollama_base_url: str = "http://localhost:11434"
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = Field(default="", repr=False)

    @property
    def selected_model(self) -> str:
        return self.model.strip()

    def model_for_provider(self, provider: LLMProvider) -> str:
        if provider != self.provider:
            raise LLMConfigurationError("cross-provider routing is disabled")
        return self.selected_model

    @property
    def endpoint(self) -> str:
        return {
            LLMProvider.OLLAMA: self.ollama_base_url.rstrip("/"),
            LLMProvider.OPENAI_COMPATIBLE: self.openai_compatible_base_url.rstrip("/"),
            LLMProvider.GROQ: "https://api.groq.com/openai/v1",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            LLMProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta",
        }[self.provider]

    def require_provider_configuration(self) -> None:
        if not self.selected_model:
            raise LLMConfigurationError(
                "selected provider requires an explicit model", provider=self.provider
            )
        keys = {
            LLMProvider.GROQ: self.groq_api_key,
            LLMProvider.OPENROUTER: self.openrouter_api_key,
            LLMProvider.GEMINI: self.gemini_api_key,
        }
        if self.provider in keys and not keys[self.provider].strip():
            raise LLMConfigurationError(
                "selected provider requires an API key", provider=self.provider
            )
        parsed = urlsplit(self.endpoint)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise LLMConfigurationError(
                "provider endpoint must be an HTTP(S) URL without credentials or query",
                provider=self.provider,
            )
