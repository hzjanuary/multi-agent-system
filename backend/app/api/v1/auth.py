"""Authentication API routes."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.dependencies import provide_db_session
from app.models import User
from app.schemas import (
    CurrentUserResponse,
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    TokenResponse,
    UserProfile,
)
from app.services import AuthenticationError, AuthService

DbSessionDependency = Annotated[AsyncSession, Depends(provide_db_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: DbSessionDependency,
) -> TokenResponse:
    """Authenticate a user and return JWT tokens."""
    auth_service = AuthService(session)
    try:
        return await auth_service.login(email=payload.email, password=payload.password)
    except AuthenticationError:
        raise_invalid_credentials()


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    session: DbSessionDependency,
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    auth_service = AuthService(session)
    try:
        return await auth_service.refresh(payload.refresh_token)
    except AuthenticationError:
        raise_invalid_credentials()


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    payload: RefreshRequest, session: DbSessionDependency
) -> LogoutResponse:
    """Revoke a refresh session; access tokens expire independently."""
    try:
        await AuthService(session).logout(payload.refresh_token)
    except AuthenticationError:
        raise_invalid_credentials()
    return LogoutResponse(success=True)


@router.get("/me", response_model=CurrentUserResponse)
async def me(current_user: CurrentUserDependency) -> CurrentUserResponse:
    """Return the current authenticated user profile."""
    return CurrentUserResponse(user=UserProfile.model_validate(current_user))


def raise_invalid_credentials() -> NoReturn:
    """Raise a generic authentication failure response."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": "Invalid credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )
