"""Tests for preview-only outbound communication schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.enums import WorkflowStatus
from app.outbound import (
    OutboundCommunicationChannel,
    OutboundCommunicationPreview,
    OutboundCommunicationProvider,
    OutboundRecipient,
)


def generated_at() -> datetime:
    """Return a stable timezone-aware timestamp."""
    return datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def preview_payload() -> dict[str, object]:
    """Return a valid outbound preview payload."""
    return {
        "workflow_id": uuid4(),
        "channel": "email_preview",
        "provider": "preview",
        "subject": " Approved quotation preview ",
        "body": " <p>Dear customer, this is preview content only.</p> ",
        "recipients": [
            {
                "name": " Customer ",
                "email": "customer@example.test",
                "role": "buyer",
            },
        ],
        "source": "email_preview",
        "approval_status": "approved_and_resumed",
        "workflow_status": WorkflowStatus.COMPLETED,
        "generated_at": generated_at(),
        "warnings": [
            " Preview only; no outbound message was sent. ",
            "Preview only; no outbound message was sent.",
        ],
    }


def test_valid_preview_schema_normalizes_safe_values() -> None:
    preview = OutboundCommunicationPreview.model_validate(preview_payload())

    assert preview.channel is OutboundCommunicationChannel.EMAIL_PREVIEW
    assert preview.provider is OutboundCommunicationProvider.PREVIEW
    assert preview.subject == "Approved quotation preview"
    assert preview.body == "Dear customer, this is preview content only."
    assert preview.recipients == (
        OutboundRecipient(
            name="Customer",
            email="customer@example.test",
            role="buyer",
        ),
    )
    assert preview.warnings == ("Preview only; no outbound message was sent.",)
    assert preview.is_sendable is False
    assert preview.is_sent is False
    assert preview.requires_human_approval is False
    assert preview.communication_label == "approved_outbound_preview"


def test_preview_rejects_is_sent_true() -> None:
    payload = preview_payload()
    payload["is_sent"] = True

    with pytest.raises(ValidationError, match="sent"):
        OutboundCommunicationPreview.model_validate(payload)


def test_preview_rejects_sendable_true() -> None:
    payload = preview_payload()
    payload["is_sendable"] = True

    with pytest.raises(ValidationError, match="sendable"):
        OutboundCommunicationPreview.model_validate(payload)


def test_preview_rejects_future_gmail_provider() -> None:
    payload = preview_payload()
    payload["provider"] = "gmail_future"

    with pytest.raises(ValidationError, match="future"):
        OutboundCommunicationPreview.model_validate(payload)


def test_preview_requires_timezone_aware_generated_at() -> None:
    payload = preview_payload()
    payload["generated_at"] = datetime(2026, 7, 26, 12, 0)

    with pytest.raises(ValidationError, match="timezone-aware"):
        OutboundCommunicationPreview.model_validate(payload)


def test_preview_rejects_sensitive_markers() -> None:
    for field in ("subject", "body"):
        payload = preview_payload()
        payload[field] = "contains api_key secret"

        with pytest.raises(ValidationError, match="sensitive"):
            OutboundCommunicationPreview.model_validate(payload)


def test_preview_rejects_sensitive_warning_and_recipient() -> None:
    payload = preview_payload()
    payload["warnings"] = ["raw_provider payload"]

    with pytest.raises(ValidationError, match="sensitive"):
        OutboundCommunicationPreview.model_validate(payload)

    payload = preview_payload()
    payload["recipients"] = [{"email": "bearer-token@example.test"}]

    with pytest.raises(ValidationError, match="sensitive"):
        OutboundCommunicationPreview.model_validate(payload)


def test_preview_public_schema_has_no_raw_payload_fields() -> None:
    preview = OutboundCommunicationPreview.model_validate(preview_payload())
    serialized_keys = set(preview.model_dump(mode="json"))

    assert "raw_prompt" not in serialized_keys
    assert "provider_payload" not in serialized_keys
    assert "chain_of_thought" not in serialized_keys
    assert "smtp_password" not in serialized_keys
