"""Actual PostgreSQL locking, restart, checkpoint and approval proof.

MAOS_TEST_DATABASE_URL must name an explicitly disposable test database.
"""

import asyncio
import os
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.definitions import AgentDefinition, load_registry
from app.models import Job, Run, RunEvent, RunStatus, User
from app.runtime.service import Worker
from app.workflows.service import RunError, RunService

Storage = tuple[RunService, UUID, str, str]


@pytest.fixture
async def storage() -> AsyncIterator[Storage]:
    url = os.getenv("MAOS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("explicit disposable PostgreSQL database not configured")
    schema = "maos_test_" + uuid4().hex
    admin = create_async_engine(url)
    async with admin.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}}
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    user_id = uuid4()
    async with factory() as session, session.begin():
        session.add(
            User(
                id=user_id,
                email="operator@example.invalid",
                hashed_password="test-only",
                is_active=True,
                is_superuser=False,
            )
        )
    registry = load_registry(["app.tests.runtime_extensions"])
    service = RunService(factory, registry, {})
    yield service, user_id, url, schema
    await engine.dispose()
    async with admin.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    await admin.dispose()


async def create(
    storage: Storage, workflow: str = "checkpoint", value: dict[str, Any] | None = None
) -> Run:
    service, principal, *_ = storage
    run = await service.create(
        principal, workflow, "1", value or {"text": "user input"}
    )
    await service.start(run.id, principal)
    return run


async def test_two_unrelated_workflows_one_graph(storage: Storage) -> None:
    service, *_ = storage
    one = await create(storage)
    two = await create(storage, "arithmetic", {"value": 21})
    worker = Worker(service, None)
    assert await worker.tick() and await worker.tick()
    assert (await service.get(one.id)).final_output == {"text": "USER INPUT!"}
    assert (await service.get(two.id)).final_output == {"value": 42}
    assert len(await service.nodes(one.id)) == 2
    assert len(await service.nodes(two.id)) == 1


async def test_concurrent_start_claim_and_idempotency(storage: Storage) -> None:
    service, actor, *_ = storage
    run = await service.create(actor, "checkpoint", "1", {"text": "a"}, "create-key")
    same = await service.create(actor, "checkpoint", "1", {"text": "a"}, "create-key")
    assert same.id == run.id
    with pytest.raises(RunError, match="idempotency_conflict"):
        await service.create(actor, "checkpoint", "1", {"text": "b"}, "create-key")
    outcomes = await asyncio.gather(
        service.start(run.id, actor, "start-key"),
        service.start(run.id, actor, "start-key"),
    )
    assert all(outcome.id == run.id for outcome in outcomes)
    another = await service.create(actor, "checkpoint", "1", {"text": "a"})
    with pytest.raises(RunError, match="idempotency_conflict"):
        await service.start(another.id, actor, "start-key")
    claims = await asyncio.gather(
        Worker(service, None).claim(), Worker(service, None).claim()
    )
    assert sum(claim is not None for claim in claims) == 1
    async with service.session_factory() as session:
        assert (
            await session.scalar(
                select(func.count()).select_from(Job).where(Job.run_id == run.id)
            )
            == 1
        )


async def test_concurrent_creation_key_is_atomic(storage: Storage) -> None:
    service, actor, *_ = storage
    outcomes = await asyncio.gather(
        *(
            service.create(actor, "checkpoint", "1", {"text": "a"}, "same-key")
            for _ in range(4)
        )
    )
    assert len({run.id for run in outcomes}) == 1
    assert len(await service.list()) == 1


async def test_approval_restart_staleness_explicit_resume_and_race(
    storage: Storage,
) -> None:
    service, actor, *_ = storage
    run = await create(storage, "approval")
    await Worker(service, None).tick()
    paused = await service.get(run.id)
    assert paused.status == RunStatus.WAITING_APPROVAL
    approval = (await service.approvals(run.id))[0]
    with pytest.raises(RunError, match="stale_approval"):
        await service.decide(
            run.id,
            approval.id,
            actor,
            "approved",
            paused.revision - 1,
            approval.content_revision,
            approval.content_hash,
        )

    async def decide(decision: str) -> Run:
        return await service.decide(
            run.id,
            approval.id,
            actor,
            decision,
            paused.revision,
            approval.content_revision,
            approval.content_hash,
        )

    outcomes = await asyncio.gather(
        decide("approved"), decide("rejected"), return_exceptions=True
    )
    assert sum(not isinstance(outcome, Exception) for outcome in outcomes) == 1
    winner = await service.get(run.id)
    assert not await Worker(service, None).tick()
    assert "boundary" not in winner.outputs
    if winner.status == RunStatus.APPROVED:
        # Fresh service/worker instances load the persisted approval/checkpoint.
        restarted = RunService(service.session_factory, service.registry, {})
        await restarted.resume(run.id, actor)
        await Worker(restarted, None).tick()
        assert (await restarted.get(run.id)).final_output == {"text": "USER INPUT!"}
    else:
        with pytest.raises(RunError, match="invalid_transition"):
            await service.resume(run.id, actor)


