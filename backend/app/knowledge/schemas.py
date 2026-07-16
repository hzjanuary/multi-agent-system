"""Provider-independent knowledge base contracts."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_IDENTIFIER_LENGTH = 160
MAX_TITLE_LENGTH = 240
MAX_DOMAIN_LENGTH = 100
MAX_VERSION_LENGTH = 80
MAX_OWNER_TEAM_LENGTH = 120
MAX_STORAGE_KEY_LENGTH = 512
MAX_CHECKSUM_LENGTH = 128
MAX_CONTENT_TYPE_LENGTH = 120
MAX_DATASET_PATH_LENGTH = 512
MAX_TAGS = 20
MAX_TAG_LENGTH = 80
MAX_ATTRIBUTE_KEYS = 40
MAX_ATTRIBUTE_DEPTH = 4
MAX_ATTRIBUTE_STRING_LENGTH = 1000
MAX_ATTRIBUTE_LIST_LENGTH = 50
MAX_DOCUMENT_CONTENT_CHARS = 200_000
MAX_CHUNK_TEXT_CHARS = 8000
MAX_CITATION_EXCERPT_CHARS = 1200
MAX_QUERY_CHARS = 2000
MAX_SEARCH_TOP_K = 20
MAX_RESULTS = 50
MAX_SECTION_LENGTH = 200

SENSITIVE_METADATA_TOKENS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "chain_of_thought",
    "password",
    "provider_payload",
    "raw_prompt",
    "raw_provider",
    "secret",
    "token",
)


class KnowledgeDocumentSourceType(StrEnum):
    """Supported knowledge document source types."""

    POLICY = "policy"
    CONTRACT = "contract"
    PRICING = "pricing"
    SUPPLIER_PROFILE = "supplier_profile"
    RFQ = "rfq"
    GUIDELINE = "guideline"
    COMPLIANCE_CHECKLIST = "compliance_checklist"


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def validate_json_metadata(value: dict[str, Any], field_name: str) -> dict[str, Any]:
    """Validate bounded JSON-compatible metadata without sensitive keys."""
    _validate_json_value(value, field_name=field_name, depth=0)
    return value


def _validate_json_value(value: Any, *, field_name: str, depth: int) -> None:
    if depth > MAX_ATTRIBUTE_DEPTH:
        raise ValueError(f"{field_name} exceeds maximum nesting depth")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{field_name} contains a non-finite number")
        return
    if isinstance(value, str):
        if len(value) > MAX_ATTRIBUTE_STRING_LENGTH:
            raise ValueError(f"{field_name} contains an overlong string")
        return
    if isinstance(value, list):
        if len(value) > MAX_ATTRIBUTE_LIST_LENGTH:
            raise ValueError(f"{field_name} contains too many list items")
        for item in value:
            _validate_json_value(item, field_name=field_name, depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_ATTRIBUTE_KEYS:
            raise ValueError(f"{field_name} contains too many keys")
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field_name} keys must be strings")
            normalized_key = key.strip().lower()
            if not normalized_key or len(normalized_key) > MAX_TAG_LENGTH:
                raise ValueError(f"{field_name} keys must be bounded strings")
            if any(token in normalized_key for token in SENSITIVE_METADATA_TOKENS):
                raise ValueError(f"{field_name} contains sensitive metadata key")
            _validate_json_value(item, field_name=field_name, depth=depth + 1)
        return
    raise ValueError(f"{field_name} must be JSON-compatible")


class KnowledgeDocumentMetadata(BaseModel):
    """Safe metadata for a source document."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    source_type: KnowledgeDocumentSourceType
    domain: str = Field(min_length=1, max_length=MAX_DOMAIN_LENGTH)
    version: str | None = Field(
        default=None, min_length=1, max_length=MAX_VERSION_LENGTH
    )
    effective_date: date | None = None
    owner_team: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_OWNER_TEAM_LENGTH,
    )
    object_storage_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_STORAGE_KEY_LENGTH,
    )
    checksum: str | None = Field(
        default=None, min_length=1, max_length=MAX_CHECKSUM_LENGTH
    )
    content_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_CONTENT_TYPE_LENGTH,
    )
    dataset_path: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_DATASET_PATH_LENGTH,
    )
    tags: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_TAGS)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("document_id", "title", "domain", "version", "owner_team")
    @classmethod
    def strip_string_fields(cls, value: str | None) -> str | None:
        """Normalize bounded string fields."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(
        cls, value: tuple[str, ...] | list[str]
    ) -> tuple[str, ...] | list[str]:
        """Accept list input while storing tags immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Keep tags bounded and deterministic."""
        seen: set[str] = set()
        normalized: list[str] = []
        for tag in value:
            stripped = tag.strip()
            if not stripped or len(stripped) > MAX_TAG_LENGTH:
                raise ValueError("tags must be non-empty bounded strings")
            lowered = stripped.lower()
            if lowered in seen:
                continue
            if any(token in lowered for token in SENSITIVE_METADATA_TOKENS):
                raise ValueError("tags must not contain sensitive markers")
            seen.add(lowered)
            normalized.append(stripped)
        return tuple(normalized)

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure attributes are safe JSON-compatible metadata."""
        return validate_json_metadata(value, "attributes")


