"""Tests for SPEC-010 explicit demo seed CLI orchestration."""

from __future__ import annotations

from typing import Any, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.seed import main, run_demo_seed
from app.demo.user_seed import DemoUserSeedResult
from app.demo.workflow_seed import DemoWorkflowSeedResult


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeSessionContext:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> AsyncSession:
        return cast(AsyncSession, self.session)

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        return None


class FakeSessionFactory:
    def __init__(self) -> None:
        self.session = FakeSession()

    def __call__(self) -> FakeSessionContext:
        return FakeSessionContext(self.session)


@pytest.mark.asyncio
async def test_run_demo_seed_commits_once_after_seed_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_user_seed(session: AsyncSession) -> DemoUserSeedResult:
        calls.append("users")
        return DemoUserSeedResult(roles_created=6, users_created=6)

    async def fake_workflow_seed(session: AsyncSession) -> DemoWorkflowSeedResult:
        calls.append("workflows")
        return DemoWorkflowSeedResult(workflows_created=3, events_created=5)

    monkeypatch.setattr("app.demo.seed.seed_demo_roles_and_users", fake_user_seed)
    monkeypatch.setattr(
        "app.demo.seed.seed_demo_workflows_and_events",
        fake_workflow_seed,
    )
    factory = FakeSessionFactory()

    summary = await run_demo_seed(session_factory=factory)

    assert calls == ["users", "workflows"]
    assert factory.session.commits == 1
    assert factory.session.rollbacks == 0
    assert summary.committed is True
    assert summary.user_seed.users_created == 6
    assert summary.workflow_seed.workflows_created == 3


@pytest.mark.asyncio
async def test_run_demo_seed_rolls_back_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_user_seed(session: AsyncSession) -> DemoUserSeedResult:
        return DemoUserSeedResult(roles_reused=6, users_reused=6)

    async def fail_workflow_seed(session: AsyncSession) -> DemoWorkflowSeedResult:
        raise RuntimeError("seed failure")

    monkeypatch.setattr("app.demo.seed.seed_demo_roles_and_users", fake_user_seed)
    monkeypatch.setattr(
        "app.demo.seed.seed_demo_workflows_and_events",
        fail_workflow_seed,
    )
    factory = FakeSessionFactory()

    with pytest.raises(RuntimeError, match="seed failure"):
        await run_demo_seed(session_factory=factory)

    assert factory.session.commits == 0
    assert factory.session.rollbacks == 1


@pytest.mark.asyncio
async def test_run_demo_seed_dry_run_rolls_back_without_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_user_seed(session: AsyncSession) -> DemoUserSeedResult:
        return DemoUserSeedResult(roles_reused=6, users_reused=6)

    async def fake_workflow_seed(session: AsyncSession) -> DemoWorkflowSeedResult:
        return DemoWorkflowSeedResult(workflows_reused=3, events_reused=5)

    monkeypatch.setattr("app.demo.seed.seed_demo_roles_and_users", fake_user_seed)
    monkeypatch.setattr(
        "app.demo.seed.seed_demo_workflows_and_events",
        fake_workflow_seed,
    )
    factory = FakeSessionFactory()

    summary = await run_demo_seed(session_factory=factory, dry_run=True)

    assert factory.session.commits == 0
    assert factory.session.rollbacks == 1
    assert summary.dry_run is True
    assert summary.committed is False


def test_cli_refuses_mutating_seed_without_confirmation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    assert "--confirm-local-demo" in capsys.readouterr().err


def test_cli_json_output_with_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run_cli(*, dry_run: bool) -> Any:
        return _summary(dry_run=dry_run)

    monkeypatch.setattr("app.demo.seed._run_cli", fake_run_cli)

    exit_code = main(["--confirm-local-demo", "--json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"committed":true' in output
    assert "hashed_password" not in output


def test_cli_import_does_not_auto_run() -> None:
    import app.demo.seed as seed_module

    assert callable(seed_module.main)


def _summary(*, dry_run: bool) -> Any:
    from app.demo.seed import DemoSeedSummary

    return DemoSeedSummary(
        demo_only_warning="LOCAL DEMO DATA ONLY - do not use as production seed data.",
        dry_run=dry_run,
        committed=not dry_run,
        user_seed=DemoUserSeedResult(
            roles_created=6,
            users_created=6,
            role_assignments_created=6,
        ),
        workflow_seed=DemoWorkflowSeedResult(
            workflows_created=3,
            events_created=5,
        ),
    )
