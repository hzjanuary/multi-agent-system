"""LLM retry and fallback classification helpers."""

from __future__ import annotations

from app.llm.contracts import LLMErrorCategory

RETRYABLE_ERROR_CATEGORIES: frozenset[LLMErrorCategory] = frozenset(
    {
        LLMErrorCategory.TIMEOUT,
        LLMErrorCategory.UNAVAILABLE,
        LLMErrorCategory.RATE_LIMIT,
    },
)

NON_RETRYABLE_ERROR_CATEGORIES: frozenset[LLMErrorCategory] = frozenset(
    {
        LLMErrorCategory.CONFIGURATION,
        LLMErrorCategory.AUTHENTICATION,
        LLMErrorCategory.INVALID_RESPONSE,
        LLMErrorCategory.SAFETY,
        LLMErrorCategory.INVALID_REQUEST,
        LLMErrorCategory.CANCELLATION,
    },
)


def is_retryable_llm_error(category: LLMErrorCategory) -> bool:
    """Return whether the category is safe to retry."""
    return category in RETRYABLE_ERROR_CATEGORIES


def is_fallback_eligible_llm_error(category: LLMErrorCategory) -> bool:
    """Return whether a failure can use configured fallback behavior."""
    return category in RETRYABLE_ERROR_CATEGORIES
