"""pg_dump/pg_restore rehearsal into an empty, separately named database.

Uses installed PostgreSQL clients or explicit MAOS_TEST_POSTGRES_CONTAINER.
Both database names are unique and owned solely by this test.
"""

import asyncio
import os
import shutil
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth import hash_password
from app.definitions import load_registry
from app.models import Role, User
from app.runtime.service import Worker
from app.services import AuthService
from app.tests.test_alembic_headless import Database, database, migrate
from app.workflows.service import RunService

# pytest discovers this imported, typed fixture; it always creates a fresh DB.
__all__ = ["database"]


def client_command(program: str, url: str) -> tuple[list[str], dict[str, str]]:
    parsed = make_url(url)
    environment = {**os.environ, "PGPASSWORD": parsed.password or ""}
    container = os.getenv("MAOS_TEST_POSTGRES_CONTAINER")
    installed = None if container else shutil.which(program)
    arguments = ["--username", parsed.username or "", "--dbname", parsed.database or ""]
    if installed:
        return [
            installed,
            "--host",
            parsed.host or "",
            "--port",
            str(parsed.port or 5432),
            *arguments,
        ], environment
    if not container:
        raise RuntimeError(
            "PostgreSQL client tools required; install pg_dump/pg_restore "
            "or explicitly set MAOS_TEST_POSTGRES_CONTAINER"
        )
    return [
        "docker",
        "exec",
        "-i",
        "-e",
        "PGPASSWORD=" + (parsed.password or ""),
        container,
        program,
        "--host",
        "127.0.0.1",
        *arguments,
    ], environment


async def test_backup_restores_outputs_approval_events_and_auth(
    database: Database, tmp_path: Path
) -> None:
    source_engine, source_url = database
    result, output = await migrate(source_url)
    assert result == 0, output
    source_factory = async_sessionmaker(source_engine, expire_on_commit=False)
    principal = uuid4()
    password = "test-only-restore-password"
    async with source_factory() as session, session.begin():
        role = Role(id=uuid4(), name="operator")
        user = User(
            id=principal,
            email="restore@example.invalid",
            hashed_password=hash_password(password),
            roles=[role],
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
    async with source_factory() as session:
        source_tokens = await AuthService(session).login(
            email="restore@example.invalid", password=password
        )
    registry = load_registry(["app.tests.runtime_extensions"])
    source = RunService(source_factory, registry, {})
    finished = await source.create(
        principal, "checkpoint", "1", {"text": "persisted result"}
    )
    waiting = await source.create(
        principal, "approval", "1", {"text": "approval snapshot"}
    )
    await source.start(finished.id, principal)
    await source.start(waiting.id, principal)
    worker = Worker(source, None)
    assert await worker.tick() and await worker.tick()
    assert (await source.get(finished.id)).status == "COMPLETED"
    assert (await source.get(waiting.id)).status == "WAITING_APPROVAL"
    event_identity = [
        (event.id, event.sequence, event.event_type)
        for event in await source.events(waiting.id)
    ]
    pending = (await source.approvals(waiting.id))[0]

    command, environment = client_command("pg_dump", source_url)
    dump = await asyncio.create_subprocess_exec(
        *command,
        "--format=custom",
        "--no-owner",
        "--no-acl",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=environment,
    )
    archive, errors = await asyncio.wait_for(dump.communicate(), 30)
    assert dump.returncode == 0, errors.decode()
    archive_path = tmp_path / "headless-backup.dump"
    archive_path.write_bytes(archive)
    archive_path.chmod(0o600)
    assert archive_path.stat().st_size > 0

    target_name = "maos_restore_" + uuid4().hex
    admin = create_async_engine(
        os.environ["MAOS_TEST_DATABASE_URL"], isolation_level="AUTOCOMMIT"
    )
    target_url = (
        make_url(source_url)
        .set(database=target_name)
        .render_as_string(hide_password=False)
    )
    target_engine = create_async_engine(target_url)
    async with admin.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{target_name}"'))
    try:
        command, environment = client_command("pg_restore", target_url)
        restore = await asyncio.create_subprocess_exec(
            *command,
            "--no-owner",
            "--no-acl",
            "--exit-on-error",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=environment,
        )
        _, errors = await asyncio.wait_for(
            restore.communicate(archive_path.read_bytes()), 30
        )
        assert restore.returncode == 0, errors.decode()
        assert target_name != make_url(source_url).database
        factory = async_sessionmaker(target_engine, expire_on_commit=False)
        restored = RunService(factory, registry, {})
        assert (await restored.get(finished.id)).final_output == {
            "text": "PERSISTED RESULT!"
        }
        assert (await restored.get(waiting.id)).status == "WAITING_APPROVAL"
        assert [
            (event.id, event.sequence, event.event_type)
            for event in await restored.events(waiting.id)
        ] == event_identity
        request = (await restored.approvals(waiting.id))[0]
        assert request.id == pending.id and request.content_hash == pending.content_hash
        assert (
            request.content == {"text": "APPROVAL SNAPSHOT"}
            and request.decision is None
        )
        async with factory() as session:
            auth = AuthService(session)
            identity = await auth.get_current_user(source_tokens.access_token)
            assert identity.id == principal and [
                role.name for role in identity.roles
            ] == ["operator"]
            rotated = await auth.refresh(source_tokens.refresh_token)
            assert rotated.refresh_token != source_tokens.refresh_token
        async with factory() as session:
            assert (
                await AuthService(session).login(
                    email="restore@example.invalid", password=password
                )
            ).access_token
        current = await restored.get(waiting.id)
        await restored.decide(
            waiting.id,
            request.id,
            principal,
            "approved",
            current.revision,
            request.content_revision,
            request.content_hash,
        )
        await restored.resume(waiting.id, principal)
        assert await Worker(restored, None).tick()
        assert (await restored.get(waiting.id)).final_output == {
            "text": "APPROVAL SNAPSHOT!"
        }
        # The source remains paused and unchanged after operating the restored copy.
        assert (await source.get(waiting.id)).status == "WAITING_APPROVAL"
    finally:
        await target_engine.dispose()
        async with admin.connect() as conn:
            await conn.execute(text(f'DROP DATABASE "{target_name}"'))
        await admin.dispose()
