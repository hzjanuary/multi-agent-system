"""One composition boundary shared by API and worker."""

from dataclasses import replace
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.db import get_session_factory
from app.definitions import Registry, load_registry
from app.llm.service import LLMService
from app.streaming import publish_committed
from app.workflows.service import RunService


@lru_cache
def get_registry() -> Registry:
    settings = get_settings()
    registry = load_registry(settings.extension_modules)
    bounded = Registry()
    for definition in registry.workflows.values():
        bounded.register(
            replace(
                definition,
                max_nodes=min(definition.max_nodes, settings.max_workflow_nodes),
                max_calls=min(definition.max_calls, settings.max_provider_calls),
                max_input_bytes=min(
                    definition.max_input_bytes, settings.max_input_bytes
                ),
                max_node_output_bytes=min(
                    definition.max_node_output_bytes, settings.max_node_output_bytes
                ),
                max_total_bytes=min(definition.max_total_bytes, settings.max_run_bytes),
            )
        )
    return bounded


def get_run_service() -> RunService:
    settings = get_settings()
    llm = LLMService(settings=settings.llm_settings)

    async def notify(identity: dict[str, Any]) -> None:
        await publish_committed(settings.redis_url, identity)

    return RunService(
        get_session_factory(),
        get_registry(),
        llm.profile_identity,
        notifier=notify,
        provider_validator=llm.validate_ready,
        max_event_payload_bytes=settings.max_event_payload_bytes,
    )
