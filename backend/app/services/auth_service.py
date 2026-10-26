"""Argon2 authentication and database-backed refresh rotation/revocation."""

from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.models import User
from app.models.refresh_session import RefreshSession
from app.repositories import UserRepository
from app.schemas import TokenResponse


class AuthenticationError(ValueError):
    """Safe authentication failure."""


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)

    async def login(self, *, email: str, password: str) -> TokenResponse:
        user = await self.user_repository.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.hashed_password)
        ):
            raise AuthenticationError("Invalid credentials")
        tokens = await self.create_token_response(str(user.id))
        await self.session.commit()
        return tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self.verify_payload(refresh_token, expected_token_type="refresh")
        record = await self.session.scalar(
            select(RefreshSession)
            .where(
                RefreshSession.token_hash == sha256(refresh_token.encode()).hexdigest()
            )
            .with_for_update()
        )
        if (
            record is None
            or record.revoked_at is not None
            or record.expires_at <= datetime.now(UTC)
        ):
            raise AuthenticationError("Invalid token")
        user = await self.get_active_user(payload.sub)
        record.revoked_at = datetime.now(UTC)
        tokens = await self.create_token_response(str(user.id))
        await self.session.commit()
        return tokens

    async def logout(self, refresh_token: str) -> None:
        self.verify_payload(refresh_token, expected_token_type="refresh")
        record = await self.session.scalar(
            select(RefreshSession)
            .where(
                RefreshSession.token_hash == sha256(refresh_token.encode()).hexdigest()
            )
            .with_for_update()
        )
        if record is not None:
            record.revoked_at = datetime.now(UTC)
        await self.session.commit()

    async def get_current_user(self, access_token: str) -> User:
        payload = self.verify_payload(access_token, expected_token_type="access")
        return await self.get_active_user(payload.sub)

    async def create_token_response(self, subject: str) -> TokenResponse:
        refresh = create_refresh_token(subject)
        payload = self.verify_payload(refresh, expected_token_type="refresh")
        self.session.add(
            RefreshSession(
                user_id=UUID(subject),
                token_hash=sha256(refresh.encode()).hexdigest(),
                expires_at=payload.exp,
            )
        )
        return TokenResponse(
            access_token=create_access_token(subject), refresh_token=refresh
        )

    def verify_payload(self, token: str, *, expected_token_type: str) -> TokenPayload:
        payload = verify_token(token, expected_token_type=expected_token_type)
        if payload is None:
            raise AuthenticationError("Invalid token")
        return payload

    async def get_active_user(self, subject: str) -> User:
        try:
            user_id = UUID(subject)
        except ValueError as error:
            raise AuthenticationError("Invalid token") from error
        user = await self.user_repository.get_with_roles(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid token")
        return user
