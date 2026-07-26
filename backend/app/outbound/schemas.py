"""Preview-only outbound communication contracts.

Outbound communication in SPEC-020 Sprint 1 is review material only. It never
sends email, never represents a sent message, and never bypasses the existing
Manager/Admin approval plus explicit resume boundary.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import WorkflowStatus

MAX_TEXT_CHARS = 1000
MAX_SUBJECT_CHARS = 500
MAX_BODY_CHARS = 20000
MAX_RECIPIENTS = 50
MAX_WARNINGS = 20
SENSITIVE_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "chain_of_thought",
    "cookie",
    "jwt",
    "password",
    "provider_payload",
    "raw_prompt",
    "raw_provider",
    "secret",
    "token",
)


class OutboundCommunicationChannel(StrEnum):
    """Supported preview channels for outbound communication."""

    EMAIL_PREVIEW = "email_preview"
    TELEGRAM_PREVIEW = "telegram_preview"
    FILE_PREVIEW = "file_preview"


class OutboundCommunicationProvider(StrEnum):
    """Supported provider identifiers for preview-only contracts."""

    PREVIEW = "preview"
    FILE = "file"
    GMAIL_FUTURE = "gmail_future"


class OutboundRecipient(BaseModel):
    """A bounded recipient descriptor for preview metadata."""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1, max_length=MAX_TEXT_CHARS)
    email: str | None = Field(default=None, min_length=1, max_length=320)
    role: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("name", "email", "role")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """Strip and validate optional recipient text."""
        return normalize_optional_safe_text(value)


class OutboundCommunicationPreview(BaseModel):
    """Approved outbound communication preview.

    This schema intentionally constrains `is_sent` and `is_sendable` to false.
    Sprint 1 creates preview contracts only; future send behavior requires a
    separate approved provider and audit implementation.
    """

    model_config = ConfigDict(frozen=True)

    workflow_id: UUID
    channel: OutboundCommunicationChannel = OutboundCommunicationChannel.EMAIL_PREVIEW
    provider: OutboundCommunicationProvider = OutboundCommunicationProvider.PREVIEW
    subject: str = Field(min_length=1, max_length=MAX_SUBJECT_CHARS)
    body: str = Field(min_length=1, max_length=MAX_BODY_CHARS)
    recipients: tuple[OutboundRecipient, ...] = Field(
        default_factory=tuple,
        max_length=MAX_RECIPIENTS,
    )
    source: str = Field(min_length=1, max_length=120)
    approval_status: str = Field(min_length=1, max_length=120)
    workflow_status: WorkflowStatus
    generated_at: datetime
    warnings: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_WARNINGS)
    is_sendable: bool = False
    is_sent: bool = False
    requires_human_approval: bool = False
    communication_label: str = Field(
        default="approved_outbound_preview",
        min_length=1,
        max_length=120,
    )

    @field_validator("subject")
    @classmethod
    def normalize_subject(cls, value: str) -> str:
        """Strip, bound, and validate preview subject."""
        return normalize_required_safe_text(value, max_chars=MAX_SUBJECT_CHARS)

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str) -> str:
        """Strip, bound, and validate preview body."""
        return normalize_required_safe_text(value, max_chars=MAX_BODY_CHARS)

    @field_validator("source", "approval_status", "communication_label")
    @classmethod
    def normalize_required_metadata(cls, value: str) -> str:
        """Strip and validate required metadata text."""
        return normalize_required_safe_text(value, max_chars=120)

    @field_validator("recipients", mode="before")
    @classmethod
    def coerce_recipients(
        cls,
        value: tuple[OutboundRecipient, ...] | list[OutboundRecipient],
    ) -> tuple[OutboundRecipient, ...] | list[OutboundRecipient]:
        """Accept list input while storing recipients immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("warnings", mode="before")
    @classmethod
    def coerce_warnings(cls, value: tuple[str, ...] | list[str]) -> object:
        """Accept list input while storing warnings immutably."""
        return tuple(value) if isinstance(value, list) else value

    @field_validator("warnings")
    @classmethod
    def normalize_warnings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Strip, bound, and de-duplicate warnings."""
        seen: set[str] = set()
        warnings: list[str] = []
        for warning in value:
            normalized = normalize_required_safe_text(warning, max_chars=MAX_TEXT_CHARS)
            lowered = normalized.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            warnings.append(normalized)
        return tuple(warnings)

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Require timezone-aware generation timestamps."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def enforce_preview_only(self) -> OutboundCommunicationPreview:
        """Prevent send-like state in Sprint 1."""
        if self.is_sent:
            raise ValueError("outbound communication preview cannot be marked sent")
        if self.is_sendable:
            raise ValueError("outbound communication preview cannot be sendable")
        if self.provider is OutboundCommunicationProvider.GMAIL_FUTURE:
            raise ValueError("gmail_future provider is reserved for a future sprint")
        return self


def normalize_required_safe_text(value: object, *, max_chars: int) -> str:
    """Return stripped safe text, rejecting sensitive markers."""
    normalized = _normalize_text(value, max_chars=max_chars)
    if not normalized:
        raise ValueError("value must not be blank")
    return normalized


def normalize_optional_safe_text(
    value: object,
    *,
    max_chars: int = MAX_TEXT_CHARS,
) -> str | None:
    """Return optional stripped safe text."""
    if value is None:
        return None
    normalized = _normalize_text(value, max_chars=max_chars)
    return normalized or None


def _normalize_text(value: object, *, max_chars: int) -> str:
    text = str(value)
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("outbound preview text contains sensitive marker")
    return text[:max_chars].strip()


def safe_warning(value: object, *, max_chars: int = MAX_TEXT_CHARS) -> str:
    """Return a bounded warning or a generic redaction warning."""
    try:
        return normalize_required_safe_text(value, max_chars=max_chars)
    except ValueError:
        return "Preview warning redacted for safety."


JsonObject = dict[str, Any]
