"""Direct provider wire contracts, with test-only transport and no inference."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from app.llm.clients.http import HTTPResponse, HTTPResponseLimitError
from app.llm.errors import LLMProviderError
from app.llm.factory import create_llm_client
from app.llm.service import LLMService
from app.llm.settings import LLMSettings
from app.tests.test_llm_generic import Transport
from app.tests.test_llm_provider_clients import chat_request


@pytest.mark.parametrize("provider", ["groq", "openai_compatible"])
async def test_direct_provider_uses_only_its_credential_endpoint_and_parameters(
    provider: str,
) -> None:
    cf_base = "https://api.cloudflare.com/client/v4/accounts/" + "a" * 32 + "/ai/v1"
    settings = LLMSettings(
        provider=provider,
        model=(
            "openai/gpt-oss-20b"
            if provider == "groq"
            else "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        ),
        groq_api_key="groq-test-secret",
        openai_compatible_api_key="cf-test-secret",
        openai_compatible_base_url=cf_base,
        openrouter_api_key="or-test-secret",
        groq_reasoning_effort="low" if provider == "groq" else "",
        max_retries=0,
        openrouter_provider_preferences={"data_collection": "allow", "zdr": False},
    )
    transport = Transport(
        [
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "direct-response",
                    "choices": [{"message": {"content": "{}"}}],
                },
            )
        ]
    )
    result = await create_llm_client(settings, transport=transport).complete(
        chat_request().model_copy(update={"max_tokens": 1024})
    )
    captured = transport.requests[0]
    body = captured["payload"]
    assert (
        captured["url"]
        == ("https://api.groq.com/openai/v1" if provider == "groq" else cf_base)
        + "/chat/completions"
    )
    assert captured["headers"]["Authorization"] == "Bearer " + (
        "groq-test-secret" if provider == "groq" else "cf-test-secret"
    )
    assert (
        body["response_format"] == {"type": "json_object"} and body["stream"] is False
    )
    assert (
        not {
            "provider",
            "plugins",
            "tools",
            "models",
            "max_price",
            "data_collection",
            "zdr",
            "reasoning_format",
        }
        & body.keys()
    )
    if provider == "groq":
        assert body["max_completion_tokens"] == 1024 and "max_tokens" not in body
        assert body["reasoning_effort"] == "low" and body["include_reasoning"] is False
        assert (
            LLMService(settings=settings).profile_identity["reasoning_effort"] == "low"
        )
    else:
        assert body["max_tokens"] == 1024 and "max_completion_tokens" not in body
        assert not {"reasoning_effort", "include_reasoning"} & body.keys()
    assert "secret" not in str(result.metadata)
    path = Path(__file__).resolve().parents[3] / "scripts/ops/live_text_review.py"
    spec = importlib.util.spec_from_file_location("direct_smoke_identity", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert LLMService(settings=settings).profile_identity == module.selected_profile(
        {
            "LLM_PROVIDER": provider,
            "LLM_MODEL": settings.model,
            "LLM_MAX_RETRIES": "0",
            "GROQ_REASONING_EFFORT": settings.groq_reasoning_effort,
            "OPENAI_COMPATIBLE_BASE_URL": cf_base,
        }
    )


@pytest.mark.parametrize("provider", ["groq", "openai_compatible"])
async def test_direct_errors_retain_sanitized_diagnostics(provider: str) -> None:
    settings = LLMSettings(
        provider=provider,
        model="test-model",
        groq_api_key="test-secret",
        openai_compatible_api_key="test-secret",
        openai_compatible_base_url="https://api.cloudflare.com/client/v4/accounts/"
        + "a" * 32
        + "/ai/v1",
    )
    error = {
        "code": "rate_limit_exceeded",
        "type": "tokens",
        "message": "test-secret private-input",
    }
    transport = Transport(
        [
            HTTPResponse(
                status_code=429,
                payload=(
                    {"error": error}
                    if provider == "groq"
                    else {"errors": [error], "success": False}
                ),
                headers={"Retry-After": "120", "X-Request-ID": "provider-response"},
            )
        ]
    )
    with pytest.raises(LLMProviderError) as caught:
        await create_llm_client(settings, transport=transport).complete(chat_request())
    diagnostic = caught.value.diagnostics
    assert diagnostic is not None and diagnostic.http_status == 429
    assert diagnostic.error_code == "rate_limit_exceeded"
    assert diagnostic.received_limit_headers["retry-after"] == "120"
    assert diagnostic.response_identifiers["header_x_request_id"] == "provider-response"
    assert (
        "test-secret" not in diagnostic.model_dump_json()
        and "private-input" not in diagnostic.model_dump_json()
    )


async def test_overlarge_response_is_invalid_output_not_fallback_availability() -> None:
    class Oversize:
        async def post_json(self, **kwargs: Any) -> HTTPResponse:
            raise HTTPResponseLimitError("provider response exceeds transport limit")

    settings = LLMSettings(provider="groq", model="test-model", groq_api_key="test-key")
    with pytest.raises(LLMProviderError) as caught:
        await create_llm_client(settings, transport=Oversize()).complete(chat_request())
    assert caught.value.category.value == "invalid_response"
