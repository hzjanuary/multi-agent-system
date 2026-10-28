"""Provider-independent LLM errors."""

from __future__ import annotations

from typing import Any

from app.llm.contracts import LLMErrorCategory, LLMProvider
from app.llm.diagnostics import ProviderDiagnostics


class LLMProviderError(Exception):
    """Base safe LLM provider exception."""

    def __init__(
        self,
        message: str,
        *,
        category: LLMErrorCategory = LLMErrorCategory.UNKNOWN,
        provider: LLMProvider | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        diagnostics: ProviderDiagnostics | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.category = category
        self.provider = provider
        self.request_id = request_id
        self.details = dict(details or {})
        self.diagnostics = diagnostics

    def safe_details(self) -> dict[str, Any]:
        """Return bounded metadata suitable for logs or events."""
        safe_details: dict[str, Any] = {"category": self.category.value}
        if self.provider is not None:
            safe_details["provider"] = self.provider.value
        if self.request_id is not None:
            safe_details["request_id"] = self.request_id
        for key in ("http_status", "retry_after_seconds", "retryable"):
            value = self.details.get(key)
            if isinstance(value, (int, float, bool)):
                safe_details[key] = value
        return safe_details


class LLMConfigurationError(LLMProviderError):
    """Raised when selected LLM provider configuration is incomplete."""

    def __init__(
        self,
        message: str,
        *,
        provider: LLMProvider | None = None,
    ) -> None:
        super().__init__(
            message,
            category=LLMErrorCategory.CONFIGURATION,
            provider=provider,
        )
