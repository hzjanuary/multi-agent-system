"""Tests for application settings."""

import pytest

from app.config import AppEnvironment, Settings


def test_settings_load_default_development_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Enterprise Multi-Agent OS"
    assert settings.app_env is AppEnvironment.DEVELOPMENT
    assert settings.debug is True
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.backend_cors_origins == ("http://localhost:3000",)
    assert settings.log_level == "INFO"
    assert settings.llm_provider == "ollama"
    assert settings.ollama_base_url == "http://localhost:11434"


def test_settings_can_be_overridden_by_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "Settings Override")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("API_V1_PREFIX", "/api")
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        "https://app.example.com, https://admin.example.com",
    )
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/1")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
    monkeypatch.setenv("MINIO_BUCKET_NAME", "quotes")
    monkeypatch.setenv("LLM_PROVIDER", "GROQ")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")

    settings = Settings(_env_file=None)

    assert settings.app_name == "Settings Override"
    assert settings.app_env is AppEnvironment.PRODUCTION
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api"
    assert settings.backend_cors_origins == (
        "https://app.example.com",
        "https://admin.example.com",
    )
    assert settings.log_level == "DEBUG"
    assert settings.database_url == "postgresql+asyncpg://user:pass@db:5432/app"
    assert settings.redis_url == "redis://redis:6379/1"
    assert settings.qdrant_url == "http://qdrant:6333"
    assert settings.minio_endpoint == "minio:9000"
    assert settings.minio_access_key == "access"
    assert settings.minio_secret_key == "secret"
    assert settings.minio_bucket_name == "quotes"
    assert settings.llm_provider == "groq"
    assert settings.groq_api_key == "groq-key"
    assert settings.openrouter_api_key == "openrouter-key"
    assert settings.gemini_api_key == "gemini-key"
    assert settings.ollama_base_url == "http://ollama:11434"


def test_testing_environment_can_be_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "false")

    settings = Settings(_env_file=None)

    assert settings.app_env is AppEnvironment.TESTING
    assert settings.debug is False
