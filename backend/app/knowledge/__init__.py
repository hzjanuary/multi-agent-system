"""Provider-independent knowledge base contracts and chunking helpers."""

from app.knowledge.chunking import (
    build_chunk_id,
    chunk_document,
    normalize_knowledge_text,
    sha256_normalized_text,
)
from app.knowledge.schemas import (
    ChunkingConfig,
    ChunkingResult,
    KnowledgeChunk,
    KnowledgeChunkMetadata,
    KnowledgeCitation,
    KnowledgeDocument,
    KnowledgeDocumentMetadata,
    KnowledgeDocumentSourceType,
    KnowledgeRetrievalResult,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)

__all__ = [
    "ChunkingConfig",
    "ChunkingResult",
    "KnowledgeChunk",
    "KnowledgeChunkMetadata",
    "KnowledgeCitation",
    "KnowledgeDocument",
    "KnowledgeDocumentMetadata",
    "KnowledgeDocumentSourceType",
    "KnowledgeRetrievalResult",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "build_chunk_id",
    "chunk_document",
    "normalize_knowledge_text",
    "sha256_normalized_text",
]
