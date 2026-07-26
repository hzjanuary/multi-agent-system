"""Typed outbound communication errors."""

from __future__ import annotations


class OutboundCommunicationError(Exception):
    """Base error for preview-only outbound communication."""


class OutboundCommunicationDisabledError(OutboundCommunicationError):
    """Raised when outbound communication preview generation is disabled."""


class OutboundCommunicationPolicyError(OutboundCommunicationError):
    """Raised when approval/resume policy does not allow a preview."""


class OutboundCommunicationUnavailableError(OutboundCommunicationError):
    """Raised when explicit preview source content is unavailable."""


class OutboundSendDisabledError(OutboundCommunicationError):
    """Raised for any attempted send path in the preview-only sprint."""
