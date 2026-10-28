"""Operator bootstrap/config behavior using disposable storage."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.administration import provision, set_role
from app.cli import config_init
from app.models import Run, User
from app.tests.db_helpers import isolated_session


def test_configuration_without_settings_is_private_and_preserves_values(
    tmp_path: Path,
) -> None:
    env = tmp_path / ".maos" / ".env"
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "config", "init", "--output", str(env)],
        env={
            k: v
            for k, v in os.environ.items()
            if k not in ("DATABASE_URL", "JWT_SECRET_KEY")
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert str(env) in result.stdout
    assert env.stat().st_mode & 0o777 == 0o600
    assert (env.parent / "cli").stat().st_mode & 0o777 == 0o700
    values = dict(
        line.split("=", 1)
        for line in env.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )
    assert len(values["JWT_SECRET_KEY"]) >= 48
    assert values["POSTGRES_PASSWORD"] in values["DATABASE_URL"]
    assert values["MAOS_UID"] == str(os.getuid())
    assert "JWT_SECRET_KEY=" not in result.stdout
    before = env.read_text()
    config_init(env)
    assert env.read_text() == before
    assert json.loads(result.stdout)["status"] == "initialized"


async def test_explicit_bootstrap_never_regrants_or_resets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with isolated_session() as session:
        assert session.bind is not None
        factory = async_sessionmaker(session.bind, expire_on_commit=False)
        monkeypatch.setattr("app.administration.get_session_factory", lambda: factory)
        created = await provision(
            "owner@example.invalid", "a-private-strong-password", bootstrap=True
        )
        assert created["role"] == "admin"
        with pytest.raises(ValueError, match="bootstrap_refused"):
            await provision(
                "owner@example.invalid", "a-different-strong-password", bootstrap=True
            )
        with pytest.raises(ValueError, match="user_exists"):
            await provision("owner@example.invalid", "a-different-strong-password")
        async with factory() as check:
            users = (await check.scalars(select(User))).all()
            assert len(users) == 1
            from app.auth.password import verify_password

            assert verify_password(
                "a-private-strong-password", users[0].hashed_password
            )
            assert await check.scalar(select(func.count()).select_from(Run)) == 0
        with pytest.raises(ValueError, match="last_administrator"):
            await set_role("owner@example.invalid", "viewer")
        await provision(
            "second@example.invalid", "another-private-password", role="admin"
        )
        assert (await set_role("owner@example.invalid", "viewer"))["role"] == "viewer"


async def test_worker_availability_uses_database_clock_expiry() -> None:
    from datetime import timedelta

    from sqlalchemy import func, update

    from app.core.worker_health import record_worker_heartbeat, worker_available
    from app.models import WorkerPresence

    async with isolated_session() as session:
        assert session.bind is not None
        factory = async_sessionmaker(session.bind, expire_on_commit=False)
        assert not await worker_available(factory)
        await record_worker_heartbeat(factory)
        assert await worker_available(factory)
        async with factory() as check, check.begin():
            await check.execute(
                update(WorkerPresence).values(
                    heartbeat_at=func.clock_timestamp() - timedelta(seconds=31)
                )
            )
        assert not await worker_available(factory)


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("http://localhost:11434", True),
        ("http://ollama:11434", True),
        ("http://192.168.10.5:8000/v1", True),
        ("https://paid-model.example/v1", False),
        ("https://api.openai.com/v1", False),
    ],
)
def test_provider_probe_requires_enablement_for_public_endpoints(
    endpoint: str, expected: bool
) -> None:
    from app.cli import local_model_endpoint

    assert local_model_endpoint(endpoint) is expected
