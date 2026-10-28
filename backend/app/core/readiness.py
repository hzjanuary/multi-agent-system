"""Readiness checks query configuration/storage, never model inference."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from sqlalchemy import text

from app.cache import create_redis_cache_provider
from app.config import Settings
from app.db.session import create_database_engine
from app.definitions import load_registry
from app.schemas.health import ReadinessDependencyStatus

ReadinessCheckCallable = Callable[[], Awaitable[bool]]
EXPECTED_REVISION = "029_headless_01"


class ReadinessChecker:
    """Database/schema are required; Redis is explicitly degradable."""

    def __init__(
        self,
        settings: Settings,
        *,
        postgres_check: ReadinessCheckCallable | None = None,
        redis_check: ReadinessCheckCallable | None = None,
        configuration_check: ReadinessCheckCallable | None = None,
    ) -> None:
        self._settings = settings
        self._checks: tuple[tuple[str, bool, ReadinessCheckCallable], ...] = (
            ("postgres_schema", True, postgres_check or self._check_postgres),
            ("configuration", True, configuration_check or self._check_configuration),
            ("redis_notifications", False, redis_check or self._check_redis),
        )

    async def check_all(self) -> list[ReadinessDependencyStatus]:
        return list(
            await asyncio.gather(
                *(
                    self._run_check(name, required, check)
                    for name, required, check in self._checks
                )
            )
        )

    async def _run_check(
        self,
        name: str,
        required: bool,
        check: ReadinessCheckCallable,
    ) -> ReadinessDependencyStatus:
        started = perf_counter()
        message = "ready"
        healthy = False
        try:
            healthy = await asyncio.wait_for(
                check(), self._settings.readiness_timeout_seconds
            )
            if not healthy:
                message = "dependency or configuration is not ready"
        except TimeoutError:
            message = "readiness check timed out"
        except Exception:
            message = "dependency or configuration check failed"
        if not healthy and not required:
            message = (
                "notification delivery degraded; "
                "durable database replay remains available"
            )
        return ReadinessDependencyStatus(
            name=name,
            required=required,
            status="ok" if healthy else "failed",
            latency_ms=round((perf_counter() - started) * 1000, 2),
            message=message,
        )

    async def _check_configuration(self) -> bool:
        self._settings.llm_settings.require_provider_configuration()
        load_registry(self._settings.extension_modules)
        return True

    async def _check_postgres(self) -> bool:
        engine = create_database_engine(self._settings.database_url, echo=False)
        try:
            async with engine.connect() as connection:
                revision = (
                    await connection.execute(
                        text("SELECT version_num FROM alembic_version")
                    )
                ).scalar_one()
                marker = (
                    await connection.execute(
                        text("SELECT product FROM maos_instance WHERE id = 1")
                    )
                ).scalar_one()
                return bool(revision == EXPECTED_REVISION and marker == "headless-1")
        finally:
            await engine.dispose()

    async def _check_redis(self) -> bool:
        provider = create_redis_cache_provider(self._settings.redis_url)
        try:
            return await provider.health_check()
        finally:
            await provider.close()
