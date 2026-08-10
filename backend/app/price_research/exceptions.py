"""Typed exceptions for reference price research."""

from enum import StrEnum


class PriceResearchErrorCategory(StrEnum):
    """Safe provider error categories for reference price research."""

    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN = "unknown"


class PriceResearchError(RuntimeError):
    """Base error for safe reference price research failures."""


class PriceResearchDisabledError(PriceResearchError):
    """Raised when price research is requested while disabled by settings."""


class PriceResearchProviderError(PriceResearchError):
    """Raised when a configured price research provider fails safely.

    The error category is a bounded stable identifier suitable for logs and
    events; it never carries provider payloads, prompts, keys, or secrets.
    """

    def __init__(
        self,
        message: str,
        *,
        category: PriceResearchErrorCategory = PriceResearchErrorCategory.UNKNOWN,
    ) -> None:
        super().__init__(message)
        self.category = category

    def safe_details(self) -> dict[str, str]:
        """Return bounded category metadata suitable for logs or events."""
        return {"category": self.category.value}


class PriceResearchValidationError(PriceResearchError):
    """Raised when price research input or output cannot be normalized safely."""
