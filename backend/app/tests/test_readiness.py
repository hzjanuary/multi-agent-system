"""Readiness separates required state from optional notification delivery."""

import asyncio
from typing import Any

import pytest

from app.config import Settings
from app.core.readiness import ReadinessChecker


async def healthy() -> bool:
    return True


async def unhealthy() -> bool:
    return False


async def raises_secret() -> bool:
    raise RuntimeError("postgresql://private:secret-value@host/db")


def config(**kwargs: Any) -> Settings:
    return Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://test:test@localhost/test",
        jwt_secret_key="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        **kwargs,
    )


@pytest.mark.asyncio
async def test_redis_loss_is_visible_but_does_not_block_storage() -> None:
    checker = ReadinessChecker(
        config(),
        postgres_check=healthy,
        configuration_check=healthy,
        redis_check=unhealthy,
    )
    checks = await checker.check_all()
    assert [c.name for c in checks] == [
        "postgres_schema",
        "configuration",
        "redis_notifications",
    ]
    assert all(c.status == "ok" for c in checks if c.required)
    redis = checks[-1]
    assert redis.status == "failed" and redis.required is False
    assert "degraded" in (redis.message or "")


@pytest.mark.asyncio
async def test_missing_schema_blocks_readiness_and_never_leaks_errors() -> None:
    checks = await ReadinessChecker(
        config(),
        postgres_check=raises_secret,
        configuration_check=healthy,
        redis_check=healthy,
    ).check_all()
    assert checks[0].required and checks[0].status == "failed"
    assert "private" not in checks[0].model_dump_json()
    assert "secret-value" not in checks[0].model_dump_json()


@pytest.mark.asyncio
async def test_missing_model_is_not_ready_without_any_model_call() -> None:
    checks = await ReadinessChecker(
        config(), postgres_check=healthy, redis_check=healthy
    ).check_all()
    assert checks[1].required and checks[1].status == "failed"


@pytest.mark.asyncio
async def test_health_checks_have_bounded_timeouts() -> None:
    async def blocked() -> bool:
        await asyncio.sleep(1)
        return True

    checks = await ReadinessChecker(
        config(readiness_timeout_seconds=0.1),
        postgres_check=blocked,
        configuration_check=healthy,
        redis_check=healthy,
    ).check_all()
    assert checks[0].status == "failed"
    assert checks[0].message == "readiness check timed out"
