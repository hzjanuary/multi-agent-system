"""Small application dependencies; no optional business integrations."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.readiness import ReadinessChecker
from app.db import get_db_session


def provide_settings() -> Settings:
    return get_settings()


def provide_readiness_checker(
    settings: Annotated[Settings, Depends(provide_settings)],
) -> ReadinessChecker:
    return ReadinessChecker(settings)


async def provide_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session
