"""Preview-only outbound communication foundation."""

from app.outbound.exceptions import (
    OutboundCommunicationDisabledError,
    OutboundCommunicationError,
    OutboundCommunicationPolicyError,
    OutboundCommunicationUnavailableError,
    OutboundSendDisabledError,
)
from app.outbound.policies import (
    approval_records_from_workflow,
    has_approved_decision,
    has_resume_completed,
    validate_preview_allowed,
)
from app.outbound.schemas import (
    OutboundCommunicationChannel,
    OutboundCommunicationPreview,
    OutboundCommunicationProvider,
    OutboundRecipient,
)
from app.outbound.service import OutboundCommunicationService

__all__ = [
    "OutboundCommunicationChannel",
    "OutboundCommunicationDisabledError",
    "OutboundCommunicationError",
    "OutboundCommunicationPolicyError",
    "OutboundCommunicationPreview",
    "OutboundCommunicationProvider",
    "OutboundCommunicationService",
    "OutboundCommunicationUnavailableError",
    "OutboundRecipient",
    "OutboundSendDisabledError",
    "approval_records_from_workflow",
    "has_approved_decision",
    "has_resume_completed",
    "validate_preview_allowed",
]
