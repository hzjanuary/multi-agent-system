"""Preview-only outbound communication service foundation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.models import Workflow
from app.outbound.exceptions import (
    OutboundCommunicationDisabledError,
    OutboundCommunicationPolicyError,
    OutboundCommunicationUnavailableError,
    OutboundSendDisabledError,
)
from app.outbound.policies import validate_preview_allowed
from app.outbound.schemas import (
    OutboundCommunicationChannel,
    OutboundCommunicationPreview,
    OutboundCommunicationProvider,
    OutboundRecipient,
    safe_warning,
)

EXPLICIT_PREVIEW_KEYS: tuple[str, ...] = (
    "email_preview",
    "generated_email",
    "outbound_preview",
    "communication_preview",
    "final_response_preview",
)
EXPLICIT_PREVIEW_CONTAINERS: tuple[str, ...] = (
    "outputs",
    "runtime_context",
)
BODY_KEYS: tuple[str, ...] = (
    "body",
    "body_preview",
    "content",
    "message",
    "text",
)
SUBJECT_KEYS: tuple[str, ...] = (
    "subject",
    "subject_preview",
    "title",
)


class OutboundCommunicationService:
    """Build approved outbound communication previews only.

    This service has no send implementation, performs no network calls, writes
    no database rows, and does not generate content with LLM/RAG/Tavily. It only
    converts explicit workflow-state preview fields into a bounded schema after
    the approval/resume policy has been satisfied.
    """

    def __init__(
        self,
        *,
        enabled: bool = False,
        send_enabled: bool = False,
        provider: str = "preview",
        require_approval: bool = True,
        max_body_chars: int = 5000,
        max_subject_chars: int = 180,
        max_recipients: int = 10,
    ) -> None:
        self.enabled = enabled
        self.send_enabled = send_enabled
        self.provider = provider.strip().lower() or "preview"
        self.require_approval = require_approval
        self.max_body_chars = max(100, min(max_body_chars, 20000))
        self.max_subject_chars = max(20, min(max_subject_chars, 500))
        self.max_recipients = max(1, min(max_recipients, 50))

    def build_preview(
        self,
        workflow: Workflow,
        *,
        actor_role: str | None = None,
    ) -> OutboundCommunicationPreview:
        """Return a safe approved outbound preview for one completed workflow."""
        if not self.enabled:
            raise OutboundCommunicationDisabledError(
                "Outbound communication preview is disabled.",
            )
        if self.send_enabled:
            raise OutboundSendDisabledError(
                "Outbound sending is disabled in preview-only Sprint 1.",
            )
        provider = _provider_from_name(self.provider)
        if provider is not OutboundCommunicationProvider.PREVIEW:
            raise OutboundSendDisabledError(
                "Only the preview provider is available in Sprint 1.",
            )
        policy_warnings: tuple[str, ...] = ()
        if self.require_approval:
            policy_warnings = validate_preview_allowed(workflow)
        else:
            raise OutboundCommunicationPolicyError(
                "Outbound preview cannot bypass approval in Sprint 1.",
            )

        source_name, source_payload = _find_explicit_preview_source(workflow)
        subject = _first_text(source_payload, SUBJECT_KEYS)
        body = _first_text(source_payload, BODY_KEYS)
        if subject is None or body is None:
            raise OutboundCommunicationUnavailableError(
                "Explicit outbound preview requires subject and body.",
            )

        recipients = _recipients_from_payload(source_payload)[: self.max_recipients]
        warnings = (
            *policy_warnings,
            "Preview only; no outbound message was sent.",
            "Final customer communication remains subject to human operating policy.",
        )
        if actor_role:
            warnings = (*warnings, f"Preview requested by role: {actor_role}.")

        return OutboundCommunicationPreview(
            workflow_id=workflow.id,
            channel=OutboundCommunicationChannel.EMAIL_PREVIEW,
            provider=provider,
            subject=subject[: self.max_subject_chars],
            body=body[: self.max_body_chars],
            recipients=tuple(recipients),
            source=source_name,
            approval_status="approved_and_resumed",
            workflow_status=workflow.status,
            generated_at=datetime.now(UTC),
            warnings=tuple(safe_warning(warning) for warning in warnings),
            is_sendable=False,
            is_sent=False,
            requires_human_approval=False,
        )

    async def send_preview(self, *_args: object, **_kwargs: object) -> None:
        """Sending is intentionally impossible in Sprint 1."""
        raise OutboundSendDisabledError(
            "Outbound sending is disabled in preview-only Sprint 1.",
        )


def _find_explicit_preview_source(workflow: Workflow) -> tuple[str, Mapping[str, Any]]:
    state_payload = _mapping(workflow.state_payload)

    for key in EXPLICIT_PREVIEW_KEYS:
        value = _mapping(state_payload.get(key))
        if value:
            return key, value

    for container_key in EXPLICIT_PREVIEW_CONTAINERS:
        container = _mapping(state_payload.get(container_key))
        for key in EXPLICIT_PREVIEW_KEYS:
            value = _mapping(container.get(key))
            if value:
                return f"{container_key}.{key}", value

    email_payload = _mapping(state_payload.get("email"))
    if any(_first_text(email_payload, keys) for keys in (SUBJECT_KEYS, BODY_KEYS)):
        return "email", email_payload

    raise OutboundCommunicationUnavailableError(
        "No explicit outbound preview source exists in workflow state.",
    )


def _recipients_from_payload(payload: Mapping[str, Any]) -> list[OutboundRecipient]:
    raw_recipients = payload.get("recipients", ())
    if isinstance(raw_recipients, Mapping):
        raw_recipients = (raw_recipients,)
    if not isinstance(raw_recipients, list | tuple):
        return []

    recipients: list[OutboundRecipient] = []
    for raw_recipient in raw_recipients:
        if isinstance(raw_recipient, Mapping):
            recipients.append(OutboundRecipient.model_validate(raw_recipient))
    return recipients


def _first_text(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _provider_from_name(value: str) -> OutboundCommunicationProvider:
    try:
        return OutboundCommunicationProvider(value)
    except ValueError as exc:
        raise OutboundSendDisabledError(
            "Unsupported outbound provider for preview-only Sprint 1.",
        ) from exc


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
