"""Role-based access control dependencies."""

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Annotated, NoReturn

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models import User

CurrentUserDependency = Annotated[User, Depends(get_current_user)]
RoleDependency = Callable[[User], Awaitable[User]]


class RoleName(StrEnum):
    """Supported application role names."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


def normalize_role_name(role: str | RoleName) -> str:
    """Return the canonical string value for a role name."""
    return role.value if isinstance(role, RoleName) else role


def get_user_role_names(user: User) -> set[str]:
    """Return the case-sensitive role names assigned to a user."""
    return {role.name for role in user.roles}


def require_any_role(*allowed_roles: str | RoleName) -> RoleDependency:
    """Require the authenticated user to have at least one allowed role."""
    allowed_role_names = {normalize_role_name(role) for role in allowed_roles}

    async def dependency(current_user: CurrentUserDependency) -> User:
        user_role_names = get_user_role_names(current_user)
        if user_role_names.isdisjoint(allowed_role_names):
            raise_forbidden()
        return current_user

    return dependency


def require_all_roles(*required_roles: str | RoleName) -> RoleDependency:
    """Require the authenticated user to have every required role."""
    required_role_names = {normalize_role_name(role) for role in required_roles}

    async def dependency(current_user: CurrentUserDependency) -> User:
        user_role_names = get_user_role_names(current_user)
        if not required_role_names.issubset(user_role_names):
            raise_forbidden()
        return current_user

    return dependency


def require_roles(*allowed_roles: str | RoleName) -> RoleDependency:
    """Alias for requiring any one of the allowed roles."""
    return require_any_role(*allowed_roles)


def require_admin() -> RoleDependency:
    """Require the authenticated user to have the Admin role."""
    return require_any_role(RoleName.ADMIN)


def raise_forbidden() -> NoReturn:
    """Raise a generic HTTP 403 authorization error."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )
