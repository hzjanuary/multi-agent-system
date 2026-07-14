"""LLM settings helpers independent from provider implementations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.llm.contracts import LLMProvider
from app.llm.errors import LLMConfigurationError


class LLMSettings(BaseModel):
    """Typed LLM configuration derived from application settings."""

    model_config = ConfigDict(frozen=True)

    provider: LLMProvider = LLMProvider.FAKE
    model: str = ""
    runtime_enabled: bool = False
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=2, ge=0, le=10)
    fallback_enabled: bool = False
    fallback_provider: LLMProvider = LLMProvider.FAKE
    groq_api_key: str = ""
    groq_model: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        min_length=1,
        max_length=500,
    )
    ollama_model: str = ""
    gemini_api_key: str = ""
    gemini_model: str = ""

    @field_validator(
        "model",
        "groq_api_key",
        "groq_model",
        "openrouter_api_key",
        "openrouter_model",
        "ollama_base_url",
        "ollama_model",
        "gemini_api_key",
        "gemini_model",
        mode="before",
    )
    @classmethod
    def normalize_strings(cls, value: str | None) -> str:
        """Normalize optional environment strings to stripped strings."""
        return "" if value is None else str(value).strip()

    @property
    def selected_model(self) -> str:
        """Return provider-specific model override or global model."""
        provider_models = {
            LLMProvider.GROQ: self.groq_model,
            LLMProvider.OPENROUTER: self.openrouter_model,
            LLMProvider.OLLAMA: self.ollama_model,
            LLMProvider.GEMINI: self.gemini_model,
            LLMProvider.FAKE: self.model,
        }
        return provider_models[self.provider] or self.model

    def model_for_provider(self, provider: LLMProvider) -> str:
        """Return provider-specific model override or global model."""
        provider_models = {
            LLMProvider.GROQ: self.groq_model,
            LLMProvider.OPENROUTER: self.openrouter_model,
            LLMProvider.OLLAMA: self.ollama_model,
            LLMProvider.GEMINI: self.gemini_model,
            LLMProvider.FAKE: self.model,
        }
        return provider_models[provider] or self.model

    @property
    def requires_api_key(self) -> bool:
        """Return whether the selected provider needs an API key."""
        return self.provider in {
            LLMProvider.GROQ,
            LLMProvider.OPENROUTER,
            LLMProvider.GEMINI,
        }

    def require_provider_configuration(self) -> None:
        """Fail safely if the selected real provider is missing required config."""
        required_keys = {
            LLMProvider.GROQ: self.groq_api_key,
            LLMProvider.OPENROUTER: self.openrouter_api_key,
            LLMProvider.GEMINI: self.gemini_api_key,
        }
        required_key = required_keys.get(self.provider)
        if required_key is not None and not required_key:
            raise LLMConfigurationError(
                f"{self.provider.value} provider requires an API key",
                provider=self.provider,
            )
