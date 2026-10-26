"""Database-clock worker availability shared by operator checks and worker."""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import WorkerPresence


async def record_worker_heartbeat(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session, session.begin():
        statement = insert(WorkerPresence).values(
            id=1, heartbeat_at=func.clock_timestamp()
        )
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=[WorkerPresence.id],
                set_={"heartbeat_at": func.clock_timestamp()},
            )
        )


async def worker_available(factory: async_sessionmaker[AsyncSession]) -> bool:
    async with factory() as session:
        found = await session.scalar(
            select(WorkerPresence.id).where(
                WorkerPresence.id == 1,
                WorkerPresence.heartbeat_at
                > func.clock_timestamp() - timedelta(seconds=30),
            )
        )
        return found is not None
