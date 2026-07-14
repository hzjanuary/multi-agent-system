"""Tests for SPEC-010 demo role/user seeding."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import hash_password, verify_password
from app.auth.rbac import RoleName
from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.demo import DEMO_CREDENTIALS, DEMO_USERS, seed_demo_roles_and_users
from app.models import Role, User


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for demo seed tests."""
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


@pytest.mark.asyncio
async def test_seed_demo_roles_and_users_creates_required_records(
    db_session: AsyncSession,
) -> None:
    result = await seed_demo_roles_and_users(db_session)

    role_names = await _role_names(db_session)
    users = await _demo_users(db_session)

    assert set(role_names) >= {role.value for role in RoleName}
    assert {user.email for user in users} == {user.email for user in DEMO_USERS}
    assert set(result.demo_user_emails) == {user.email for user in DEMO_USERS}
    assert set(result.role_names) == set(RoleName)


@pytest.mark.asyncio
async def test_seed_demo_users_have_expected_single_role(
    db_session: AsyncSession,
) -> None:
    await seed_demo_roles_and_users(db_session)

    users = await _demo_users(db_session)
    expected_roles_by_email = {user.email: user.role_name.value for user in DEMO_USERS}

    for user in users:
        assert [role.name for role in user.roles] == [
            expected_roles_by_email[user.email],
        ]


@pytest.mark.asyncio
async def test_seed_demo_users_hash_passwords_and_can_authenticate(
    db_session: AsyncSession,
) -> None:
    await seed_demo_roles_and_users(db_session)

    users = await _demo_users(db_session)
    credential_by_email = {
        credential.email: credential for credential in DEMO_CREDENTIALS
    }

    for user in users:
        credential = credential_by_email[user.email]
        assert user.hashed_password != credential.password
        assert verify_password(credential.password, user.hashed_password)


@pytest.mark.asyncio
async def test_seed_demo_roles_and_users_is_idempotent(
    db_session: AsyncSession,
) -> None:
    await seed_demo_roles_and_users(db_session)
    first_user_count = await _demo_user_count(db_session)
    first_role_count = await _demo_role_count(db_session)

    result = await seed_demo_roles_and_users(db_session)
    second_user_count = await _demo_user_count(db_session)
    second_role_count = await _demo_role_count(db_session)

    assert second_user_count == first_user_count
    assert second_role_count == first_role_count
    assert result.users_created == 0
    assert result.roles_created == 0
    assert result.role_assignments_created == 0
    assert result.users_reused == len(DEMO_USERS)
    assert result.roles_reused == len(RoleName)


@pytest.mark.asyncio
async def test_seed_refreshes_existing_demo_user_safely(
    db_session: AsyncSession,
) -> None:
    stale_user = User(
        email="admin@example.test",
        hashed_password=hash_password("old-demo-password"),
        full_name="Old Demo Admin",
        is_active=False,
        is_superuser=True,
    )
    db_session.add(stale_user)
    await db_session.flush()

    result = await seed_demo_roles_and_users(db_session)
    user = await _demo_user(db_session, "admin@example.test")

    assert result.users_reused >= 1
    assert result.users_updated >= 1
    assert result.passwords_refreshed >= 1
    assert user.full_name == "Demo Admin"
    assert user.is_active is True
    assert user.is_superuser is False
    assert verify_password("DemoPassword123!", user.hashed_password)
    assert [role.name for role in user.roles] == [RoleName.ADMIN.value]


@pytest.mark.asyncio
async def test_seed_does_not_delete_or_modify_non_demo_users(
    db_session: AsyncSession,
) -> None:
    role = Role(name="ExistingRole", description="Do not touch")
    non_demo_user = User(
        email="existing@example.com",
        hashed_password=hash_password("existing-password"),
        full_name="Existing User",
        is_active=True,
        roles=[role],
    )
    db_session.add(non_demo_user)
    await db_session.flush()
    original_hash = non_demo_user.hashed_password

    await seed_demo_roles_and_users(db_session)
    found_user = await _user_by_email(db_session, "existing@example.com")
    found_role = await db_session.scalar(
        select(Role).where(Role.name == "ExistingRole"),
    )

    assert found_user is non_demo_user
    assert found_user.full_name == "Existing User"
    assert found_user.hashed_password == original_hash
    assert found_role is role


@pytest.mark.asyncio
async def test_seed_function_does_not_commit(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_commit() -> None:
        raise AssertionError("seed helper must not commit")

    monkeypatch.setattr(db_session, "commit", fail_commit)

    await seed_demo_roles_and_users(db_session)


async def _role_names(session: AsyncSession) -> list[str]:
    result = await session.scalars(select(Role.name))
    return list(result.all())


async def _demo_users(session: AsyncSession) -> list[User]:
    emails = [user.email for user in DEMO_USERS]
    statement = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.email.in_(emails))
        .order_by(User.email)
    )
    result = await session.scalars(statement)
    return list(result.all())


async def _demo_user(session: AsyncSession, email: str) -> User:
    user = await _user_by_email(session, email)
    assert user is not None
    return user


async def _user_by_email(session: AsyncSession, email: str) -> User | None:
    statement = (
        select(User).options(selectinload(User.roles)).where(User.email == email)
    )
    result = await session.scalars(statement)
    return result.one_or_none()


async def _demo_user_count(session: AsyncSession) -> int:
    emails = [user.email for user in DEMO_USERS]
    count = await session.scalar(
        select(func.count()).select_from(User).where(User.email.in_(emails)),
    )
    assert count is not None
    return count


async def _demo_role_count(session: AsyncSession) -> int:
    role_names = [role.value for role in RoleName]
    count = await session.scalar(
        select(func.count()).select_from(Role).where(Role.name.in_(role_names)),
    )
    assert count is not None
    return count
