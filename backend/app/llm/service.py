"""One real-provider invocation path with bounded retries and typed validation."""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from typing import Any

from app.definitions import AgentDefinition, fingerprint
from app.llm.contracts import (
    LLMChatMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMMessageRole,
    LLMResponseFormat,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.factory import LLMClientFactory, SettingsLLMClientFactory
from app.llm.output_parser import parse_structured_output
from app.llm.retry import is_retryable_llm_error
from app.llm.settings import LLMSettings

ReserveCall = Callable[[], Awaitable[None]]


def backoff_delay_seconds(attempt: int) -> float:
    return float(min(8.0, 0.5 * 2 ** min(attempt, 6)) * random.uniform(0.75, 1.0))


class LLMService:
    def __init__(
        self,
        *,
        settings: LLMSettings,
        client_factory: LLMClientFactory | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self._settings = settings
        self._client_factory = client_factory or SettingsLLMClientFactory()
        self._sleep = sleep or asyncio.sleep

    @property
    def settings(self) -> LLMSettings:
        return self._settings

    @property
    def profile_identity(self) -> dict[str, str]:
        return {
            "profile": "default",
            "provider": self.settings.provider.value,
            "model": self.settings.selected_model,
            "endpoint_hash": fingerprint(self.settings.endpoint),
            "max_output_tokens": str(self.settings.max_output_tokens),
            "max_retries": str(self.settings.max_retries),
            "timeout_seconds": str(self.settings.timeout_seconds),
        }

    def validate_ready(self) -> None:
        self.settings.require_provider_configuration()
        self._client_factory(self.settings).validate_ready()

    async def complete(
        self, request: LLMChatRequest, *, reserve_call: ReserveCall | None = None
    ) -> LLMChatResponse:
        self.validate_ready()
        if (request.provider and request.provider != self.settings.provider) or (
            request.model and request.model != self.settings.selected_model
        ):
            raise LLMConfigurationError(
                "request does not match the pinned provider profile"
            )
        request = request.model_copy(
            update={
                "provider": self.settings.provider,
                "model": self.settings.selected_model,
            }
        )
        client = self._client_factory(self.settings)
        for attempt in range(self.settings.max_retries + 1):
            # This callback reserves in PostgreSQL under the worker fencing claim.
            # It runs before every dispatch, including retries and recovered attempts.
            if reserve_call:
                await reserve_call()
            try:
                response = await client.complete(request)
                return response.model_copy(
                    update={
                        "metadata": {**response.metadata, "attempt_count": attempt + 1}
                    }
                )
            except LLMProviderError as exc:
                if attempt == self.settings.max_retries or not is_retryable_llm_error(
                    exc.category
                ):
                    raise
                retry_after = exc.details.get("retry_after_seconds")
                delay = (
                    min(8.0, max(0.0, float(retry_after)))
                    if isinstance(retry_after, (int, float))
                    else backoff_delay_seconds(attempt)
                )
                await self._sleep(delay)
            except Exception as exc:
                raise LLMProviderError(
                    "provider operation failed",
                    category=LLMErrorCategory.UNKNOWN,
                    provider=self.settings.provider,
                ) from exc
        raise AssertionError("bounded retry loop exhausted without a result")

    async def complete_json(
        self, request: LLMChatRequest, *, reserve_call: ReserveCall | None = None
    ) -> LLMChatResponse:
        return await self.complete(
            request.model_copy(
                update={
                    "response_format": LLMResponseFormat.JSON_OBJECT,
                    "structured_json": True,
                }
            ),
            reserve_call=reserve_call,
        )

    async def invoke(
        self,
        agent: AgentDefinition,
        input_value: dict[str, Any],
        reserve_call: ReserveCall,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if agent.profile != "default":
            raise LLMConfigurationError("agent profile is unavailable")
        validated = agent.input_schema.model_validate(input_value)
        instructions = (
            agent.instructions
            + "\nReturn only one JSON object conforming to this schema:\n"
            + json.dumps(agent.output_schema.model_json_schema(), separators=(",", ":"))
        )
        response = await self.complete_json(
            LLMChatRequest(
                messages=(
                    LLMChatMessage(role=LLMMessageRole.SYSTEM, content=instructions),
                    LLMChatMessage(
                        role=LLMMessageRole.USER, content=validated.model_dump_json()
                    ),
                ),
                max_tokens=min(agent.max_tokens, self.settings.max_output_tokens),
                timeout_seconds=min(
                    agent.timeout_seconds, self.settings.timeout_seconds
                ),
            ),
            reserve_call=reserve_call,
        )
        output = parse_structured_output(response, agent.output_schema)
        return output.model_dump(mode="json"), {
            "provider": response.provider.value,
            "model": response.model,
            "attempt_count": response.metadata.get("attempt_count", 1),
            "usage": response.usage.model_dump(mode="json") if response.usage else None,
        }
