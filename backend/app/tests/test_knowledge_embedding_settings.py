"""Tests for embedding settings integration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings
from app.knowledge.embeddings import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingProviderName,
    EmbeddingSettings,
)


def test_default_embedding_settings_are_no_key_safe() -> None:
    settings = Settings()

    assert settings.embedding_provider is EmbeddingProviderName.FAKE
    assert settings.embedding_settings == EmbeddingSettings()
    assert settings.embedding_settings.model == DEFAULT_EMBEDDING_MODEL
    assert settings.embedding_settings.dimensions == DEFAULT_EMBEDDING_DIMENSIONS


def test_embedding_settings_can_be_overridden_by_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "FAKE")
    monkeypatch.setenv("EMBEDDING_MODEL", "fake-custom")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "128")
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "16")

    settings = Settings()

    assert settings.embedding_settings.provider is EmbeddingProviderName.FAKE
    assert settings.embedding_settings.model == "fake-custom"
    assert settings.embedding_settings.dimensions == 128
    assert settings.embedding_settings.batch_size == 16


def test_embedding_settings_validate_dimensions_and_batch_size() -> None:
    with pytest.raises(ValidationError):
        EmbeddingSettings(dimensions=0)

    with pytest.raises(ValidationError):
        EmbeddingSettings(dimensions=4097)

    with pytest.raises(ValidationError):
        EmbeddingSettings(batch_size=0)

    with pytest.raises(ValidationError):
        EmbeddingSettings(batch_size=257)


def test_app_settings_reject_invalid_embedding_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "unsupported")

    with pytest.raises(ValidationError):
        Settings()
