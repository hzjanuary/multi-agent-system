"""JWT token utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import jwt
from jwt import PyJWTError
from pydantic import BaseModel, ValidationError

from app.config import get_settings

TokenType = Literal["access", "refresh"]


class TokenDecodeError(ValueError):
    """Raised when a JWT cannot be decoded into a valid token payload."""


class TokenPayload(BaseModel):
    """Structured JWT payload used by authentication utilities."""

    sub: str
    token_type: TokenType
    exp: datetime
    iat: datetime


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(UTC)


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for a subject."""
    settings = get_settings()
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token for a subject."""
    settings = get_settings()
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    """Create a signed JWT with the standard auth payload claims."""
    settings = get_settings()
    issued_at = utc_now()
    expires_at = issued_at + expires_delta
    payload: dict[str, object] = {
        "sub": subject,
        "jti": str(uuid4()),
        "token_type": token_type,
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(
    token: str,
    expected_token_type: str | None = None,
) -> TokenPayload:
    """Decode and validate a signed JWT payload."""
    settings = get_settings()
    try:
        decoded_payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        token_payload = TokenPayload.model_validate(
            normalize_datetime_claims(decoded_payload),
        )
    except (PyJWTError, TypeError, ValidationError) as error:
        raise TokenDecodeError("Invalid token") from error

    if (
        expected_token_type is not None
        and token_payload.token_type != expected_token_type
    ):
        raise TokenDecodeError("Unexpected token type")

    return token_payload


def verify_token(
    token: str,
    expected_token_type: str | None = None,
) -> TokenPayload | None:
    """Decode a JWT and return None when validation fails."""
    try:
        return decode_token(token, expected_token_type=expected_token_type)
    except TokenDecodeError:
        return None


def normalize_datetime_claims(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert numeric JWT datetime claims into timezone-aware datetimes."""
    normalized_payload = dict(payload)
    for claim in ("exp", "iat"):
        claim_value = normalized_payload.get(claim)
        if isinstance(claim_value, int | float):
            normalized_payload[claim] = datetime.fromtimestamp(claim_value, UTC)
    return normalized_payload
