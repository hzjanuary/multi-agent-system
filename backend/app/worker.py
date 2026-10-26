"""Single-process durable worker entry point."""

import asyncio
import sys
import time
from pathlib import Path

from app.composition import get_run_service
from app.config import get_settings
from app.core.worker_health import record_worker_heartbeat
from app.db import get_session_factory
from app.llm.service import LLMService
from app.runtime.service import Worker


def main() -> None:
    if "--healthcheck" in sys.argv:
        marker = Path("/tmp/maos-worker-heartbeat")
        raise SystemExit(
            0 if marker.exists() and time.time() - marker.stat().st_mtime < 30 else 1
        )
    settings = get_settings()
    worker = Worker(
        get_run_service(),
        LLMService(settings=settings.llm_settings),
        lease_seconds=settings.worker_lease_seconds,
        heartbeat_seconds=settings.worker_heartbeat_seconds,
    )

    async def run() -> None:
        async def heartbeat() -> None:
            while True:
                await record_worker_heartbeat(get_session_factory())
                Path("/tmp/maos-worker-heartbeat").touch()
                await asyncio.sleep(5)

        monitor = asyncio.create_task(heartbeat())
        try:
            await worker.run_forever(settings.worker_poll_seconds)
        finally:
            monitor.cancel()

    asyncio.run(run())


if __name__ == "__main__":
    main()
