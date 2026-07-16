"""Safe observability helpers for logs, metrics, and payload summaries."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any

SENSITIVE_KEY_MARKERS: tuple[str, ...] = (
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "jwt",
    "provider_payload",
    "raw_provider_payload",
    "raw_prompt",
    "raw_document",
    "chain_of_thought",
    "embedding",
    "vector_payload",
)

REDACTED_VALUE = "[REDACTED]"
TRUNCATED_SUFFIX = "...[truncated]"
DEFAULT_MAX_STRING_LENGTH = 500
DEFAULT_MAX_COLLECTION_ITEMS = 50


def is_sensitive_key(key: str) -> bool:
    """Return whether a key name should be redacted from observability output."""
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_KEY_MARKERS)


def redact_value(
    value: Any,
    *,
    key: str | None = None,
    max_string_length: int = DEFAULT_MAX_STRING_LENGTH,
    max_collection_items: int = DEFAULT_MAX_COLLECTION_ITEMS,
) -> Any:
    """Return a JSON-safe redacted copy of a value.

    Sensitive dictionary keys are masked recursively. Non-sensitive strings and
    collections are bounded so logs and metrics payloads cannot grow without
    limit.
    """
    if key is not None and is_sensitive_key(key):
        return REDACTED_VALUE

    if isinstance(value, Mapping):
        return {
            str(item_key): redact_value(
                item_value,
                key=str(item_key),
                max_string_length=max_string_length,
                max_collection_items=max_collection_items,
            )
            for item_key, item_value in list(value.items())[:max_collection_items]
        }

    if isinstance(value, str):
        return bound_string(value, max_length=max_string_length)

    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray | str):
        return [
            redact_value(
                item,
                max_string_length=max_string_length,
                max_collection_items=max_collection_items,
            )
            for item in list(value)[:max_collection_items]
        ]

    return value


def bound_string(value: str, *, max_length: int = DEFAULT_MAX_STRING_LENGTH) -> str:
    """Return a string bounded to a deterministic maximum length."""
    if len(value) <= max_length:
        return value
    suffix_length = len(TRUNCATED_SUFFIX)
    if max_length <= suffix_length:
        return TRUNCATED_SUFFIX[:max_length]
    return f"{value[: max_length - suffix_length]}{TRUNCATED_SUFFIX}"


def redacted_log_event(
    _logger: Any,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> Mapping[str, Any]:
    """Structlog processor that redacts sensitive event fields."""
    return dict(redact_value(event_dict))


__all__ = [
    "DEFAULT_MAX_COLLECTION_ITEMS",
    "DEFAULT_MAX_STRING_LENGTH",
    "REDACTED_VALUE",
    "SENSITIVE_KEY_MARKERS",
    "bound_string",
    "is_sensitive_key",
    "redact_value",
    "redacted_log_event",
]
