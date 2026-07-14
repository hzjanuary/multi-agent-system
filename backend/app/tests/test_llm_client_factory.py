"""Tests for settings-driven LLM client factory."""

import pytest

from app.llm import LLMConfigurationError, LLMProvider, LLMSettings
from app.llm.clients import (
    FakeLLMClient,
    GeminiLLMClient,
    GroqLLMClient,
    OllamaLLMClient,
    OpenRouterLLMClient,
)
from app.llm.factory import SettingsLLMClientFactory, create_llm_client


def test_factory_default_creates_fake_client() -> None:
    client = create_llm_client(LLMSettings())

    assert isinstance(client, FakeLLMClient)
    assert client.provider is LLMProvider.FAKE
    assert client.model == "fake-deterministic-model"


@pytest.mark.parametrize(
    ("provider", "expected_type"),
    [
        (LLMProvider.FAKE, FakeLLMClient),
        (LLMProvider.GROQ, GroqLLMClient),
        (LLMProvider.OPENROUTER, OpenRouterLLMClient),
        (LLMProvider.OLLAMA, OllamaLLMClient),
        (LLMProvider.GEMINI, GeminiLLMClient),
    ],
)
def test_factory_supports_all_providers(
    provider: LLMProvider,
    expected_type: type[object],
) -> None:
    settings = LLMSettings(
        provider=provider,
        model="global-model",
        groq_api_key="groq-key",
        openrouter_api_key="openrouter-key",
        gemini_api_key="gemini-key",
        ollama_base_url="http://localhost:11434",
    )

    client = create_llm_client(settings)

    assert isinstance(client, expected_type)
    assert client.provider is provider


def test_factory_uses_provider_specific_model_overrides() -> None:
    settings = LLMSettings(
        provider=LLMProvider.GROQ,
        model="global-model",
        groq_model="groq-model",
        groq_api_key="groq-key",
    )

    client = create_llm_client(settings)

    assert isinstance(client, GroqLLMClient)
    assert client.model == "groq-model"


def test_factory_does_not_validate_missing_remote_key_until_client_use() -> None:
    client = create_llm_client(
        LLMSettings(provider=LLMProvider.GROQ, groq_model="groq-model"),
    )

    assert isinstance(client, GroqLLMClient)
    with pytest.raises(LLMConfigurationError):
        client.validate_ready()


def test_settings_factory_callable_uses_requested_provider_override() -> None:
    factory = SettingsLLMClientFactory()
    settings = LLMSettings(
        provider=LLMProvider.GROQ,
        model="global-model",
        groq_api_key="groq-key",
    )

    client = factory(settings, provider=LLMProvider.FAKE)

    assert isinstance(client, FakeLLMClient)
    assert client.provider is LLMProvider.FAKE
