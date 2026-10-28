"""Alembic environment for async SQLAlchemy migrations."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import inspect, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.models  # noqa: F401
from alembic import context
from app.config import get_settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """Return the application database URL used by Alembic."""
    return str(get_settings().database_url)


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations through a synchronous connection facade."""
    # Guard before Alembic can create/update any schema or version table.
    # Session lock serializes two migrate commands without touching operator data.
    connection.execute(text("SELECT pg_advisory_lock(290029)"))
    tables = set(inspect(connection).get_table_names())
    # Views, materialized views, sequences and non-public schemas are user state
    # too. An otherwise table-empty database must not bypass initialization guard.
    user_relations = connection.execute(
        text(
            "SELECT count(*) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' "
            "AND c.relkind IN ('r','p','v','m','S','f')"
        )
    ).scalar()
    custom_schemas = connection.execute(
        text(
            "SELECT count(*) FROM pg_namespace WHERE nspname !~ '^pg_' "
            "AND nspname NOT IN ('public','information_schema')"
        )
    ).scalar()
    user_types = connection.execute(
        text(
            "SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace "
            "WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'"
        )
    ).scalar()
    user_functions = connection.execute(
        text(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'"
        )
    ).scalar()
    user_extensions = connection.execute(
        text("SELECT count(*) FROM pg_extension WHERE extname <> 'plpgsql'")
    ).scalar()
    if "maos_instance" not in tables and (
        user_relations
        or custom_schemas
        or user_types
        or user_functions
        or user_extensions
    ):
        raise RuntimeError("unmarked_or_legacy_database_refused")
    if tables:
        if "maos_instance" not in tables:
            raise RuntimeError("unmarked_or_legacy_database_refused")
        marker = connection.execute(
            text("SELECT product FROM maos_instance WHERE id=1")
        ).scalar()
        if marker != "headless-1" or "alembic_version" not in tables:
            raise RuntimeError("unknown_database_refused")
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()
        if revision != "029_headless_01":
            raise RuntimeError("unsupported_schema_revision")
    connection.commit()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in online async mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
