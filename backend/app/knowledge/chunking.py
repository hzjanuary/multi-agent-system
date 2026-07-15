"""Deterministic text chunking and content hashing helpers."""

from __future__ import annotations

from hashlib import sha256

from app.knowledge.exceptions import KnowledgeChunkingError
from app.knowledge.schemas import (
    ChunkingConfig,
    ChunkingResult,
    KnowledgeChunk,
    KnowledgeChunkMetadata,
    KnowledgeDocument,
)

CHUNK_ID_DIGEST_LENGTH = 16


def normalize_knowledge_text(text: str) -> str:
    """Normalize whitespace deterministically while preserving paragraphs."""
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs: list[str] = []
    current_lines: list[str] = []
    for line in normalized_newlines.split("\n"):
        stripped_line = " ".join(line.strip().split())
        if stripped_line:
            current_lines.append(stripped_line)
            continue
        if current_lines:
            paragraphs.append(" ".join(current_lines))
            current_lines = []
    if current_lines:
        paragraphs.append(" ".join(current_lines))
    return "\n\n".join(paragraphs).strip()


def sha256_normalized_text(text: str) -> str:
    """Return a stable SHA-256 hex digest of normalized text."""
    normalized = normalize_knowledge_text(text)
    return sha256(normalized.encode("utf-8")).hexdigest()


def build_chunk_id(document_id: str, chunk_index: int, chunk_text: str) -> str:
    """Build a reproducible chunk id from document id, index, and content hash."""
    chunk_digest = sha256_normalized_text(chunk_text)[:CHUNK_ID_DIGEST_LENGTH]
    return f"kbchunk:{document_id}:{chunk_index}:{chunk_digest}"


def chunk_document(
    document: KnowledgeDocument,
    config: ChunkingConfig | None = None,
) -> ChunkingResult:
    """Split a document into deterministic bounded character chunks."""
    chunking_config = config or ChunkingConfig()
    normalized_content = normalize_knowledge_text(document.content)
    if not normalized_content:
        raise KnowledgeChunkingError("document content has no chunkable text")

    document_checksum = sha256_normalized_text(normalized_content)
    chunk_texts = _split_text(normalized_content, chunking_config)
    if not chunk_texts:
        raise KnowledgeChunkingError("document content produced no chunks")

    chunks: list[KnowledgeChunk] = []
    for chunk_index, chunk_text in enumerate(chunk_texts):
        chunk_checksum = sha256_normalized_text(chunk_text)
        chunk_metadata = KnowledgeChunkMetadata(
            chunk_id=build_chunk_id(
                document.metadata.document_id,
                chunk_index,
                chunk_text,
            ),
            document_id=document.metadata.document_id,
            chunk_index=chunk_index,
            citation_label=f"{document.metadata.title} chunk {chunk_index + 1}",
            source_type=document.metadata.source_type,
            domain=document.metadata.domain,
            checksum=chunk_checksum,
            character_count=len(chunk_text),
        )
        chunks.append(KnowledgeChunk(metadata=chunk_metadata, text=chunk_text))

    return ChunkingResult(
        document_id=document.metadata.document_id,
        checksum=document_checksum,
        chunks=tuple(chunks),
    )


def _split_text(text: str, config: ChunkingConfig) -> list[str]:
    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + config.max_chunk_chars, text_length)
        if end < text_length:
            paragraph_boundary = text.rfind(
                "\n\n",
                start + config.min_chunk_chars,
                end,
            )
            if paragraph_boundary != -1:
                end = paragraph_boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = max(end - config.chunk_overlap_chars, 0)
        if next_start <= start:
            next_start = end
        start = _skip_leading_whitespace(text, next_start)

    return _merge_tiny_final_chunk(chunks, config)


def _skip_leading_whitespace(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def _merge_tiny_final_chunk(chunks: list[str], config: ChunkingConfig) -> list[str]:
    if len(chunks) < 2:
        return chunks
    final_chunk = chunks[-1]
    previous_chunk = chunks[-2]
    merged = f"{previous_chunk}\n\n{final_chunk}"
    if (
        len(final_chunk) < config.min_chunk_chars
        and len(merged) <= config.max_chunk_chars
    ):
        return [*chunks[:-2], merged]
    return chunks
