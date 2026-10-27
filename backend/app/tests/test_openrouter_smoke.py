"""Offline proof of the production OpenRouter boundary; no generation network."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.llm.clients import OpenRouterLLMClient
from app.llm.clients.http import (
    HTTPResponse,
    HTTPTimeoutError,
    HTTPXAsyncJSONHTTPTransport,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.factory import SettingsLLMClientFactory
from app.llm.provider_preferences import OpenRouterProviderPreferences
from app.llm.service import LLMService
from app.llm.settings import LLMSettings
from app.tests.test_llm_generic import AGENT, Transport
from app.tests.test_llm_provider_clients import chat_request

MODEL = "google/gemma-4-31b-it:free"
POLICY: dict[str, Any] = {
    "data_collection": "allow",
    "zdr": False,
    "allow_fallbacks": False,
    "require_parameters": True,
    "only": ["google-ai-studio"],
    "max_price": {"prompt": 0, "completion": 0, "request": 0},
}


def configuration(**overrides: Any) -> LLMSettings:
    return LLMSettings(
        **{
            "provider": "openrouter",
            "model": MODEL,
            "openrouter_api_key": "test-only-key",
            "max_retries": 0,
            "max_output_tokens": 1024,
            "openrouter_provider_preferences": POLICY,
            **overrides,
        }
    )


async def test_serialized_request_pins_free_route_and_retains_output_contract() -> None:
    transport = Transport(
        [
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "generation-123",
                    "model": MODEL,
                    "provider": "Google AI Studio",
                    "choices": [
                        {"message": {"content": '{"summary":"actual result"}'}}
                    ],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 8, "cost": 0},
                },
            )
        ]
    )
    service = LLMService(
        settings=configuration(),
        client_factory=SettingsLLMClientFactory(transport=transport),
    )
    reserved = 0

    async def reserve() -> None:
        nonlocal reserved
        assert not transport.requests
        reserved += 1

    output, evidence = await service.invoke(
        AGENT, {"text": "private test text"}, reserve
    )
    request = transport.requests[0]
    payload = json.loads(json.dumps(request["payload"]))
    assert request["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert payload["provider"] == POLICY
    assert payload["model"] == MODEL and payload["max_tokens"] == 1024
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["stream"] is False and payload["plugins"] == []
    assert not {"models", "tools", "web_search_options", "reasoning"} & payload.keys()
    assert '"summary"' in payload["messages"][0]["content"]
    assert request["headers"]["X-Request-ID"]
    assert reserved == len(transport.requests) == 1
    assert output == {"summary": "actual result"}
    assert evidence["request_id"] == "generation-123"
    assert evidence["provider_route"] == "Google AI Studio"
    assert evidence["reported_cost"] == 0 and evidence["cost_currency"] == "USD"
    assert "test-only-key" not in str(evidence)


@pytest.mark.parametrize("failure", [429, 503, "timeout", "invalid"])
async def test_failure_consumes_one_reservation_without_retry_or_repair(
    failure: int | str,
) -> None:
    class FailingTransport:
        calls = 0

        async def post_json(self, **kwargs: Any) -> HTTPResponse:
            self.calls += 1
            if failure == "timeout":
                raise HTTPTimeoutError("uncertain outcome")
            if failure == "invalid":
                return HTTPResponse(
                    status_code=200,
                    payload={
                        "choices": [{"message": {"content": '{"wrong":"field"}'}}]
                    },
                )
            return HTTPResponse(status_code=int(failure))

    transport = FailingTransport()
    service = LLMService(
        settings=configuration(),
        client_factory=SettingsLLMClientFactory(transport=transport),
    )
    reservations = 0

    async def reserve() -> None:
        nonlocal reservations
        reservations += 1
        assert transport.calls == 0

    with pytest.raises(LLMProviderError):
        await service.invoke(AGENT, {"text": "non-sensitive"}, reserve)
    assert reservations == transport.calls == 1


async def test_missing_key_prevents_reservation_and_generation() -> None:
    transport = Transport([])
    service = LLMService(
        settings=configuration(openrouter_api_key=""),
        client_factory=SettingsLLMClientFactory(transport=transport),
    )

    async def reserve() -> None:
        pytest.fail("missing credentials must fail before reservation")

    with pytest.raises(LLMConfigurationError, match="API key"):
        await service.invoke(AGENT, {"text": "text"}, reserve)
    assert not transport.requests


def test_default_privacy_and_profile_identity_match_operator_entrypoint() -> None:
    path = Path(__file__).resolve().parents[3] / "scripts/ops/live_text_review.py"
    spec = importlib.util.spec_from_file_location("smoke_profile_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    strict = OpenRouterProviderPreferences().request_dict()
    assert strict == {
        "data_collection": "deny",
        "zdr": True,
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    for policy in ({}, POLICY):
        settings = configuration(openrouter_provider_preferences=policy)
        identity = LLMService(settings=settings).profile_identity
        assert identity == module.selected_profile(
            {
                "LLM_PROVIDER": "openrouter",
                "LLM_MODEL": MODEL,
                "LLM_MAX_RETRIES": "0",
                "OPENROUTER_PROVIDER_PREFERENCES": json.dumps(policy),
            }
        )
        assert (
            identity
            == LLMService(
                settings=settings.model_copy(update={"openrouter_api_key": "rotated"})
            ).profile_identity
        )
    assert (
        LLMService(settings=configuration()).profile_identity
        != LLMService(
            settings=configuration(openrouter_provider_preferences={})
        ).profile_identity
    )


def test_invalid_policy_is_redacted_and_never_implicitly_consents() -> None:
    with pytest.raises(ValidationError) as caught:
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://u:p@localhost/test",
            jwt_secret_key="0123456789abcdef" * 4,
            OPENROUTER_PROVIDER_PREFERENCES='{"secret":"do-not-echo"}',
        )
    assert "do-not-echo" not in str(caught.value)
    with pytest.raises(ValidationError):
        OpenRouterProviderPreferences(only=("provider", "provider"))


async def test_http_transport_explicitly_disables_connect_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.llm.clients.http as transport_module

    captured = {}

    def transport_factory(**kwargs: Any) -> None:
        captured.update(kwargs)
        raise RuntimeError("stop before HTTP client creation")

    monkeypatch.setattr(transport_module.httpx, "AsyncHTTPTransport", transport_factory)
    with pytest.raises(RuntimeError, match="stop before"):
        await HTTPXAsyncJSONHTTPTransport().post_json(
            url="https://invalid.example", headers={}, payload={}, timeout_seconds=1
        )
    assert captured == {"retries": 0}


async def test_httpx_serialization_of_production_openrouter_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.llm.clients.http as transport_module

    captured = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr(
        transport_module.httpx,
        "AsyncHTTPTransport",
        lambda **kwargs: httpx.MockTransport(handler),
    )
    client = OpenRouterLLMClient(
        api_key="test-key",
        model=MODEL,
        provider_preferences=OpenRouterProviderPreferences.model_validate(POLICY),
    )
    result = await client.complete(chat_request())
    assert len(captured) == 1
    assert str(captured[0].url) == "https://openrouter.ai/api/v1/chat/completions"
    assert json.loads(captured[0].content)["provider"] == POLICY
    assert "reported_cost" not in result.metadata
