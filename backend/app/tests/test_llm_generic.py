"""Real-provider contracts using injected test-only transports (no live inference)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.definitions import AgentDefinition
from app.llm.clients.http import HTTPResponse
from app.llm.contracts import LLMErrorCategory
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.factory import SettingsLLMClientFactory, create_llm_client
from app.llm.service import LLMService
from app.llm.settings import LLMSettings


class Input(BaseModel):
    text: str


class Output(BaseModel):
    summary: str


AGENT = AgentDefinition(
    id="summarize",
    version="1",
    name="Summarizer",
    responsibility="Summarize supplied text",
    instructions="Summarize faithfully",
    input_schema=Input,
    output_schema=Output,
)


class Transport:
    def __init__(self, responses: list[HTTPResponse]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    async def post_json(self, **kwargs: Any) -> HTTPResponse:
        self.requests.append(kwargs)
        return self.responses.pop(0)


def response(content: str) -> HTTPResponse:
    return HTTPResponse(
        status_code=200,
        payload={
            "model": "operator-model",
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        },
    )


def settings(**overrides: Any) -> LLMSettings:
    return LLMSettings(
        **{
            "provider": "openai_compatible",
            "model": "operator-model",
            "openai_compatible_base_url": "http://model:8000/v1",
            **overrides,
        }
    )


async def test_typed_invocation_reserves_each_dispatch_and_retries_transient_only() -> (
    None
):
    transport = Transport(
        [HTTPResponse(status_code=429), response('{"summary":"actual fixture result"}')]
    )
    service = LLMService(
        settings=settings(),
        client_factory=SettingsLLMClientFactory(transport=transport),
        sleep=lambda _: no_wait(),
    )
    reservations = []

    async def reserve() -> None:
        reservations.append(1)

    output, metadata = await service.invoke(
        AGENT, {"text": "user supplied content"}, reserve
    )
    assert output == {"summary": "actual fixture result"}
    assert len(reservations) == len(transport.requests) == 2
    assert metadata["attempt_count"] == 2 and metadata["usage"] is None
    assert transport.requests[0]["url"] == "http://model:8000/v1/chat/completions"
    assert "Authorization" not in transport.requests[0]["headers"]
    assert (
        "user supplied content"
        in transport.requests[0]["payload"]["messages"][1]["content"]
    )


async def no_wait() -> None:
    pass


@pytest.mark.parametrize(
    "bad_response",
    [
        response("not-json"),
        response('{"wrong":"secret response"}'),
        HTTPResponse(status_code=401),
    ],
)
async def test_invalid_output_or_auth_does_not_retry_or_return_success(
    bad_response: HTTPResponse,
) -> None:
    transport = Transport([bad_response])
    service = LLMService(
        settings=settings(),
        client_factory=SettingsLLMClientFactory(transport=transport),
    )

    async def reserve() -> None:
        pass

    with pytest.raises(LLMProviderError) as exc:
        await service.invoke(AGENT, {"text": "secret input"}, reserve)
    assert exc.value.category in {
        LLMErrorCategory.INVALID_RESPONSE,
        LLMErrorCategory.AUTHENTICATION,
    }
    assert len(transport.requests) == 1
    assert "secret" not in str(exc.value.safe_details())


async def test_budget_refusal_prevents_network_call() -> None:
    transport = Transport([])
    service = LLMService(
        settings=settings(),
        client_factory=SettingsLLMClientFactory(transport=transport),
    )

    async def reserve() -> None:
        raise RuntimeError("budget exhausted")

    with pytest.raises(RuntimeError, match="budget exhausted"):
        await service.invoke(AGENT, {"text": "content"}, reserve)
    assert not transport.requests


def test_fake_fallback_and_runtime_bypass_settings_are_rejected() -> None:
    configurations: list[dict[str, Any]] = [
        {"provider": "fake"},
        {"fallback_enabled": True},
        {"runtime_enabled": False},
    ]
    for config in configurations:
        with pytest.raises(ValidationError):
            settings(**config)


@pytest.mark.parametrize(
    "config",
    [
        {"model": ""},
        {"provider": "groq", "groq_api_key": ""},
        {"openai_compatible_base_url": "http://user:secret@model/v1"},
    ],
)
def test_missing_or_unsafe_configuration_never_selects_fixture(
    config: dict[str, Any],
) -> None:
    with pytest.raises(LLMConfigurationError):
        create_llm_client(settings(**config))


def test_profile_pins_endpoint_provider_model_but_allows_credential_rotation() -> None:
    original = LLMService(
        settings=settings(openai_compatible_api_key="first")
    ).profile_identity
    rotated = LLMService(
        settings=settings(openai_compatible_api_key="second")
    ).profile_identity
    moved = LLMService(settings=settings(model="another-model")).profile_identity
    assert original == rotated and original != moved
    assert "first" not in str(original)


def test_profile_pins_resource_limits() -> None:
    original = LLMService(settings=settings()).profile_identity
    for override in (
        {"max_output_tokens": 512},
        {"max_retries": 0},
        {"timeout_seconds": 30},
    ):
        assert LLMService(settings=settings(**override)).profile_identity != original


async def test_exhausted_transient_retries_fail_with_every_dispatch_reserved() -> None:
    transport = Transport([HTTPResponse(status_code=503) for _ in range(3)])
    service = LLMService(
        settings=settings(),
        client_factory=SettingsLLMClientFactory(transport=transport),
        sleep=lambda _: no_wait(),
    )
    reserved = 0

    async def reserve() -> None:
        nonlocal reserved
        reserved += 1

    with pytest.raises(LLMProviderError) as exc:
        await service.invoke(AGENT, {"text": "user input"}, reserve)
    assert exc.value.category == LLMErrorCategory.UNAVAILABLE
    assert reserved == len(transport.requests) == 3
