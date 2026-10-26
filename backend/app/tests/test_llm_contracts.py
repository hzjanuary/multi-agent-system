"""Tests for provider-independent LLM contracts."""

import pytest
from pydantic import ValidationError

from app.llm import (
    LLMChatMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMFinishReason,
    LLMMessageRole,
    LLMModelCapabilities,
    LLMProvider,
    LLMProviderError,
    LLMResponseFormat,
    LLMStructuredResponseMetadata,
    LLMUsage,
)


def test_llm_provider_enum_supports_required_providers() -> None:
    assert {provider.value for provider in LLMProvider} == {
        "openai_compatible",
        "groq",
        "openrouter",
        "ollama",
        "gemini",
    }


def test_llm_error_categories_are_safe_and_stable() -> None:
    assert {category.value for category in LLMErrorCategory} >= {
        "configuration",
        "authentication",
        "rate_limit",
        "timeout",
        "unavailable",
        "invalid_response",
        "safety",
        "unknown",
    }


def test_chat_request_accepts_provider_independent_messages() -> None:
    request = LLMChatRequest(
        messages=(
            LLMChatMessage(
                role=LLMMessageRole.SYSTEM,
                content="Return concise JSON.",
            ),
            LLMChatMessage(
                role=LLMMessageRole.USER,
                content="Classify this request.",
                metadata={"workflow_id": "workflow-1"},
            ),
        ),
        provider=LLMProvider.OLLAMA,
        model="configured-model",
        temperature=0,
        max_tokens=200,
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
        request_id="request-1",
        timeout_seconds=10,
    )

    assert request.provider is LLMProvider.OLLAMA
    assert request.messages[0].role is LLMMessageRole.SYSTEM
    assert request.messages[1].metadata == {"workflow_id": "workflow-1"}
    assert request.model_dump(mode="json")["provider"] == "ollama"


def test_structured_json_requires_json_response_format() -> None:
    with pytest.raises(ValidationError):
        LLMChatRequest(
            messages=(LLMChatMessage(role=LLMMessageRole.USER, content="hello"),),
            structured_json=True,
        )


def test_chat_response_can_represent_structured_json() -> None:
    response = LLMChatResponse(
        provider=LLMProvider.OLLAMA,
        model="configured-model",
        content='{"domain":"it_equipment"}',
        structured_json={"domain": "it_equipment"},
        structured_metadata=LLMStructuredResponseMetadata(
            schema_name="RequirementExtraction",
            schema_version="1",
        ),
        finish_reason=LLMFinishReason.STOP,
        usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        request_id="request-1",
    )

    dumped = response.model_dump(mode="json")

    assert dumped["structured_json"] == {"domain": "it_equipment"}
    assert dumped["usage"]["total_tokens"] == 15
    assert dumped["finish_reason"] == "stop"


def test_usage_rejects_inconsistent_total_tokens() -> None:
    with pytest.raises(ValidationError):
        LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=12)


def test_model_capabilities_are_provider_independent() -> None:
    capabilities = LLMModelCapabilities(
        provider=LLMProvider.OLLAMA,
        model="llama3.1",
        supports_json_mode=True,
        is_local=True,
        max_input_tokens=8192,
    )

    assert capabilities.provider is LLMProvider.OLLAMA
    assert capabilities.supports_chat is True
    assert capabilities.is_local is True


def test_provider_error_exposes_safe_details_only() -> None:
    error = LLMProviderError(
        "Provider timed out",
        category=LLMErrorCategory.TIMEOUT,
        provider=LLMProvider.GROQ,
        request_id="request-1",
        details={"retryable": True},
    )

    assert error.safe_details() == {
        "category": "timeout",
        "provider": "groq",
        "request_id": "request-1",
        "retryable": True,
    }
