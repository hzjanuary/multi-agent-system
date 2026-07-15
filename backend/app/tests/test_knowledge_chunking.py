"""Tests for deterministic knowledge chunking helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.knowledge.chunking import (
    build_chunk_id,
    chunk_document,
    normalize_knowledge_text,
    sha256_normalized_text,
)
from app.knowledge.schemas import (
    ChunkingConfig,
    KnowledgeDocument,
    KnowledgeDocumentMetadata,
    KnowledgeDocumentSourceType,
)


def _document(content: str, document_id: str = "contract-001") -> KnowledgeDocument:
    return KnowledgeDocument(
        metadata=KnowledgeDocumentMetadata(
            document_id=document_id,
            title="ACME IT Contract",
            source_type=KnowledgeDocumentSourceType.CONTRACT,
            domain="it_equipment",
        ),
        content=content,
    )


def test_chunking_config_validates_bounds() -> None:
    assert ChunkingConfig(
        max_chunk_chars=200, chunk_overlap_chars=20, min_chunk_chars=50
    )

    with pytest.raises(ValidationError, match="smaller"):
        ChunkingConfig(max_chunk_chars=200, chunk_overlap_chars=200, min_chunk_chars=50)

    with pytest.raises(ValidationError, match="<="):
        ChunkingConfig(max_chunk_chars=200, chunk_overlap_chars=20, min_chunk_chars=201)


def test_text_normalization_is_deterministic() -> None:
    messy = " First\t paragraph \r\n wraps. \n\n\nSecond   paragraph. "
    normalized = normalize_knowledge_text(messy)

    assert normalized == "First paragraph wraps.\n\nSecond paragraph."
    assert sha256_normalized_text(messy) == sha256_normalized_text(normalized)


def test_hash_changes_when_content_changes() -> None:
    assert sha256_normalized_text("Policy A") != sha256_normalized_text("Policy B")


def test_build_chunk_id_is_stable_for_same_inputs() -> None:
    chunk_id = build_chunk_id("doc-001", 0, "Stable chunk text")

    assert chunk_id == build_chunk_id("doc-001", 0, "Stable chunk text")
    assert chunk_id != build_chunk_id("doc-001", 1, "Stable chunk text")
    assert chunk_id.startswith("kbchunk:doc-001:0:")


def test_chunk_document_is_deterministic_and_preserves_ordering() -> None:
    content = "\n\n".join(
        [
            "Section one describes procurement controls for laptops.",
            "Section two describes warranty and service-level obligations.",
            "Section three describes approval thresholds and review notes.",
        ],
    )
    config = ChunkingConfig(
        max_chunk_chars=100, chunk_overlap_chars=10, min_chunk_chars=30
    )

    first = chunk_document(_document(content), config)
    second = chunk_document(_document(content), config)

    assert first == second
    assert first.checksum == sha256_normalized_text(content)
    assert [chunk.metadata.chunk_index for chunk in first.chunks] == list(
        range(len(first.chunks)),
    )
    assert first.chunks[0].text.startswith("Section one")


def test_chunk_document_applies_overlap_for_long_text() -> None:
    content = " ".join(f"word{index:03d}" for index in range(80))
    config = ChunkingConfig(
        max_chunk_chars=120, chunk_overlap_chars=24, min_chunk_chars=60
    )

    result = chunk_document(_document(content), config)

    assert len(result.chunks) > 1
    first_tail = result.chunks[0].text[-24:].strip()
    assert result.chunks[1].text.startswith(first_tail)


def test_chunks_are_non_empty_and_do_not_exceed_max_length() -> None:
    content = "\n\n".join(f"Paragraph {index} " + ("x" * 80) for index in range(10))
    config = ChunkingConfig(
        max_chunk_chars=180, chunk_overlap_chars=20, min_chunk_chars=50
    )

    result = chunk_document(_document(content), config)

    assert result.chunks
    assert all(chunk.text.strip() for chunk in result.chunks)
    assert all(len(chunk.text) <= config.max_chunk_chars for chunk in result.chunks)
    assert all(
        chunk.metadata.character_count == len(chunk.text) for chunk in result.chunks
    )


def test_repeated_chunking_produces_same_ids_and_checksums() -> None:
    content = " ".join(f"contract term {index}" for index in range(100))
    config = ChunkingConfig(
        max_chunk_chars=200, chunk_overlap_chars=30, min_chunk_chars=80
    )

    first = chunk_document(_document(content), config)
    second = chunk_document(_document(content), config)

    assert [chunk.metadata.chunk_id for chunk in first.chunks] == [
        chunk.metadata.chunk_id for chunk in second.chunks
    ]
    assert [chunk.metadata.checksum for chunk in first.chunks] == [
        chunk.metadata.checksum for chunk in second.chunks
    ]


def test_blank_document_content_is_rejected_by_contract() -> None:
    with pytest.raises(ValidationError):
        _document("   \n\n  ")
