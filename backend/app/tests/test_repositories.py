"""Tests for generic repository behavior."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.models import User
from app.repositories import BaseRepository, CRUDRepository


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for repository tests."""
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


def build_user(email: str | None = None) -> User:
    """Create a deterministic test user without password hashing logic."""
    unique_email = email or f"user-{uuid4()}@example.test"
    return User(
        email=unique_email,
        hashed_password="not-a-real-password-hash",
        full_name="Repository Test User",
    )


@pytest.mark.asyncio
async def test_repository_initialization(db_session: AsyncSession) -> None:
    repository = BaseRepository(db_session, User)

    assert repository.session is db_session
    assert repository.model_type is User


@pytest.mark.asyncio
async def test_crud_repository_add_get_list_update_refresh_and_delete(
    db_session: AsyncSession,
) -> None:
    repository = CRUDRepository(db_session, User)
    user = build_user()

    added_user = repository.add(user)
    await db_session.flush()

    assert added_user is user

    found_user = await repository.get(user.id)
    assert found_user is user

    users = await repository.list(limit=10, offset=0)
    assert user in users

    updated_user = repository.update_fields(user, {"full_name": "Updated User"})
    await db_session.flush()
    await repository.refresh(updated_user)

    assert updated_user.full_name == "Updated User"

    await repository.delete(user)
    await db_session.flush()

    assert await repository.get(user.id) is None


@pytest.mark.asyncio
async def test_crud_repository_list_limit_and_offset(
    db_session: AsyncSession,
) -> None:
    repository = CRUDRepository(db_session, User)
    first_user = repository.add(build_user())
    second_user = repository.add(build_user())
    await db_session.flush()

    users = await repository.list(limit=1, offset=1)

    assert len(users) == 1
    assert users[0] in [first_user, second_user]
