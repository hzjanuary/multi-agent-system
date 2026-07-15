"""Tests for embedding contracts and deterministic fake provider."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.knowledge.embeddings import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingBatchResult,
    EmbeddingInput,
    EmbeddingProviderName,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingSettings,
    FakeEmbeddingClient,
    create_embedding_client,
    create_embedding_service,
)
from app.knowledge.exceptions import KnowledgeEmbeddingInputError


def test_embedding_contracts_validate_bounded_text_and_metadata() -> None:
    input_value = EmbeddingInput(
        text="  Contract terms\n\nfor warranty. ",
        metadata={"source": "unit-test"},
    )
    request = EmbeddingRequest(
        inputs=(input_value,),
        dimensions=16,
        metadata={"request": "safe"},
    )

    assert input_value.text == "Contract terms\n\nfor warranty."
    assert request.inputs == (input_value,)


def test_embedding_contract_rejects_blank_oversized_and_sensitive_metadata() -> None:
    with pytest.raises(ValidationError):
        EmbeddingInput(text="   \n\n")

    with pytest.raises(ValidationError):
        EmbeddingInput(text="x" * 20_001)

    with pytest.raises(ValidationError, match="sensitive"):
        EmbeddingInput(text="safe text", metadata={"api_key": "secret"})


@pytest.mark.asyncio
async def test_fake_provider_returns_configured_dimensions_and_bounded_values() -> None:
    client = FakeEmbeddingClient(EmbeddingSettings(dimensions=12))

    result = await client.embed_text("Warranty terms apply to laptop purchases.")

    assert isinstance(result, EmbeddingResult)
    assert result.metadata.provider is EmbeddingProviderName.FAKE
    assert result.metadata.model == DEFAULT_EMBEDDING_MODEL
    assert result.metadata.dimensions == 12
    assert len(result.vector) == 12
    assert all(isinstance(value, float) for value in result.vector)
    assert all(-1.0 <= value <= 1.0 for value in result.vector)


@pytest.mark.asyncio
async def test_fake_provider_is_deterministic_for_same_text_and_dimensions() -> None:
    client = FakeEmbeddingClient(EmbeddingSettings(dimensions=24))

    first = await client.embed_text("Manager approval is required.")
    second = await client.embed_text("Manager approval is required.")

    assert first == second


@pytest.mark.asyncio
async def test_fake_provider_changes_vector_for_different_text_or_model() -> None:
    client = FakeEmbeddingClient(EmbeddingSettings(dimensions=24))
    alternate_model_client = FakeEmbeddingClient(
        EmbeddingSettings(model="alternate-fake", dimensions=24),
    )

    first = await client.embed_text("Contract A")
    second = await client.embed_text("Contract B")
    alternate_model = await alternate_model_client.embed_text("Contract A")

    assert first.vector != second.vector
    assert first.vector != alternate_model.vector


@pytest.mark.asyncio
async def test_fake_provider_batch_preserves_order_and_is_repeatable() -> None:
    client = FakeEmbeddingClient(EmbeddingSettings(dimensions=16, batch_size=4))
    texts = ("policy", "contract", "pricing")

    first = await client.embed_texts(texts)
    second = await client.embed_texts(texts)

    assert isinstance(first, EmbeddingBatchResult)
    assert first == second
    assert [result.metadata.input_index for result in first.results] == [0, 1, 2]
    assert [result.vector for result in first.results] == [
        (await client.embed_text(text)).vector for text in texts
    ]


@pytest.mark.asyncio
async def test_fake_provider_rejects_empty_or_oversized_batches() -> None:
    client = FakeEmbeddingClient(EmbeddingSettings(batch_size=2))

    with pytest.raises(KnowledgeEmbeddingInputError):
        await client.embed_texts(())

    with pytest.raises(KnowledgeEmbeddingInputError):
        await client.embed_texts(("one", "two", "three"))


def test_factory_and_service_default_to_fake_provider() -> None:
    client = create_embedding_client()
    service = create_embedding_service()

    assert isinstance(client, FakeEmbeddingClient)
    assert service.provider is EmbeddingProviderName.FAKE


def test_fake_client_rejects_non_fake_settings_if_constructed_directly() -> None:
    with pytest.raises(ValidationError):
        EmbeddingSettings.model_validate({"provider": "unsupported"})


def test_embedding_result_rejects_wrong_dimensions_or_out_of_range_values() -> None:
    client = FakeEmbeddingClient(EmbeddingSettings(dimensions=4))
    metadata = client.capabilities

    assert metadata.provider is EmbeddingProviderName.FAKE

    with pytest.raises(ValidationError):
        EmbeddingResult.model_validate(
            {
                "vector": (0.1, 0.2),
                "metadata": {
                    "provider": "fake",
                    "model": DEFAULT_EMBEDDING_MODEL,
                    "dimensions": 4,
                    "input_index": 0,
                    "text_checksum": "a" * 64,
                },
            },
        )

    with pytest.raises(ValidationError):
        EmbeddingResult.model_validate(
            {
                "vector": (0.1, 2.0, 0.3, 0.4),
                "metadata": {
                    "provider": "fake",
                    "model": DEFAULT_EMBEDDING_MODEL,
                    "dimensions": 4,
                    "input_index": 0,
                    "text_checksum": "a" * 64,
                },
            },
        )


def test_default_embedding_dimensions_constant_matches_settings() -> None:
    settings = EmbeddingSettings()

    assert settings.provider is EmbeddingProviderName.FAKE
    assert settings.model == DEFAULT_EMBEDDING_MODEL
    assert settings.dimensions == DEFAULT_EMBEDDING_DIMENSIONS
    assert settings.batch_size == 32
