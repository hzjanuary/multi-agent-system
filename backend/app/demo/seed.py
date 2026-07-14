"""Explicit local-demo seed CLI and orchestration.

This module is intentionally inert on import. Mutating seed execution requires
the caller to run ``python -m app.demo.seed --confirm-local-demo``.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import (
    AsyncSessionFactory,
    create_database_engine,
    create_session_factory,
)
from app.demo.user_seed import DemoUserSeedResult, seed_demo_roles_and_users
from app.demo.workflow_seed import (
    DemoWorkflowSeedResult,
    seed_demo_workflows_and_events,
)


class DemoSeedSummary(BaseModel):
    """Bounded summary for full local demo seed orchestration."""

    model_config = ConfigDict(frozen=True)

    demo_only_warning: str
    dry_run: bool = False
    committed: bool = False
    user_seed: DemoUserSeedResult
    workflow_seed: DemoWorkflowSeedResult


class _AsyncSessionContext(Protocol):
    async def __aenter__(self) -> AsyncSession: ...

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> object: ...


class _SessionFactory(Protocol):
    def __call__(self) -> _AsyncSessionContext: ...


async def run_demo_seed(
    *,
    session_factory: _SessionFactory | AsyncSessionFactory | None = None,
    dry_run: bool = False,
) -> DemoSeedSummary:
    """Run all demo seed helpers in one caller-owned transaction."""
    engine = None
    if session_factory is None:
        engine = create_database_engine(get_settings().database_url, echo=False)
        factory: _SessionFactory | AsyncSessionFactory = create_session_factory(engine)
    else:
        factory = session_factory

    try:
        async with factory() as session:
            try:
                user_seed = await seed_demo_roles_and_users(session)
                workflow_seed = await seed_demo_workflows_and_events(session)
                if dry_run:
                    await session.rollback()
                else:
                    await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        if engine is not None:
            await engine.dispose()

    return DemoSeedSummary(
        demo_only_warning="LOCAL DEMO DATA ONLY - do not use as production seed data.",
        dry_run=dry_run,
        committed=not dry_run,
        user_seed=user_seed,
        workflow_seed=workflow_seed,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the local-demo seed CLI parser."""
    parser = argparse.ArgumentParser(
        prog="python -m app.demo.seed",
        description="Seed local/demo users, workflows, and workflow events.",
    )
    parser.add_argument(
        "--confirm-local-demo",
        action="store_true",
        help="Required for mutating local demo seed execution.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run seed steps and rollback instead of committing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the seed summary as JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the demo seed CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.dry_run and not args.confirm_local_demo:
        parser.error("mutating seed execution requires --confirm-local-demo")

    try:
        summary = asyncio.run(_run_cli(dry_run=args.dry_run))
    except Exception as exc:  # pragma: no cover - bounded CLI failure path
        print(
            f"Demo seed failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(summary.model_dump_json())
    else:
        _print_human_summary(summary)
    return 0


async def _run_cli(*, dry_run: bool) -> DemoSeedSummary:
    return await run_demo_seed(dry_run=dry_run)


def _print_human_summary(summary: DemoSeedSummary) -> None:
    print(summary.demo_only_warning)
    print(f"Dry run: {summary.dry_run}")
    print(f"Committed: {summary.committed}")
    print("Roles:")
    print(f"  created: {summary.user_seed.roles_created}")
    print(f"  reused: {summary.user_seed.roles_reused}")
    print("Users:")
    print(f"  created: {summary.user_seed.users_created}")
    print(f"  reused: {summary.user_seed.users_reused}")
    print(f"  updated: {summary.user_seed.users_updated}")
    print(f"  role assignments created: {summary.user_seed.role_assignments_created}")
    print("Workflows:")
    print(f"  created: {summary.workflow_seed.workflows_created}")
    print(f"  reused: {summary.workflow_seed.workflows_reused}")
    print(f"  updated: {summary.workflow_seed.workflows_updated}")
    print("Events:")
    print(f"  created: {summary.workflow_seed.events_created}")
    print(f"  reused: {summary.workflow_seed.events_reused}")
    print(f"  updated: {summary.workflow_seed.events_updated}")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["DemoSeedSummary", "build_parser", "main", "run_demo_seed"]
