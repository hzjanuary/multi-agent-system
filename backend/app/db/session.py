"""Async SQLAlchemy engine and session setup."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

AsyncSessionFactory = async_sessionmaker[AsyncSession]


def create_database_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async SQLAlchemy engine from a database URL."""
    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        hide_parameters=True,
    )


def create_session_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    """Create an async session factory bound to the given engine."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@lru_cache
def get_database_engine() -> AsyncEngine:
    """Return the process-wide async database engine."""
    settings = get_settings()
    return create_database_engine(
        settings.database_url,
        echo=settings.debug,
    )


@lru_cache
def get_session_factory() -> AsyncSessionFactory:
    """Return the process-wide async session factory."""
    return create_session_factory(get_database_engine())


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for request-scoped dependency injection."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def dispose_database_engine() -> None:
    """Dispose the cached database engine and clear database dependency caches."""
    await get_database_engine().dispose()
    get_session_factory.cache_clear()
    get_database_engine.cache_clear()
