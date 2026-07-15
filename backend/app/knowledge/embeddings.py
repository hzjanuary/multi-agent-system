"""Provider-independent embedding contracts and deterministic fake provider."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from hashlib import sha256
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.knowledge.chunking import normalize_knowledge_text
from app.knowledge.exceptions import (
    KnowledgeEmbeddingConfigurationError,
    KnowledgeEmbeddingInputError,
)
from app.knowledge.schemas import validate_json_metadata

DEFAULT_EMBEDDING_MODEL = "fake-hash-embedding"
DEFAULT_EMBEDDING_DIMENSIONS = 64
DEFAULT_EMBEDDING_BATCH_SIZE = 32
MAX_EMBEDDING_DIMENSIONS = 4096
MAX_EMBEDDING_BATCH_SIZE = 256
MAX_EMBEDDING_TEXT_CHARS = 20_000
EMBEDDING_HASH_BYTES = 32


class EmbeddingProviderName(StrEnum):
    """Supported embedding provider identifiers."""

    FAKE = "fake"


class EmbeddingErrorCategory(StrEnum):
    """Safe embedding error categories for future providers."""

    CONFIGURATION = "configuration"
    INVALID_INPUT = "invalid_input"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN = "unknown"


class EmbeddingSettings(BaseModel):
    """Typed embedding configuration with offline-safe defaults."""

    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProviderName = EmbeddingProviderName.FAKE
    model: str = Field(default=DEFAULT_EMBEDDING_MODEL, min_length=1, max_length=200)
    dimensions: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        ge=1,
        le=MAX_EMBEDDING_DIMENSIONS,
    )
    batch_size: int = Field(
        default=DEFAULT_EMBEDDING_BATCH_SIZE,
        ge=1,
        le=MAX_EMBEDDING_BATCH_SIZE,
    )

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(
        cls, value: str | EmbeddingProviderName
    ) -> str | EmbeddingProviderName:
        """Normalize provider names loaded from environment variables."""
        return value.lower() if isinstance(value, str) else value

    @field_validator("model", mode="before")
    @classmethod
    def normalize_model(cls, value: str | None) -> str:
        """Normalize optional model strings."""
        normalized = "" if value is None else str(value).strip()
        return normalized or DEFAULT_EMBEDDING_MODEL


class EmbeddingInput(BaseModel):
    """Single bounded text input for embedding."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=MAX_EMBEDDING_TEXT_CHARS)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Normalize text and reject blank input."""
        normalized = normalize_knowledge_text(value)
        if not normalized:
            raise ValueError("embedding text must not be blank")
        return normalized

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure embedding metadata is safe and JSON-compatible."""
        return validate_json_metadata(value, "metadata")


class EmbeddingRequest(BaseModel):
    """Provider-independent embedding request."""

    model_config = ConfigDict(frozen=True)

    inputs: tuple[EmbeddingInput, ...] = Field(
        min_length=1, max_length=MAX_EMBEDDING_BATCH_SIZE
    )
    model: str | None = Field(default=None, min_length=1, max_length=200)
    dimensions: int | None = Field(default=None, ge=1, le=MAX_EMBEDDING_DIMENSIONS)
    request_id: str | None = Field(default=None, min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("inputs", mode="before")
    @classmethod
    def coerce_inputs(
        cls,
        value: tuple[EmbeddingInput, ...] | list[EmbeddingInput],
    ) -> tuple[EmbeddingInput, ...] | list[EmbeddingInput]:
        """Accept list input while storing inputs immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure request metadata is safe and JSON-compatible."""
        return validate_json_metadata(value, "metadata")


class EmbeddingVectorMetadata(BaseModel):
    """Metadata for one generated embedding vector."""

    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProviderName
    model: str = Field(min_length=1, max_length=200)
    dimensions: int = Field(ge=1, le=MAX_EMBEDDING_DIMENSIONS)
    input_index: int = Field(ge=0)
    text_checksum: str = Field(min_length=64, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure vector metadata is safe and JSON-compatible."""
        return validate_json_metadata(value, "metadata")