class KnowledgeDocument(BaseModel):
    """Source document content accepted by chunking helpers."""

    model_config = ConfigDict(frozen=True)

    metadata: KnowledgeDocumentMetadata
    content: str = Field(min_length=1, max_length=MAX_DOCUMENT_CONTENT_CHARS)

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        """Reject documents with no meaningful text."""
        if not value.strip():
            raise ValueError("document content must not be blank")
        return value


class KnowledgeChunkMetadata(BaseModel):
    """Metadata for a bounded searchable text chunk."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    document_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    chunk_index: int = Field(ge=0)
    citation_label: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    section: str | None = Field(
        default=None, min_length=1, max_length=MAX_SECTION_LENGTH
    )
    page: int | None = Field(default=None, ge=1)
    source_type: KnowledgeDocumentSourceType
    domain: str = Field(min_length=1, max_length=MAX_DOMAIN_LENGTH)
    checksum: str = Field(min_length=1, max_length=MAX_CHECKSUM_LENGTH)
    character_count: int = Field(ge=1, le=MAX_CHUNK_TEXT_CHARS)


class KnowledgeChunk(BaseModel):
    """Bounded chunk text plus citation metadata."""

    model_config = ConfigDict(frozen=True)

    metadata: KnowledgeChunkMetadata
    text: str = Field(min_length=1, max_length=MAX_CHUNK_TEXT_CHARS)

    @model_validator(mode="after")
    def validate_character_count(self) -> KnowledgeChunk:
        """Keep metadata count aligned with chunk text."""
        if self.metadata.character_count != len(self.text):
            raise ValueError("chunk character_count must match text length")
        return self


class KnowledgeCitation(BaseModel):
    """Safe source citation shown in runtime and frontend surfaces."""

    model_config = ConfigDict(frozen=True)

    citation_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    document_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    document_title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    source_type: KnowledgeDocumentSourceType
    section: str | None = Field(
        default=None, min_length=1, max_length=MAX_SECTION_LENGTH
    )
    page: int | None = Field(default=None, ge=1)
    excerpt: str = Field(min_length=1, max_length=MAX_CITATION_EXCERPT_CHARS)
    relevance_score: float = Field(ge=0, le=1)
    citation_label: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)


class KnowledgeRetrievalResult(BaseModel):
    """Provider-independent normalized retrieval result."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    document_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    chunk_text: str = Field(min_length=1, max_length=MAX_CHUNK_TEXT_CHARS)
    score: float = Field(ge=0, le=1)
    source_type: KnowledgeDocumentSourceType
    document_title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    domain: str = Field(min_length=1, max_length=MAX_DOMAIN_LENGTH)
    citation: KnowledgeCitation
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure retrieval metadata is safe and bounded."""
        return validate_json_metadata(value, "metadata")


class KnowledgeSearchRequest(BaseModel):
    """Search request contract for future retrieval APIs/services."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    top_k: int = Field(default=5, ge=1, le=MAX_SEARCH_TOP_K)
    source_types: tuple[KnowledgeDocumentSourceType, ...] = Field(default_factory=tuple)
    domain: str | None = Field(default=None, min_length=1, max_length=MAX_DOMAIN_LENGTH)
    document_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAX_SEARCH_TOP_K
    )
    minimum_score: float | None = Field(default=None, ge=0, le=1)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        """Normalize query text and reject whitespace-only queries."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped

    @field_validator("source_types", mode="before")
    @classmethod
    def coerce_source_types(
        cls,
        value: (
            tuple[KnowledgeDocumentSourceType, ...] | list[KnowledgeDocumentSourceType]
        ),
    ) -> tuple[KnowledgeDocumentSourceType, ...] | list[KnowledgeDocumentSourceType]:
        """Accept list input while storing source filters immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("document_ids", mode="before")
    @classmethod
    def coerce_document_ids(
        cls, value: tuple[str, ...] | list[str]
    ) -> tuple[str, ...] | list[str]:
        """Accept list input while storing document filters immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Keep document id filters bounded."""
        for document_id in value:
            if not document_id.strip() or len(document_id) > MAX_IDENTIFIER_LENGTH:
                raise ValueError("document_ids must contain bounded non-empty values")
        return value


