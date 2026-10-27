"""Validated configuration for one trusted, headless self-hosted instance."""

from enum import StrEnum
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.llm.contracts import LLMProvider
from app.llm.provider_preferences import OpenRouterProviderPreferences
from app.llm.settings import LLMSettings


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Secrets are host configuration; missing model settings fail agent admission."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = "Multi-Agent OS"
    app_env: AppEnvironment = AppEnvironment.PRODUCTION
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins_raw: str = Field(default="", alias="BACKEND_CORS_ORIGINS")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"
    log_redaction_enabled: bool = True
    metrics_enabled: bool = True
    metrics_route_enabled: bool = False
    metrics_max_path_label_length: int = Field(default=120, ge=20, le=500)

    database_url: str = Field(repr=False)
    redis_url: str = Field(default="redis://localhost:6379/0", repr=False)
    jwt_secret_key: str = Field(min_length=32, repr=False)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=120)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    llm_provider: LLMProvider = LLMProvider.OLLAMA
    llm_model: str = ""
    llm_timeout_seconds: int = Field(default=60, ge=1, le=300)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_max_output_tokens: int = Field(default=1024, ge=1, le=32768)
    groq_api_key: str = Field(default="", repr=False)
    groq_reasoning_effort: Literal["", "low", "medium", "high"] = ""
    openrouter_api_key: str = Field(default="", repr=False)
    openrouter_provider_preferences_raw: str = Field(
        default="", alias="OPENROUTER_PROVIDER_PREFERENCES", repr=False
    )
    gemini_api_key: str = Field(default="", repr=False)
    ollama_base_url: str = "http://localhost:11434"
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = Field(default="", repr=False)
    extension_modules_raw: str = Field(default="", alias="MAOS_EXTENSION_MODULES")

    worker_heartbeat_seconds: float = Field(default=10, ge=0.1, le=60)
    worker_lease_seconds: float = Field(default=60, ge=1, le=600)
    worker_poll_seconds: float = Field(default=1, ge=0.05, le=30)
    worker_concurrency: int = Field(default=1, ge=1, le=1)
    max_workflow_nodes: int = Field(default=32, ge=1, le=32)
    max_provider_calls: int = Field(default=16, ge=1, le=128)
    max_input_bytes: int = Field(default=65536, ge=1024, le=65536)
    max_node_output_bytes: int = Field(default=65536, ge=1024, le=65536)
    max_run_bytes: int = Field(default=1048576, ge=65536, le=1048576)
    max_event_payload_bytes: int = Field(default=4096, ge=512, le=4096)
    readiness_timeout_seconds: float = Field(default=2, ge=0.1, le=30)

    @property
    def backend_cors_origins(self) -> tuple[str, ...]:
        return tuple(
            x.strip() for x in self.backend_cors_origins_raw.split(",") if x.strip()
        )

    @property
    def extension_modules(self) -> tuple[str, ...]:
        return tuple(
            x.strip() for x in self.extension_modules_raw.split(",") if x.strip()
        )

    @property
    def llm_settings(self) -> LLMSettings:
        return LLMSettings(
            provider=self.llm_provider,
            model=self.llm_model,
            timeout_seconds=self.llm_timeout_seconds,
            max_retries=self.llm_max_retries,
            max_output_tokens=self.llm_max_output_tokens,
            groq_api_key=self.groq_api_key,
            groq_reasoning_effort=self.groq_reasoning_effort,
            openrouter_api_key=self.openrouter_api_key,
            openrouter_provider_preferences=(
                OpenRouterProviderPreferences.model_validate_json(
                    self.openrouter_provider_preferences_raw
                )
                if self.openrouter_provider_preferences_raw.strip()
                else OpenRouterProviderPreferences()
            ),
            gemini_api_key=self.gemini_api_key,
            ollama_base_url=self.ollama_base_url,
            openai_compatible_base_url=self.openai_compatible_base_url,
            openai_compatible_api_key=self.openai_compatible_api_key,
        )

    @field_validator("openrouter_provider_preferences_raw")
    @classmethod
    def validate_openrouter_preferences(cls, value: str) -> str:
        if value.strip():
            try:
                OpenRouterProviderPreferences.model_validate_json(value)
            except ValueError:
                raise ValueError("invalid OpenRouter provider preferences") from None
        return value

    @field_validator("log_redaction_enabled")
    @classmethod
    def require_redaction(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Log redaction cannot be disabled")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "postgresql+asyncpg"
            or not parsed.hostname
            or not parsed.path.strip("/")
        ):
            raise ValueError("DATABASE_URL must identify a PostgreSQL asyncpg database")
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        lowered = value.lower()
        if len(set(value)) < 12 or any(
            x in lowered
            for x in ("change-me", "changeme", "development-only", "replace-me")
        ):
            raise ValueError("JWT_SECRET_KEY must be a generated non-default secret")
        return value

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        if value != "/api/v1":
            raise ValueError("API_V1_PREFIX must be /api/v1 for this release")
        return value

    @model_validator(mode="after")
    def validate_lease(self) -> "Settings":
        if self.worker_lease_seconds <= self.worker_heartbeat_seconds * 2:
            raise ValueError(
                "WORKER_LEASE_SECONDS must exceed twice WORKER_HEARTBEAT_SECONDS"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