class EmbeddingResult(BaseModel):
    """Single embedding result."""

    model_config = ConfigDict(frozen=True)

    vector: tuple[float, ...] = Field(min_length=1, max_length=MAX_EMBEDDING_DIMENSIONS)
    metadata: EmbeddingVectorMetadata

    @field_validator("vector", mode="before")
    @classmethod
    def coerce_vector(
        cls, value: tuple[float, ...] | list[float]
    ) -> tuple[float, ...] | list[float]:
        """Accept list input while storing vectors immutably."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_dimensions_and_bounds(self) -> EmbeddingResult:
        """Ensure vector length and values match metadata bounds."""
        if len(self.vector) != self.metadata.dimensions:
            raise ValueError("embedding vector length must match metadata dimensions")
        for value in self.vector:
            if value < -1.0 or value > 1.0:
                raise ValueError("embedding vector values must be bounded")
        return self


class EmbeddingBatchResult(BaseModel):
    """Batch embedding result preserving input order."""

    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProviderName
    model: str = Field(min_length=1, max_length=200)
    dimensions: int = Field(ge=1, le=MAX_EMBEDDING_DIMENSIONS)
    results: tuple[EmbeddingResult, ...] = Field(
        min_length=1, max_length=MAX_EMBEDDING_BATCH_SIZE
    )
    request_id: str | None = Field(default=None, min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("results", mode="before")
    @classmethod
    def coerce_results(
        cls,
        value: tuple[EmbeddingResult, ...] | list[EmbeddingResult],
    ) -> tuple[EmbeddingResult, ...] | list[EmbeddingResult]:
        """Accept list input while storing results immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure batch metadata is safe and JSON-compatible."""
        return validate_json_metadata(value, "metadata")

    @model_validator(mode="after")
    def validate_result_shape(self) -> EmbeddingBatchResult:
        """Ensure result metadata is internally consistent and ordered."""
        for expected_index, result in enumerate(self.results):
            if result.metadata.provider is not self.provider:
                raise ValueError("result provider must match batch provider")
            if result.metadata.model != self.model:
                raise ValueError("result model must match batch model")
            if result.metadata.dimensions != self.dimensions:
                raise ValueError("result dimensions must match batch dimensions")
            if result.metadata.input_index != expected_index:
                raise ValueError("result input_index must preserve order")
        return self


class EmbeddingModelCapabilities(BaseModel):
    """Provider-independent embedding model capability metadata."""

    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProviderName
    model: str = Field(min_length=1, max_length=200)
    dimensions: int = Field(ge=1, le=MAX_EMBEDDING_DIMENSIONS)
    max_input_chars: int = Field(default=MAX_EMBEDDING_TEXT_CHARS, ge=1)
    max_batch_size: int = Field(default=DEFAULT_EMBEDDING_BATCH_SIZE, ge=1)
    is_local: bool = True


@runtime_checkable
class EmbeddingClient(Protocol):
    """Provider-independent async embedding client protocol."""

    @property
    def provider(self) -> EmbeddingProviderName:
        """Return provider identifier."""

    @property
    def model(self) -> str:
        """Return model identifier."""

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensions."""

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Embed one text input."""

    async def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        """Embed multiple text inputs while preserving order."""


class FakeEmbeddingClient:
    """Deterministic hash-based embedding client with no network calls."""

    def __init__(self, settings: EmbeddingSettings | None = None) -> None:
        self._settings = settings or EmbeddingSettings()
        if self._settings.provider is not EmbeddingProviderName.FAKE:
            raise KnowledgeEmbeddingConfigurationError(
                "FakeEmbeddingClient requires fake embedding provider settings",
            )

    @property
    def provider(self) -> EmbeddingProviderName:
        """Return provider identifier."""
        return self._settings.provider

    @property
    def model(self) -> str:
        """Return model identifier."""
        return self._settings.model

    @property
    def dimensions(self) -> int:
        """Return embedding vector dimensions."""
        return self._settings.dimensions

    @property
    def capabilities(self) -> EmbeddingModelCapabilities:
        """Return fake provider capability metadata."""
        return EmbeddingModelCapabilities(
            provider=self.provider,
            model=self.model,
            dimensions=self.dimensions,
            max_batch_size=self._settings.batch_size,
            is_local=True,
        )

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Embed one text input deterministically."""
        batch = await self.embed_texts((text,))
        return batch.results[0]

    async def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        """Embed multiple text inputs deterministically and in order."""
        if not texts:
            raise KnowledgeEmbeddingInputError("embedding batch must not be empty")
        if len(texts) > self._settings.batch_size:
            raise KnowledgeEmbeddingInputError(
                "embedding batch exceeds configured batch size"
            )

        inputs = tuple(EmbeddingInput(text=text) for text in texts)
        results = tuple(
            self._embed_input(input_value, input_index)
            for input_index, input_value in enumerate(inputs)
        )
        return EmbeddingBatchResult(
            provider=self.provider,
            model=self.model,
            dimensions=self.dimensions,
            results=results,
        )

    def _embed_input(
        self,
        input_value: EmbeddingInput,
        input_index: int,
    ) -> EmbeddingResult:
        normalized_text = input_value.text
        vector = _hash_to_vector(
            normalized_text,
            dimensions=self.dimensions,
            model=self.model,
        )
        metadata = EmbeddingVectorMetadata(
            provider=self.provider,
            model=self.model,
            dimensions=self.dimensions,
            input_index=input_index,
            text_checksum=sha256(normalized_text.encode("utf-8")).hexdigest(),
            metadata={"algorithm": "sha256-expand-v1"},
        )
        return EmbeddingResult(vector=vector, metadata=metadata)


class EmbeddingService:
    """Thin provider-independent service boundary for embedding clients."""

    def __init__(self, client: EmbeddingClient) -> None:
        self._client = client

    @property
    def provider(self) -> EmbeddingProviderName:
        """Return configured provider."""
        return self._client.provider

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Embed one text input through the configured client."""
        return await self._client.embed_text(text)

    async def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        """Embed multiple text inputs through the configured client."""
        return await self._client.embed_texts(texts)


def create_embedding_client(
    settings: EmbeddingSettings | None = None,
) -> EmbeddingClient:
    """Create an embedding client from settings without network calls."""
    embedding_settings = settings or EmbeddingSettings()
    if embedding_settings.provider is EmbeddingProviderName.FAKE:
        return FakeEmbeddingClient(embedding_settings)
    raise KnowledgeEmbeddingConfigurationError(
        f"Unsupported embedding provider: {embedding_settings.provider.value}",
    )


def create_embedding_service(
    settings: EmbeddingSettings | None = None,
) -> EmbeddingService:
    """Create an embedding service from settings without network calls."""
    return EmbeddingService(create_embedding_client(settings))


def _hash_to_vector(text: str, *, dimensions: int, model: str) -> tuple[float, ...]:
    values: list[float] = []
    block_index = 0
    seed = f"{model}\n{text}".encode()
    while len(values) < dimensions:
        digest = sha256(seed + block_index.to_bytes(4, byteorder="big")).digest()
        for byte_value in digest:
            # Map bytes to [-1.0, 1.0] with stable rounded floats.
            values.append(round((byte_value / 127.5) - 1.0, 8))
            if len(values) == dimensions:
                break
        block_index += 1
    return tuple(values)
