"""Secure headless configuration and explicit real-provider admission."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.llm.contracts import LLMProvider
from app.llm.errors import LLMConfigurationError

SECRET = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
DB = "postgresql+asyncpg://user:password@localhost/maos"


def settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, database_url=DB, jwt_secret_key=SECRET, **overrides)


def test_required_configuration_has_no_insecure_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError) as caught:
        Settings(_env_file=None)
    assert {e["loc"][0] for e in caught.value.errors()} >= {
        "database_url",
        "jwt_secret_key",
    }


@pytest.mark.parametrize("provider", ["fake", "mock", "disabled", "unknown"])
def test_fake_or_unknown_provider_rejected(provider: str) -> None:
    with pytest.raises(ValidationError):
        settings(llm_provider=provider)


@pytest.mark.parametrize(
    "secret", ["tiny-value", "x" * 64, "development-only-change-me-32-bytes-minimum"]
)
def test_unsafe_jwt_secret_rejected_without_echo(secret: str) -> None:
    with pytest.raises(ValidationError) as caught:
        Settings(_env_file=None, database_url=DB, jwt_secret_key=secret)
    assert secret not in str(caught.value)


def test_provider_never_defaults_to_inference_success() -> None:
    config = settings()
    assert config.llm_provider == LLMProvider.OLLAMA
    with pytest.raises(LLMConfigurationError):
        config.llm_settings.require_provider_configuration()


def test_extension_configuration_is_explicit() -> None:
    config = settings(
        MAOS_EXTENSION_MODULES="maos_examples.text_review, company.workflows"
    )
    assert config.extension_modules == (
        "maos_examples.text_review",
        "company.workflows",
    )
    assert settings().extension_modules == ()


@pytest.mark.parametrize(
    "key,value",
    [
        ("database_url", "sqlite:///memory"),
        ("worker_heartbeat_seconds", 60),
        ("max_provider_calls", 0),
        ("max_input_bytes", 65537),
        ("log_redaction_enabled", False),
        ("worker_concurrency", 2),
        ("llm_max_retries", 6),
        ("llm_max_output_tokens", 0),
    ],
)
def test_unsafe_or_unbounded_configuration_rejected(key: str, value: object) -> None:
    base: dict[str, Any] = {"database_url": DB, "jwt_secret_key": SECRET, key: value}
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **base)


def test_release_and_public_templates_match() -> None:
    backend = Path(__file__).resolve().parents[2]
    assert (backend / "app/config/default.env").read_bytes() == (
        backend.parent / ".env.example"
    ).read_bytes()


def test_compose_string_values_validate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_REDACTION_ENABLED", "true")
    monkeypatch.setenv("WORKER_CONCURRENCY", "1")
    config = settings()
    assert config.log_redaction_enabled is True
    assert config.worker_concurrency == 1


def test_reference_template_covers_all_application_settings() -> None:
    path = Path(__file__).resolve().parents[1] / "config/default.env"
    keys = {
        line.split("=", 1)[0]
        for line in path.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    }
    expected = {
        field.alias or name.upper() for name, field in Settings.model_fields.items()
    }
    assert expected <= keys
