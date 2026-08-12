"""Mocked HTTP tests for concrete LLM provider clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.llm.clients import (
    GeminiLLMClient,
    GroqLLMClient,
    OllamaLLMClient,
    OpenRouterLLMClient,
)
from app.llm.clients.http import HTTPResponse
from app.llm.contracts import (
    LLMChatMessage,
    LLMChatRequest,
    LLMMessageRole,
    LLMProvider,
    LLMResponseFormat,
)


@dataclass
class CapturedRequest:
    url: str
    headers: dict[str, str]
    payload: dict[str, Any]
    timeout_seconds: int


@dataclass
class FakeTransport:
    responses: list[HTTPResponse | Exception]
    requests: list[CapturedRequest] = field(default_factory=list)

    async def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: int,
    ) -> HTTPResponse:
        self.requests.append(
            CapturedRequest(
                url=url,
                headers=headers,
                payload=payload,
                timeout_seconds=timeout_seconds,
            ),
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def chat_request() -> LLMChatRequest:
    return LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.SYSTEM, content="Return JSON."),
            LLMChatMessage(role=LLMMessageRole.USER, content="Analyze RFQ-001."),
        ),
        temperature=0,
        max_tokens=128,
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
        request_id="request-123",
        timeout_seconds=12,
    )


async def test_groq_client_maps_request_and_normalizes_response() -> None:
    transport = FakeTransport(
        responses=[
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "chatcmpl-groq-1",
                    "model": "llama-3.3-70b-versatile",
                    "choices": [
                        {
                            "message": {"content": '{"stage":"planner"}'},
                            "finish_reason": "stop",
                        },
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 4,
                        "total_tokens": 14,
                    },
                },
            ),
        ],
    )
    client = GroqLLMClient(
        api_key="groq-test-key",
        model="llama-3.3-70b-versatile",
        transport=transport,
    )

    response = await client.complete(chat_request())

    request = transport.requests[0]
    assert request.url == "https://api.groq.com/openai/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer groq-test-key"
    assert request.headers["X-Request-ID"] == "request-123"
    assert request.headers["User-Agent"] == "enterprise-os-backend/1.0"
    assert request.timeout_seconds == 12
    assert request.payload["model"] == "llama-3.3-70b-versatile"
    assert request.payload["stream"] is False
    assert request.payload["response_format"] == {"type": "json_object"}
    assert request.payload["messages"] == [
        {"role": "system", "content": "Return JSON."},
        {"role": "user", "content": "Analyze RFQ-001."},
    ]
    assert response.provider is LLMProvider.GROQ
    assert response.structured_json == {"stage": "planner"}
    assert response.usage is not None
    assert response.usage.total_tokens == 14
    assert response.request_id == "chatcmpl-groq-1"


async def test_openrouter_client_maps_request_and_normalizes_response() -> None:
    transport = FakeTransport(
        responses=[
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "openrouter-response-1",
                    "model": "openai/gpt-4o-mini",
                    "choices": [
                        {
                            "message": {"content": '{"stage":"retrieval"}'},
                            "finish_reason": "stop",
                        },
                    ],
                },
            ),
        ],
    )
    client = OpenRouterLLMClient(
        api_key="openrouter-test-key",
        model="openai/gpt-4o-mini",
        transport=transport,
    )

    response = await client.complete(chat_request())

    request = transport.requests[0]
    assert request.url == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer openrouter-test-key"
    assert request.payload["stream"] is False
    assert response.provider is LLMProvider.OPENROUTER
    assert response.structured_json == {"stage": "retrieval"}
    assert response.metadata["provider_api"] == "openai_compatible"


@pytest.mark.parametrize(
    ("client_factory", "expected_authorization"),
    [
        (
            lambda: GroqLLMClient(api_key="groq-test-key", model="m"),
            "Bearer groq-test-key",
        ),
        (
            lambda: OpenRouterLLMClient(api_key="openrouter-test-key", model="m"),
            "Bearer openrouter-test-key",
        ),
    ],
)
async def test_openai_compatible_clients_send_stable_user_agent(
    client_factory: Any,
    expected_authorization: str,
) -> None:
    transport = FakeTransport(
        responses=[
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "response-1",
                    "model": "m",
                    "choices": [
                        {"message": {"content": "ok"}, "finish_reason": "stop"},
                    ],
                },
            ),
        ],
    )
    client = client_factory()
    client._transport = transport

    await client.complete(
        LLMChatRequest(
            messages=(LLMChatMessage(role=LLMMessageRole.USER, content="hello"),),
            request_id="request-xyz",
        ),
    )

    request = transport.requests[0]
    assert request.headers["Authorization"] == expected_authorization
    assert request.headers["User-Agent"] == "enterprise-os-backend/1.0"
    assert request.headers["X-Request-ID"] == "request-xyz"


async def test_ollama_client_maps_stream_false_and_normalizes_response() -> None:
    transport = FakeTransport(
        responses=[
            HTTPResponse(
                status_code=200,
                payload={
                    "model": "llama3.1",
                    "message": {"role": "assistant", "content": '{"stage":"local"}'},
                    "done": True,
                    "done_reason": "stop",
                    "prompt_eval_count": 11,
                    "eval_count": 5,
                },
            ),
        ],
    )
    client = OllamaLLMClient(
        base_url="http://ollama.local:11434/",
        model="llama3.1",
        transport=transport,
    )

    response = await client.complete(chat_request())

    request = transport.requests[0]
    assert request.url == "http://ollama.local:11434/api/chat"
    assert "Authorization" not in request.headers
    assert request.payload["stream"] is False
    assert request.payload["format"] == "json"
    assert request.payload["options"] == {"temperature": 0.0, "num_predict": 128}
    assert response.provider is LLMProvider.OLLAMA
    assert response.structured_json == {"stage": "local"}
    assert response.usage is not None
    assert response.usage.total_tokens == 16


async def test_gemini_client_maps_generate_content_and_normalizes_response() -> None:
    transport = FakeTransport(
        responses=[
            HTTPResponse(
                status_code=200,
                payload={
                    "modelVersion": "gemini-2.0-flash",
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": '{"stage":"compliance"}'}],
                            },
                            "finishReason": "STOP",
                        },
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 20,
                        "candidatesTokenCount": 6,
                        "totalTokenCount": 26,
                    },
                },
            ),
        ],
    )
    client = GeminiLLMClient(
        api_key="gemini-test-key",
        model="gemini-2.0-flash",
        transport=transport,
    )

    response = await client.complete(chat_request())

    request = transport.requests[0]
    assert request.url.endswith("/models/gemini-2.0-flash:generateContent")
    assert request.headers["x-goog-api-key"] == "gemini-test-key"
    assert request.headers["X-Request-ID"] == "request-123"
    assert request.payload["systemInstruction"] == {
        "parts": [{"text": "Return JSON."}],
    }
    assert request.payload["contents"] == [
        {"role": "user", "parts": [{"text": "Analyze RFQ-001."}]},
    ]
    assert request.payload["generationConfig"] == {
        "temperature": 0.0,
        "maxOutputTokens": 128,
        "responseMimeType": "application/json",
    }
    assert response.provider is LLMProvider.GEMINI
    assert response.structured_json == {"stage": "compliance"}
    assert response.usage is not None
    assert response.usage.total_tokens == 26


@pytest.mark.parametrize(
    "client",
    [
        GroqLLMClient(api_key="key", model=""),
        OpenRouterLLMClient(api_key="key", model=""),
        OllamaLLMClient(base_url="http://localhost:11434", model=""),
        GeminiLLMClient(api_key="key", model=""),
    ],
)
async def test_clients_allow_request_level_model_override(client: object) -> None:
    transport = FakeTransport(
        responses=[
            HTTPResponse(
                status_code=200,
                payload={
                    "id": "response-1",
                    "model": "request-model",
                    "choices": [
                        {"message": {"content": "ok"}, "finish_reason": "stop"},
                    ],
                    "message": {"content": "ok"},
                    "done": True,
                    "candidates": [
                        {
                            "content": {"parts": [{"text": "ok"}]},
                            "finishReason": "STOP",
                        },
                    ],
                },
            ),
        ],
    )
    client._transport = transport  # type: ignore[attr-defined]

    response = await client.complete(  # type: ignore[attr-defined]
        LLMChatRequest(
            messages=(LLMChatMessage(role=LLMMessageRole.USER, content="hello"),),
            model="request-model",
        ),
    )

    assert response.model
