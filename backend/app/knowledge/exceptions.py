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


class KnowledgeIngestionError(KnowledgeBaseError):
    """Base class for knowledge ingestion errors."""


class KnowledgeIngestionConfigurationError(KnowledgeIngestionError):
    """Raised when demo knowledge ingestion is not configured safely."""


class KnowledgeRetrievalError(KnowledgeBaseError):
    """Base class for knowledge retrieval errors."""


class KnowledgeRetrievalUnavailableError(KnowledgeRetrievalError):
    """Raised when embedding or vector search providers are unavailable."""


class KnowledgeDocumentNotFoundError(KnowledgeRetrievalError):
    """Raised when a requested knowledge document is not in the catalog."""
