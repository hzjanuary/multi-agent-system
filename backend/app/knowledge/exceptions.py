"""Knowledge base domain exceptions."""

from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Base class for knowledge base contract and chunking errors."""


class KnowledgeChunkingError(KnowledgeBaseError):
    """Raised when document text cannot be chunked safely."""


class KnowledgeEmbeddingError(KnowledgeBaseError):
    """Base class for embedding contract and provider errors."""


class KnowledgeEmbeddingConfigurationError(KnowledgeEmbeddingError):
    """Raised when embedding provider configuration is invalid or unsupported."""


class KnowledgeEmbeddingInputError(KnowledgeEmbeddingError):
    """Raised when embedding input cannot be embedded safely."""
