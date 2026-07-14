"""Settings-driven LLM client factory."""

from __future__ import annotations

from typing import Protocol

from app.llm.clients import (
    FakeLLMClient,
    GeminiLLMClient,
    GroqLLMClient,
    LLMClient,
    OllamaLLMClient,
    OpenRouterLLMClient,
)
from app.llm.clients.http import AsyncJSONHTTPTransport
from app.llm.contracts import LLMProvider
from app.llm.settings import LLMSettings


class LLMClientFactory(Protocol):
    """Callable client factory interface used by LLMService."""

    def __call__(
        self,
        settings: LLMSettings,
        *,
        provider: LLMProvider | None = None,
    ) -> LLMClient:
        """Create a client for the selected or requested provider."""
        ...


class SettingsLLMClientFactory:
    """Create concrete LLM clients from typed settings without network calls."""

    def __init__(
        self,
        *,
        transport: AsyncJSONHTTPTransport | None = None,
    ) -> None:
        self._transport = transport

    def __call__(
        self,
        settings: LLMSettings,
        *,
        provider: LLMProvider | None = None,
    ) -> LLMClient:
        """Create a provider client from settings."""
        selected_provider = provider or settings.provider
        return create_llm_client(
            settings,
            provider=selected_provider,
            transport=self._transport,
        )


def create_llm_client(
    settings: LLMSettings,
    *,
    provider: LLMProvider | None = None,
    transport: AsyncJSONHTTPTransport | None = None,
) -> LLMClient:
    """Create the provider client selected by settings.

    This function only constructs clients. It does not validate remote
    readiness, open sockets, or make provider network calls.
    """
    selected_provider = provider or settings.provider
    model = settings.model_for_provider(selected_provider)
    default_timeout_seconds = settings.timeout_seconds
    if selected_provider is LLMProvider.FAKE:
        return FakeLLMClient(model=model or "fake-deterministic-model")
    if selected_provider is LLMProvider.GROQ:
        return GroqLLMClient(
            api_key=settings.groq_api_key,
            model=model,
            transport=transport,
            default_timeout_seconds=default_timeout_seconds,
        )
    if selected_provider is LLMProvider.OPENROUTER:
        return OpenRouterLLMClient(
            api_key=settings.openrouter_api_key,
            model=model,
            transport=transport,
            default_timeout_seconds=default_timeout_seconds,
        )
    if selected_provider is LLMProvider.OLLAMA:
        return OllamaLLMClient(
            base_url=settings.ollama_base_url,
            model=model,
            transport=transport,
            default_timeout_seconds=default_timeout_seconds,
        )
    if selected_provider is LLMProvider.GEMINI:
        return GeminiLLMClient(
            api_key=settings.gemini_api_key,
            model=model,
            transport=transport,
            default_timeout_seconds=default_timeout_seconds,
        )
    raise AssertionError(f"Unsupported LLM provider: {selected_provider}")
