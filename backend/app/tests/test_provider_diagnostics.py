"""Safe production error extraction with test-only responses and no network."""

import json

import pytest

from app.llm.clients import OpenRouterLLMClient
from app.llm.clients.http import HTTPResponse
from app.llm.diagnostics import extract_diagnostics
from app.llm.errors import LLMProviderError
from app.llm.factory import SettingsLLMClientFactory
from app.llm.service import LLMService
from app.tests.test_llm_generic import AGENT, Transport
from app.tests.test_llm_provider_clients import chat_request
from app.tests.test_openrouter_smoke import configuration


def test_closed_diagnostics_and_id_sources_preserve_hints_without_content() -> None:
    req = chat_request()
    response = HTTPResponse(
        status_code=429,
        payload={
            "id": "gen-response",
            "error": {
                "code": 429,
                "type": "rate_limit",
                "message": "never store this",
                "metadata": {
                    "provider_name": "Google AI Studio",
                    "provider_request_id": "upstream-id",
                    "raw": json.dumps(
                        {
                            "error": {
                                "code": 429,
                                "status": "RESOURCE_EXHAUSTED",
                                "message": "private completion",
                            }
                        }
                    ),
                },
            },
        },
        headers={
            "Retry-After": "120",
            "X-RateLimit-Reset": "2026-10-28T00:00:00Z",
            "X-Request-ID": "or-response",
            "Authorization": "Bearer secret",
            "Set-Cookie": "private",
        },
    )
    result = extract_diagnostics(response, req, "secret").model_dump(exclude_none=True)
    assert result["http_status"] == 429
    assert result["error_code"] == 429 and result["upstream_error_code"] == 429
    assert result["upstream_error_type"] == "RESOURCE_EXHAUSTED"
    assert result["provider_name"] == "Google AI Studio"
    assert result["application_request_id"] == "request-123"
    assert result["response_identifiers"]["header_x_request_id"] == "or-response"
    assert (
        result["response_identifiers"]["metadata_provider_request_id"] == "upstream-id"
    )
    assert result["received_limit_headers"]["retry-after"] == "120"
    dumped = json.dumps(result)
    assert not any(
        text in dumped
        for text in (
            "never store",
            "private completion",
            "Authorization",
            "Set-Cookie",
            "secret",
            "raw",
        )
    )


def test_credentials_and_json_input_cannot_be_echoed_in_diagnostic_slots() -> None:
    request = chat_request().model_copy(
        update={
            "messages": (
                chat_request()
                .messages[1]
                .model_copy(update={"content": '{"text":"INPUT_MUST_STAY_PRIVATE"}'}),
            )
        }
    )
    response = HTTPResponse(
        status_code=429,
        payload={
            "id": "test-api-key",
            "provider": "INPUT_MUST_STAY_PRIVATE",
            "error": {
                "code": "INPUT_MUST_STAY_PRIVATE",
                "type": "Bearer-secret",
                "message": "INPUT_MUST_STAY_PRIVATE",
                "metadata": {
                    "request_id": "INPUT_MUST_STAY_PRIVATE",
                    "provider_request_id": "test-api-key",
                    "raw": "INPUT_MUST_STAY_PRIVATE",
                },
            },
        },
        headers={
            "retry-after": "test-api-key",
            "x-request-id": "INPUT_MUST_STAY_PRIVATE",
            "x-ratelimit-reset": "test-api-key",
        },
    )
    result = extract_diagnostics(response, request, "test-api-key").model_dump(
        exclude_none=True
    )
    assert (
        result["response_identifiers"] == {} and result["received_limit_headers"] == {}
    )
    assert "INPUT_MUST_STAY_PRIVATE" not in json.dumps(result)
    assert "test-api-key" not in json.dumps(result)
    assert "provider_name" not in result


@pytest.mark.parametrize(
    "value", ["x" * 129, "secret\nheader", "Bearer abc", "sk-or-credential"]
)
def test_invalid_header_values_are_omitted(value: str) -> None:
    result = extract_diagnostics(
        HTTPResponse(status_code=429, headers={"Retry-After": value}),
        chat_request(),
        "test-key",
    )
    assert not result.received_limit_headers


async def test_adapter_http_failure_carries_safe_diagnostics_without_retry() -> None:
    transport = Transport(
        [
            HTTPResponse(
                status_code=429,
                payload={
                    "error": {
                        "code": 429,
                        "metadata": {"provider_name": "Google AI Studio"},
                    }
                },
                headers={"Retry-After": "90"},
            )
        ]
    )
    client = OpenRouterLLMClient(
        api_key="test-only-key", model="test-model", transport=transport
    )
    with pytest.raises(LLMProviderError) as caught:
        await client.complete(chat_request())
    assert len(transport.requests) == 1
    assert caught.value.diagnostics is not None
    assert caught.value.diagnostics.received_limit_headers == {"retry-after": "90"}


async def test_http_200_invalid_schema_still_carries_status_not_output() -> None:
    transport = Transport(
        [
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "gen-invalid",
                    "choices": [{"message": {"content": '{"wrong":"PRIVATE_OUTPUT"}'}}],
                },
            )
        ]
    )
    service = LLMService(
        settings=configuration(),
        client_factory=SettingsLLMClientFactory(transport=transport),
    )

    async def reserve() -> None:
        pass

    with pytest.raises(LLMProviderError) as caught:
        await service.invoke(AGENT, {"text": "private input"}, reserve)
    assert caught.value.diagnostics is not None
    assert caught.value.diagnostics.http_status == 200
    assert "PRIVATE_OUTPUT" not in caught.value.diagnostics.model_dump_json()
