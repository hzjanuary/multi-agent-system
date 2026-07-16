"""Tests for application settings."""

import pytest

from app.config import AppEnvironment, Settings
from app.llm import LLMProvider


def test_settings_load_default_development_values() -> None:
    settings = Settings()

    assert settings.app_name == "Enterprise Multi-Agent OS"
    assert settings.app_env is AppEnvironment.DEVELOPMENT
    assert settings.debug is True
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.backend_cors_origins == ("http://localhost:3000",)
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"
    assert settings.log_redaction_enabled is True
    assert settings.metrics_enabled is True
    assert settings.metrics_route_enabled is True
    assert settings.metrics_max_path_label_length == 120
    assert settings.jwt_secret_key == "development-only-change-me-32-bytes-minimum"
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.refresh_token_expire_days == 7
    assert settings.llm_provider is LLMProvider.FAKE
    assert settings.llm_model == ""
    assert settings.llm_runtime_enabled is False
    assert settings.llm_timeout_seconds == 30
    assert settings.llm_max_retries == 2
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.readiness_timeout_seconds == 2.0


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
    monkeypatch.setenv("LOG_FORMAT", "TEXT")
    monkeypatch.setenv("LOG_REDACTION_ENABLED", "false")
    monkeypatch.setenv("METRICS_ENABLED", "false")
    monkeypatch.setenv("METRICS_ROUTE_ENABLED", "false")
    monkeypatch.setenv("METRICS_MAX_PATH_LABEL_LENGTH", "240")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/1")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
    monkeypatch.setenv("MINIO_BUCKET_NAME", "quotes")
    monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "14")
    monkeypatch.setenv("LLM_PROVIDER", "GROQ")
    monkeypatch.setenv("LLM_MODEL", "global-model")
    monkeypatch.setenv("LLM_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("LLM_MAX_RETRIES", "4")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("GROQ_MODEL", "groq-model")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter-model")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-model")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "ollama-model")
    monkeypatch.setenv("READINESS_TIMEOUT_SECONDS", "5.5")

    settings = Settings()

    assert settings.app_name == "Settings Override"
    assert settings.app_env is AppEnvironment.PRODUCTION
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api"
    assert settings.backend_cors_origins == (
        "https://app.example.com",
        "https://admin.example.com",
    )
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "text"
    assert settings.log_redaction_enabled is False
    assert settings.metrics_enabled is False
    assert settings.metrics_route_enabled is False
    assert settings.metrics_max_path_label_length == 240
    assert settings.database_url == "postgresql+asyncpg://user:pass@db:5432/app"
    assert settings.redis_url == "redis://redis:6379/1"
    assert settings.qdrant_url == "http://qdrant:6333"
    assert settings.minio_endpoint == "minio:9000"
    assert settings.minio_access_key == "access"
    assert settings.minio_secret_key == "secret"
    assert settings.minio_bucket_name == "quotes"
    assert settings.jwt_secret_key == "jwt-secret"
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 15
    assert settings.refresh_token_expire_days == 14
    assert settings.llm_provider is LLMProvider.GROQ
    assert settings.llm_model == "global-model"
    assert settings.llm_runtime_enabled is True
    assert settings.llm_timeout_seconds == 60
    assert settings.llm_max_retries == 4
    assert settings.groq_api_key == "groq-key"
    assert settings.groq_model == "groq-model"
    assert settings.openrouter_api_key == "openrouter-key"
    assert settings.openrouter_model == "openrouter-model"
    assert settings.gemini_api_key == "gemini-key"
    assert settings.gemini_model == "gemini-model"
    assert settings.ollama_base_url == "http://ollama:11434"
    assert settings.ollama_model == "ollama-model"
    assert settings.readiness_timeout_seconds == 5.5


def test_testing_environment_can_be_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "false")

    settings = Settings()

    assert settings.app_env is AppEnvironment.TESTING
    assert settings.debug is False


def test_metrics_path_label_length_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_MAX_PATH_LABEL_LENGTH", "5")

    with pytest.raises(ValueError, match="METRICS_MAX_PATH_LABEL_LENGTH"):
        Settings()
