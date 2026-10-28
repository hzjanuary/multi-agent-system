"""Release migration safety against disposable PostgreSQL databases."""

import asyncio
import os
import secrets
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

Database = tuple[AsyncEngine, str]


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    raw = os.getenv("MAOS_TEST_DATABASE_URL")
    if not raw:
        pytest.skip("explicit disposable PostgreSQL database not configured")
    name = "maos_migration_" + uuid4().hex
    admin = create_async_engine(raw, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(raw).set(database=name).render_as_string(hide_password=False)
    engine = create_async_engine(url)
    yield engine, url
    await engine.dispose()
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE "{name}"'))
    await admin.dispose()


async def migrate(url: str) -> tuple[int | None, str]:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "upgrade",
        "head",
        cwd=Path(__file__).parents[2],
        env={
            **os.environ,
            "DATABASE_URL": url,
            "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        },
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), 20)
    return process.returncode, stdout.decode() + stderr.decode()


async def test_fresh_migration_zero_records_and_repeat_preserves_data(
    database: Database,
) -> None:
    engine, url = database
    result, output = await migrate(url)
    assert result == 0, output
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync: inspect(sync).get_table_names())
        assert {
            "runs",
            "jobs",
            "node_executions",
            "approvals",
            "run_events",
            "refresh_sessions",
        } <= set(tables)
        for name in tables:
            if name not in {"maos_instance", "alembic_version"}:
                assert await conn.scalar(text(f'SELECT count(*) FROM "{name}"')) == 0
        assert (
            await conn.scalar(text("SELECT product FROM maos_instance")) == "headless-1"
        )
        await conn.execute(
            text(
                "INSERT INTO users "
                "(id,email,hashed_password,is_active,is_superuser,"
                "created_at,updated_at) "
                "VALUES (:id,'retained@example.invalid','test-only',"
                "true,false,now(),now())"
            ),
            {"id": uuid4()},
        )
    result, output = await migrate(url)
    assert result == 0, output
    async with engine.connect() as conn:
        assert (
            await conn.scalar(text("SELECT email FROM users"))
            == "retained@example.invalid"
        )
        assert (
            await conn.scalar(text("SELECT version_num FROM alembic_version"))
            == "029_headless_01"
        )


@pytest.mark.parametrize("legacy", [False, True])
async def test_unmarked_or_legacy_database_refused_without_mutation(
    database: Database, legacy: bool
) -> None:
    engine, url = database
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE sentinel (value text NOT NULL)"))
        await conn.execute(text("INSERT INTO sentinel VALUES ('operator data')"))
        if legacy:
            await conn.execute(
                text(
                    "CREATE TABLE alembic_version "
                    "(version_num varchar(32) PRIMARY KEY)"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO alembic_version "
                    "VALUES ('0001_create_phase_1_core_tables')"
                )
            )
        before = await conn.run_sync(lambda sync: inspect(sync).get_table_names())
    result, output = await migrate(url)
    assert result != 0 and "unmarked_or_legacy_database_refused" in output
    async with engine.connect() as conn:
        after = await conn.run_sync(lambda sync: inspect(sync).get_table_names())
        assert before == after
        assert await conn.scalar(text("SELECT value FROM sentinel")) == "operator data"
        if legacy:
            assert (
                await conn.scalar(text("SELECT version_num FROM alembic_version"))
                == "0001_create_phase_1_core_tables"
            )


@pytest.mark.parametrize(
    "fixture_sql",
    [
        "CREATE VIEW retained_view AS SELECT 42 AS value",
        "CREATE SCHEMA retained_schema",
        "CREATE SCHEMA retained_schema; "
        "CREATE TABLE retained_schema.retained_table(value int)",
        "CREATE SEQUENCE retained_sequence",
        "CREATE SCHEMA pgshadow",
        "CREATE TYPE retained_enum AS ENUM ('unchanged')",
        "CREATE FUNCTION retained_function() RETURNS int "
        "LANGUAGE SQL AS $$ SELECT 42 $$",
    ],
)
async def test_unmarked_non_table_objects_are_refused(
    database: Database, fixture_sql: str
) -> None:
    engine, url = database
    async with engine.begin() as conn:
        for statement in fixture_sql.split(";"):
            await conn.execute(text(statement))
        before = (
            await conn.execute(
                text(
                    "SELECT nspname,relname,relkind FROM pg_class c "
                    "JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE n.nspname !~ '^pg_' "
                    "AND n.nspname <> 'information_schema' "
                    "ORDER BY nspname,relname"
                )
            )
        ).all()
        namespaces_before = (
            await conn.execute(
                text("SELECT nspname FROM pg_namespace ORDER BY nspname")
            )
        ).all()
        objects_query = text(
            "SELECT 'type', n.nspname, t.typname FROM pg_type t "
            "JOIN pg_namespace n ON n.oid=t.typnamespace "
            "WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' "
            "UNION ALL SELECT 'function', n.nspname, p.proname FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' "
            "ORDER BY 1,2,3"
        )
        objects_before = (await conn.execute(objects_query)).all()
    result, output = await migrate(url)
    assert result != 0 and "unmarked_or_legacy_database_refused" in output
    async with engine.connect() as conn:
        assert objects_before == (await conn.execute(objects_query)).all()
        after = (
            await conn.execute(
                text(
                    "SELECT nspname,relname,relkind FROM pg_class c "
                    "JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE n.nspname !~ '^pg_' "
                    "AND n.nspname <> 'information_schema' "
                    "ORDER BY nspname,relname"
                )
            )
        ).all()
        assert before == after
        assert (
            namespaces_before
            == (
                await conn.execute(
                    text("SELECT nspname FROM pg_namespace ORDER BY nspname")
                )
            ).all()
        )
