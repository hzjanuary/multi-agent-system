"""Independent test worker process, omitted from the runtime image."""

import asyncio
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.definitions import load_registry
from app.runtime.service import Worker
from app.workflows.service import RunService


async def main() -> None:
    engine = create_async_engine(
        os.environ["MAOS_TEST_DATABASE_URL"],
        connect_args={
            "server_settings": {"search_path": os.environ["MAOS_TEST_SCHEMA"]}
        },
    )
    registry = load_registry(["app.tests.runtime_extensions"])
    service = RunService(
        async_sessionmaker(engine, expire_on_commit=False), registry, {}
    )
    await Worker(service, None, lease_seconds=3, heartbeat_seconds=0.2).tick()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
