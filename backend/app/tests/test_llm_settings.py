"""Tests for LLM application settings."""

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.llm import LLMConfigurationError, LLMProvider, LLMSettings


def test_default_llm_settings_are_no_key_safe() -> None:
    settings = Settings()

    assert settings.llm_provider is LLMProvider.FAKE
    assert settings.llm_model == ""
    assert settings.llm_runtime_enabled is False
    assert settings.llm_timeout_seconds == 30
    assert settings.llm_max_retries == 2
    assert settings.llm_fallback_enabled is False
    assert settings.llm_fallback_provider is LLMProvider.FAKE
    assert settings.groq_api_key == ""
    assert settings.openrouter_api_key == ""
    assert settings.gemini_api_key == ""
    assert settings.llm_settings.provider is LLMProvider.FAKE
    settings.llm_settings.require_provider_configuration()


def test_llm_settings_can_be_overridden_by_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "GROQ")
    monkeypatch.setenv("LLM_MODEL", "global-model")
    monkeypatch.setenv("LLM_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("LLM_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "fake")
    monkeypatch.setenv("GROQ_API_KEY", "demo-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setenv("OPENROUTER_API_KEY", "demo-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter-model")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")
    monkeypatch.setenv("GEMINI_API_KEY", "demo-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")

    settings = Settings()

    assert settings.llm_provider is LLMProvider.GROQ
    assert settings.llm_model == "global-model"
    assert settings.llm_runtime_enabled is True
    assert settings.llm_timeout_seconds == 45
    assert settings.llm_max_retries == 3
    assert settings.llm_fallback_enabled is True
    assert settings.llm_fallback_provider is LLMProvider.FAKE
    assert settings.llm_settings.selected_model == "llama-3.3-70b-versatile"
    assert settings.llm_settings.fallback_enabled is True
    settings.llm_settings.require_provider_configuration()


def test_real_provider_key_is_optional_at_settings_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    settings = Settings()

    assert settings.llm_provider is LLMProvider.OPENROUTER
    with pytest.raises(LLMConfigurationError) as exc_info:
        settings.llm_settings.require_provider_configuration()

    assert exc_info.value.category.value == "configuration"
    assert exc_info.value.provider is LLMProvider.OPENROUTER


def test_ollama_does_not_require_api_key() -> None:
    llm_settings = LLMSettings(
        provider=LLMProvider.OLLAMA,
        ollama_base_url="http://localhost:11434",
        ollama_model="llama3.1",
    )

    assert llm_settings.requires_api_key is False
    assert llm_settings.selected_model == "llama3.1"
    llm_settings.require_provider_configuration()


def test_invalid_llm_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "not-a-provider")

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("env_name", "env_value"),
    [
        ("LLM_TIMEOUT_SECONDS", "0"),
        ("LLM_TIMEOUT_SECONDS", "301"),
        ("LLM_MAX_RETRIES", "-1"),
        ("LLM_MAX_RETRIES", "11"),
    ],
)
def test_timeout_and_retry_ranges_are_validated(
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
    env_value: str,
) -> None:
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(ValidationError):
        Settings()
