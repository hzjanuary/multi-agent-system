"""Typed application settings."""

from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    """Supported application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Enterprise Multi-Agent OS", alias="APP_NAME")
    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        alias="APP_ENV",
    )
    debug: bool = Field(default=True, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    backend_cors_origins_raw: str = Field(
        default="http://localhost:3000",
        alias="BACKEND_CORS_ORIGINS",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_os",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")

    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="", alias="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field(
        default="enterprise-multi-agent-os",
        alias="MINIO_BUCKET_NAME",
    )

    llm_provider: Literal["groq", "openrouter", "ollama", "gemini"] = Field(
        default="ollama",
        alias="LLM_PROVIDER",
    )
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )

    @property
    def backend_cors_origins(self) -> tuple[str, ...]:
        """Return configured CORS origins as an immutable tuple."""
        return tuple(
            origin.strip()
            for origin in self.backend_cors_origins_raw.split(",")
            if origin.strip()
        )

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        """Ensure API prefixes are absolute paths."""
        if not value.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'")
        return value.rstrip("/") or "/"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize log level values loaded from environment variables."""
        return value.upper()

    @field_validator("llm_provider", mode="before")
    @classmethod
    def normalize_llm_provider(cls, value: str) -> str:
        """Normalize provider names loaded from environment variables."""
        return value.lower()


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
