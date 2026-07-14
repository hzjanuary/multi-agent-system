"""Tests for RBAC dependency behavior."""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password
from app.auth.rbac import (
    RoleName,
    get_user_role_names,
    require_all_roles,
    require_any_role,
)
from app.config import get_settings
from app.core.dependencies import provide_db_session
from app.db import create_database_engine, create_session_factory
from app.models import Role, User

AdminUserDependency = Annotated[User, Depends(require_any_role(RoleName.ADMIN))]
AdminSalesUserDependency = Annotated[
    User,
    Depends(require_all_roles(RoleName.ADMIN, RoleName.SALES)),
]


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for RBAC tests."""
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            transaction = await session.begin()
            try:
                yield session
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Provide a test-only app that exercises RBAC dependencies."""
    app = FastAPI()
    router = APIRouter()

    @router.get("/admin")
    async def admin_route(
        _user: AdminUserDependency,
    ) -> dict[str, bool]:
        return {"ok": True}

    @router.get("/admin-and-sales")
    async def admin_and_sales_route(
        _user: AdminSalesUserDependency,
    ) -> dict[str, bool]:
        return {"ok": True}

    app.include_router(router)

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[provide_db_session] = override_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


def unique_email() -> str:
    """Return a unique test email address."""
    return f"rbac-{uuid4()}@example.test"


async def create_user_with_roles(
    session: AsyncSession,
    *,
    role_names: list[str | RoleName],
    is_active: bool = True,
) -> User:
    """Create a test user with assigned roles."""
    roles: list[Role] = []
    for role in role_names:
        role_name = role.value if isinstance(role, RoleName) else role
        existing_role = await session.scalar(select(Role).where(Role.name == role_name))
        if existing_role is None:
            existing_role = Role(
                name=role_name,
                description="RBAC test role",
            )
        roles.append(existing_role)

    user = User(
        email=unique_email(),
        hashed_password=hash_password("not-used-in-rbac-tests"),
        full_name="RBAC Test User",
        is_active=is_active,
        roles=roles,
    )
    session.add(user)
    await session.flush()
    return user


def auth_headers(user: User) -> dict[str, str]:
    """Return Authorization headers for a user."""
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def test_get_user_role_names_returns_case_sensitive_role_names() -> None:
    user = User(
        email=unique_email(),
        hashed_password="not-used",
        roles=[
            Role(name=RoleName.ADMIN.value),
            Role(name="admin"),
        ],
    )

    assert get_user_role_names(user) == {"Admin", "admin"}


@pytest.mark.asyncio
async def test_allowed_role_access_passes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])

    response = await client.get("/admin", headers=auth_headers(user))

    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_denied_role_access_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.VIEWER])

    response = await client.get("/admin", headers=auth_headers(user))

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


@pytest.mark.asyncio
async def test_missing_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/admin")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_is_denied_by_auth_dependency(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(
        db_session,
        role_names=[RoleName.ADMIN],
        is_active=False,
    )

    response = await client.get("/admin", headers=auth_headers(user))

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_all_required_roles_must_be_present(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(
        db_session,
        role_names=[RoleName.ADMIN, RoleName.SALES],
    )

    response = await client.get("/admin-and-sales", headers=auth_headers(user))

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_missing_one_required_role_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=[RoleName.ADMIN])

    response = await client.get("/admin-and-sales", headers=auth_headers(user))

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_role_comparison_is_case_sensitive(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_user_with_roles(db_session, role_names=["admin"])

    response = await client.get("/admin", headers=auth_headers(user))

    assert response.status_code == 403