async def test_failure_committed_and_later_nodes_not_run(storage: Storage) -> None:
    service, actor, *_ = storage

    class InvalidProvider:
        async def invoke(
            self,
            agent: AgentDefinition,
            content: dict[str, Any],
            reserve: Callable[[], Awaitable[None]],
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            await reserve()
            agent.output_schema.model_validate({"wrong": "response"})
            raise AssertionError("invalid provider output unexpectedly validated")

    service.provider_profile = {"provider": "test-only"}
    run = await create(storage, "agent")
    await Worker(service, InvalidProvider()).tick()
    observed = await RunService(
        service.session_factory, service.registry, service.provider_profile
    ).get(run.id)
    assert observed.status == RunStatus.FAILED
    assert observed.error == {"code": "invalid_output"}
    assert observed.call_count == 1
    assert [node.node_id for node in await service.nodes(run.id)] == ["agent"]
    assert (await service.events(run.id))[-1].event_type == "run.failed"


async def test_call_budget_is_reserved_and_survives_recovery(storage: Storage) -> None:
    service, *_ = storage
    service.provider_profile = {"provider": "test-only"}
    run = await create(storage, "agent")
    worker = Worker(service, None)
    claim = await worker.claim()
    assert claim is not None
    await worker.reserve_call(*claim)
    await worker.reserve_call(*claim)
    with pytest.raises(RunError, match="provider_call_limit"):
        await worker.reserve_call(*claim)
    assert (await service.get(run.id)).call_count == 2
    async with service.transaction() as session:
        await session.execute(
            text(
                "UPDATE runs SET "
                "lease_expires_at=clock_timestamp()-interval '1 second' "
                "WHERE id=:id"
            ),
            {"id": run.id},
        )
    assert await worker.reconcile() == 1
    await service.resume(run.id, storage[1])

    class ExhaustedProvider:
        async def invoke(
            self,
            agent: AgentDefinition,
            content: dict[str, Any],
            reserve: Callable[[], Awaitable[None]],
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            await reserve()
            raise AssertionError("exhausted budget must prevent provider dispatch")

    await Worker(service, ExhaustedProvider()).tick()
    failed = await service.get(run.id)
    assert failed.call_count == 2
    assert failed.status == RunStatus.FAILED
    assert failed.error == {"code": "provider_call_limit"}


async def test_cancellation_rejects_late_provider_result(storage: Storage) -> None:
    service, actor, *_ = storage
    entered, release = asyncio.Event(), asyncio.Event()

    class SlowProvider:
        async def invoke(
            self,
            agent: AgentDefinition,
            content: dict[str, Any],
            reserve: Callable[[], Awaitable[None]],
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            await reserve()
            entered.set()
            await release.wait()
            return {"text": "late"}, {}

    service.provider_profile = {"provider": "test-only"}
    run = await create(storage, "agent")
    task = asyncio.create_task(Worker(service, SlowProvider()).tick())
    await asyncio.wait_for(entered.wait(), 5)
    accepted = await service.cancel(run.id, actor)
    assert accepted.cancel_requested and accepted.status == RunStatus.RUNNING
    release.set()
    await task
    observed = await service.get(run.id)
    assert observed.status == RunStatus.CANCELLED and observed.outputs == {}
    assert observed.final_output is None
    attempts = await service.nodes(run.id)
    assert len(attempts) == 1 and attempts[0].status == "CANCELLED"


async def test_events_rollback_notifications_and_replay(storage: Storage) -> None:
    service, actor, *_ = storage
    calls = []

    async def broken_notification(identity: dict[str, Any]) -> None:
        async with service.session_factory() as session:
            event = await session.scalar(
                select(RunEvent).where(RunEvent.id == identity["event_id"])
            )
            assert event is not None
            calls.append(identity)
        raise ConnectionError("notification unavailable")

    service.notifier = broken_notification
    run = await create(storage)
    with pytest.raises(RuntimeError):
        async with service.transaction() as session:
            locked = await service._get(session, run.id, lock=True)
            service._event(session, locked, "rolled.back")
            raise RuntimeError("rollback")
    await Worker(service, None).tick()
    events = await service.events(run.id)
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert all(event.event_type != "rolled.back" for event in events)
    assert len(calls) == len(events)
    cursor = 0
    replay: list[UUID] = []
    while batch := await service.events(run.id, after_sequence=cursor, limit=2):
        replay.extend(event.id for event in batch)
        cursor = batch[-1].sequence
    assert replay == [event.id for event in events]
    assert (await service.get(run.id)).status == RunStatus.COMPLETED


async def _wait_node(
    service: RunService, run_id: UUID, process: asyncio.subprocess.Process
) -> None:
    # Cold package fingerprint validation takes ~4s on the verification host.
    # Observe the real process for up to20s; runtime leases/limits are unchanged.
    deadline = asyncio.get_running_loop().time() + 20
    while asyncio.get_running_loop().time() < deadline:
        nodes = await service.nodes(run_id)
        if any(
            node.node_id == "boundary" and node.status == "EXECUTING" for node in nodes
        ):
            return
        if process.returncode is not None:
            break
        await asyncio.sleep(0.05)
    observed = await service.get(run_id)
    attempts = await service.nodes(run_id)
    raise AssertionError(
        f"independent worker never reached fault boundary: "
        f"status={observed.status} error={observed.error} "
        f"attempts={[(row.node_id, row.status, row.error) for row in attempts]}"
    )


@pytest.mark.parametrize("unsafe", [False, True])
async def test_worker_process_loss_checkpoint_fencing_and_explicit_recovery(
    storage: Storage, unsafe: bool
) -> None:
    service, actor, url, schema = storage
    run = await create(storage, "unsafe" if unsafe else "checkpoint")
    env = {
        **os.environ,
        "MAOS_TEST_DATABASE_URL": url,
        "MAOS_TEST_SCHEMA": schema,
        "MAOS_TEST_BLOCK_NODE": "1",
    }
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app.tests.runtime_process",
        cwd=Path(__file__).parents[2],
        env=env,
    )
    try:
        await _wait_node(service, run.id, process)
    finally:
        if process.returncode is None:
            process.terminate()
        await asyncio.wait_for(process.wait(), 5)
    before = await service.get(run.id)
    assert before.outputs == {"upper": {"text": "USER INPUT"}}
    async with service.session_factory() as session, session.begin():
        await session.execute(
            text(
                "UPDATE runs SET "
                "lease_expires_at=clock_timestamp()-interval '1 second' "
                "WHERE id=:id"
            ),
            {"id": run.id},
        )
    worker = Worker(service, None)
    assert await worker.reconcile() == 1
    interrupted = await service.get(run.id)
    assert interrupted.status == RunStatus.INTERRUPTED
    # Old owner cannot persist a result after generation invalidation.
    with pytest.raises(RunError, match="stale_execution_claim"):
        async with service.transaction() as session:
            await worker._owned(session, run.id, before.generation)
    if unsafe:
        with pytest.raises(RunError, match="unsafe_resume_requires_reconciliation"):
            await service.resume(run.id, actor)
        return
    await service.resume(run.id, actor)
    env["MAOS_TEST_BLOCK_NODE"] = "0"
    second = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app.tests.runtime_process",
        cwd=Path(__file__).parents[2],
        env=env,
    )
    assert await asyncio.wait_for(second.wait(), 10) == 0
    observed = await service.get(run.id)
    assert observed.status == RunStatus.COMPLETED
    assert observed.final_output == {"text": "USER INPUT!"}
    nodes = await service.nodes(run.id)
    assert sum(node.node_id == "upper" for node in nodes) == 1
    assert sum(node.node_id == "boundary" for node in nodes) == 2


async def test_two_sequential_approvals_keep_distinct_immutable_content(
    storage: Storage,
) -> None:
    service, actor, *_ = storage
    run = await create(storage, "two_gates")
    for expected_node, expected_content in [
        ("gate_one", "USER INPUT"),
        ("gate_two", "USER INPUT!"),
    ]:
        await Worker(service, None).tick()
        current = await service.get(run.id)
        assert current.status == RunStatus.WAITING_APPROVAL
        pending = (await service.approvals(run.id))[-1]
        assert pending.node_id == expected_node and pending.content == {
            "text": expected_content
        }
        await service.decide(
            run.id,
            pending.id,
            actor,
            "approved",
            current.revision,
            pending.content_revision,
            pending.content_hash,
        )
        assert not await Worker(service, None).tick()
        await service.resume(run.id, actor)
    await Worker(service, None).tick()
    assert (await service.get(run.id)).status == RunStatus.COMPLETED
    history = await service.approvals(run.id)
    assert len({item.id for item in history}) == 2
    assert len({item.content_hash for item in history}) == 2
    assert all(item.decision == "approved" for item in history)


async def test_definition_profile_mismatch_and_event_limit_are_honest(
    storage: Storage,
) -> None:
    service, actor, *_ = storage
    run = await service.create(actor, "checkpoint", "1", {"text": "bounded"})
    different = RunService(
        service.session_factory, service.registry, {"model": "changed"}
    )
    with pytest.raises(RunError, match="provider_profile_mismatch"):
        await different.start(run.id, actor)
    assert (await service.get(run.id)).status == RunStatus.CREATED
    service.max_event_payload_bytes = 512
    with pytest.raises(RunError, match="limit_exceeded"):
        async with service.transaction() as session:
            locked = await service._get(session, run.id, lock=True)
            service._event(session, locked, "too.large", payload={"text": "x" * 513})
    assert len(await service.events(run.id)) == 1


async def test_concurrent_unkeyed_start_has_one_winner(storage: Storage) -> None:
    service, actor, *_ = storage
    run = await service.create(actor, "checkpoint", "1", {"text": "concurrency"})
    results = await asyncio.gather(
        service.start(run.id, actor),
        service.start(run.id, actor),
        return_exceptions=True,
    )
    assert sum(not isinstance(result, Exception) for result in results) == 1
    errors = [result for result in results if isinstance(result, RunError)]
    assert len(errors) == 1 and errors[0].code == "invalid_transition"
    assert (
        sum(event.event_type == "run.queued" for event in await service.events(run.id))
        == 1
    )


async def test_committed_unsafe_output_can_finalize_after_process_loss(
    storage: Storage,
) -> None:
    service, actor, *_ = storage
    run = await create(storage, "unsafe")

    class SimulatedProcessLoss(BaseException):
        pass

    class LostBeforeFinalize(Worker):
        async def _finalize(self, run_id: UUID, generation: int) -> None:
            raise SimulatedProcessLoss()

    with pytest.raises(SimulatedProcessLoss):
        await LostBeforeFinalize(service, None).tick()
    prior = await service.nodes(run.id)
    assert len(prior) == 2 and all(node.status == "COMPLETED" for node in prior)
    async with service.transaction() as session:
        await session.execute(
            text(
                "UPDATE runs SET lease_expires_at="
                "clock_timestamp()-interval '1 second' WHERE id=:id"
            ),
            {"id": run.id},
        )
    worker = Worker(service, None)
    assert await worker.reconcile() == 1
    await service.resume(run.id, actor)
    assert await worker.tick()
    assert (await service.get(run.id)).status == RunStatus.COMPLETED
    assert [node.id for node in await service.nodes(run.id)] == [
        node.id for node in prior
    ]


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
async def test_nonfinite_input_rejected_before_database_write(
    storage: Storage, invalid: float
) -> None:
    service, actor, *_ = storage
    with pytest.raises(RunError, match="invalid_input") as caught:
        await service.create(actor, "checkpoint", "1", {"text": invalid})
    assert caught.value.status_code == 422
    assert await service.list() == []


async def test_identity_mismatch_does_not_claim_or_interrupt_queued_work(
    storage: Storage,
) -> None:
    service, actor, *_ = storage
    run = await create(storage)
    changed = RunService(
        service.session_factory, service.registry, {"model": "changed"}
    )
    assert not await Worker(changed, None).tick()
    blocked = await service.get(run.id)
    assert blocked.status == RunStatus.QUEUED
    assert blocked.owner is None and blocked.generation == 0
    assert blocked.error == {"code": "provider_profile_mismatch"}
    assert await service.nodes(run.id) == []
    # Restoring the matching installed profile honors the original durable start.
    assert await Worker(service, None).tick()
    assert (await service.get(run.id)).status == RunStatus.COMPLETED
