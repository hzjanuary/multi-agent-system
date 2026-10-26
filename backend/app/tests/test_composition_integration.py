"""Production provider parsing through the graph into real PostgreSQL.

Only the HTTP transport is a fixture; these tests do not perform live inference.
"""

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.definitions import load_registry
from app.llm.factory import SettingsLLMClientFactory
from app.llm.service import LLMService
from app.models import RunStatus, User
from app.runtime.service import Worker
from app.tests.db_helpers import isolated_session
from app.tests.test_llm_generic import Transport, response, settings
from app.workflows.service import RunService


@pytest.mark.parametrize(
    "content", ["not-json", '{"wrong":"secret-private-provider-body"}']
)
async def test_parser_failure_is_durable_and_stops_downstream(content: str) -> None:
    async with isolated_session() as session:
        assert session.bind is not None
        factory = async_sessionmaker(session.bind, expire_on_commit=False)
        actor = uuid4()
        session.add(
            User(id=actor, email="parser@example.invalid", hashed_password="test-only")
        )
        await session.commit()
        transport = Transport([response(content)])
        llm = LLMService(
            settings=settings(),
            client_factory=SettingsLLMClientFactory(transport=transport),
        )
        service = RunService(
            factory, load_registry(["maos_examples.text_review"]), llm.profile_identity
        )
        run = await service.create(
            actor, "text_review", "1.0.0", {"text": "private supplied input"}
        )
        await service.start(run.id, actor)
        assert await Worker(service, llm).tick()
        # RunService.get opens a new session after failure transactions have ended.
        failed = await service.get(run.id)
        assert failed.status == RunStatus.FAILED and failed.call_count == 1
        assert failed.error == {"code": "provider_invalid_response"}
        nodes = await service.nodes(run.id)
        assert len(nodes) == 1 and nodes[0].status == "FAILED"
        assert len(transport.requests) == 1 and failed.outputs == {}
        events = await service.events(run.id)
        safe = str([e.payload for e in events]) + str(failed.error)
        assert "secret-private" not in safe and "private supplied input" not in safe


async def test_two_agents_chain_validated_output_and_pause_for_human() -> None:
    async with isolated_session() as session:
        assert session.bind is not None
        factory = async_sessionmaker(session.bind, expire_on_commit=False)
        actor = uuid4()
        session.add(
            User(id=actor, email="chain@example.invalid", hashed_password="test-only")
        )
        await session.commit()
        analysis = {
            "summary": "fixture analyst summary",
            "key_points": ["fixture point"],
        }
        review = {"assessment": "fixture review", "suggestions": []}
        import json

        transport = Transport(
            [response(json.dumps(analysis)), response(json.dumps(review))]
        )
        llm = LLMService(
            settings=settings(),
            client_factory=SettingsLLMClientFactory(transport=transport),
        )
        service = RunService(
            factory, load_registry(["maos_examples.text_review"]), llm.profile_identity
        )
        run = await service.create(
            actor, "text_review", "1.0.0", {"text": "operator supplied text"}
        )
        await service.start(run.id, actor)
        assert await Worker(service, llm).tick()
        paused = await service.get(run.id)
        assert paused.status == RunStatus.WAITING_APPROVAL and paused.call_count == 2
        chained: dict[str, Any] = json.loads(
            transport.requests[1]["payload"]["messages"][1]["content"]
        )
        assert chained["text"] == "operator supplied text"
        assert chained["analysis"] == analysis
        assert "assemble" not in paused.outputs
        approval = (await service.approvals(run.id))[0]
        approved = await service.decide(
            run.id,
            approval.id,
            actor,
            "approved",
            paused.revision,
            approval.content_revision,
            approval.content_hash,
        )
        assert approved.status == RunStatus.APPROVED
        assert not await Worker(service, llm).tick()
        await service.resume(run.id, actor)
        assert await Worker(service, llm).tick()
        done = await service.get(run.id)
        assert done.status == RunStatus.COMPLETED
        assert done.final_output == {"result": {"analysis": analysis, "review": review}}
        assert len(transport.requests) == 2


async def test_config_loss_blocks_new_dispatch_but_not_idempotent_replay() -> None:
    from app.llm.errors import LLMConfigurationError

    async with isolated_session() as session:
        assert session.bind is not None
        factory = async_sessionmaker(session.bind, expire_on_commit=False)
        actor = uuid4()
        session.add(
            User(id=actor, email="replay@example.invalid", hashed_password="test-only")
        )
        await session.commit()
        ready = True

        def validate_provider() -> None:
            if not ready:
                raise LLMConfigurationError("selected provider requires configuration")

        service = RunService(
            factory,
            load_registry(["maos_examples.text_review"]),
            {"profile": "pinned"},
            provider_validator=validate_provider,
        )
        run = await service.create(
            actor,
            "text_review",
            "1.0.0",
            {"text": "replay input"},
            idempotency_key="create-key",
        )
        await service.start(run.id, actor, idempotency_key="start-key")
        ready = False
        assert (
            await service.create(
                actor,
                "text_review",
                "1.0.0",
                {"text": "replay input"},
                idempotency_key="create-key",
            )
        ).id == run.id
        assert (
            await service.start(run.id, actor, idempotency_key="start-key")
        ).id == run.id
        with pytest.raises(LLMConfigurationError):
            await service.create(actor, "text_review", "1.0.0", {"text": "new input"})