class KnowledgeSearchResponse(BaseModel):
    """Search response contract with bounded retrieval results."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    results: tuple[KnowledgeRetrievalResult, ...] = Field(
        default_factory=tuple, max_length=MAX_RESULTS
    )

    @field_validator("results", mode="before")
    @classmethod
    def coerce_results(
        cls,
        value: tuple[KnowledgeRetrievalResult, ...] | list[KnowledgeRetrievalResult],
    ) -> tuple[KnowledgeRetrievalResult, ...] | list[KnowledgeRetrievalResult]:
        """Accept list input while storing results immutably."""
        return tuple(value) if isinstance(value, list) else value


class KnowledgeDocumentCatalogItem(BaseModel):
    """Bounded document catalog metadata for knowledge read APIs."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    source_type: KnowledgeDocumentSourceType
    domain: str = Field(min_length=1, max_length=MAX_DOMAIN_LENGTH)
    version: str | None = Field(
        default=None, min_length=1, max_length=MAX_VERSION_LENGTH
    )
    effective_date: date | None = None
    owner_team: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_OWNER_TEAM_LENGTH,
    )
    object_storage_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_STORAGE_KEY_LENGTH,
    )
    checksum: str | None = Field(
        default=None, min_length=1, max_length=MAX_CHECKSUM_LENGTH
    )
    content_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_CONTENT_TYPE_LENGTH,
    )
    dataset_path: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_DATASET_PATH_LENGTH,
    )
    tags: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_TAGS)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_metadata(
        cls,
        metadata: KnowledgeDocumentMetadata,
    ) -> KnowledgeDocumentCatalogItem:
        """Build a catalog item from safe document metadata."""
        return cls.model_validate(metadata.model_dump())

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(
        cls, value: tuple[str, ...] | list[str]
    ) -> tuple[str, ...] | list[str]:
        """Accept list input while storing tags immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Ensure catalog attributes remain safe JSON-compatible metadata."""
        return validate_json_metadata(value, "attributes")


class KnowledgeDocumentListResponse(BaseModel):
    """Read-only knowledge document catalog response."""

    model_config = ConfigDict(frozen=True)

    documents: tuple[KnowledgeDocumentCatalogItem, ...] = Field(
        default_factory=tuple,
        max_length=MAX_RESULTS,
    )
    count: int = Field(ge=0)

    @field_validator("documents", mode="before")
    @classmethod
    def coerce_documents(
        cls,
        value: (
            tuple[KnowledgeDocumentCatalogItem, ...]
            | list[KnowledgeDocumentCatalogItem]
        ),
    ) -> tuple[KnowledgeDocumentCatalogItem, ...] | list[KnowledgeDocumentCatalogItem]:
        """Accept list input while storing documents immutably."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_count(self) -> KnowledgeDocumentListResponse:
        """Keep count aligned with returned bounded catalog items."""
        if self.count != len(self.documents):
            raise ValueError("count must match number of documents")
        return self


class KnowledgeDocumentDetailResponse(BaseModel):
    """Read-only document detail response with optional bounded preview."""

    model_config = ConfigDict(frozen=True)

    document: KnowledgeDocumentCatalogItem
    content_preview: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_CITATION_EXCERPT_CHARS,
    )


class ChunkingConfig(BaseModel):
    """Deterministic character-based chunking configuration."""

    model_config = ConfigDict(frozen=True)

    max_chunk_chars: int = Field(default=1200, ge=100, le=MAX_CHUNK_TEXT_CHARS)
    chunk_overlap_chars: int = Field(default=120, ge=0, le=MAX_CHUNK_TEXT_CHARS)
    min_chunk_chars: int = Field(default=120, ge=1, le=MAX_CHUNK_TEXT_CHARS)

    @model_validator(mode="after")
    def validate_chunking_bounds(self) -> ChunkingConfig:
        """Validate chunk size relationships."""
        if self.chunk_overlap_chars >= self.max_chunk_chars:
            raise ValueError("chunk_overlap_chars must be smaller than max_chunk_chars")
        if self.min_chunk_chars > self.max_chunk_chars:
            raise ValueError("min_chunk_chars must be <= max_chunk_chars")
        return self


class ChunkingResult(BaseModel):
    """Result returned by deterministic chunking helpers."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    checksum: str = Field(min_length=1, max_length=MAX_CHECKSUM_LENGTH)
    chunks: tuple[KnowledgeChunk, ...] = Field(min_length=1)

    @field_validator("chunks", mode="before")
    @classmethod
    def coerce_chunks(
        cls,
        value: tuple[KnowledgeChunk, ...] | list[KnowledgeChunk],
    ) -> tuple[KnowledgeChunk, ...] | list[KnowledgeChunk]:
        """Accept list input while storing chunks immutably."""
        return tuple(value) if isinstance(value, list) else value
