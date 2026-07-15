"""Knowledge base domain exceptions."""

from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Base class for knowledge base contract and chunking errors."""


class KnowledgeChunkingError(KnowledgeBaseError):
    """Raised when document text cannot be chunked safely."""
