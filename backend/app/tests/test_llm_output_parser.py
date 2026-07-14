"""Tests for deterministic LLM structured output parsing."""

from __future__ import annotations

import json

import pytest

from app.llm.contracts import LLMChatResponse, LLMErrorCategory, LLMProvider
from app.llm.errors import LLMProviderError
from app.llm.output_parser import parse_structured_output
from app.llm.structured_outputs import RequirementExtractionOutput


def _response(content: str) -> LLMChatResponse:
    return LLMChatResponse(
        provider=LLMProvider.FAKE,
        model="fake-model",
        content=content,
        request_id="parse-request",
    )


def _valid_payload() -> dict[str, object]:
    return {
        "summary": "Customer requests 50 laptops.",
        "domain": "it_equipment",
        "customer_name": "Acme Manufacturing Group",
        "extracted_items": [{"name": "Standard business laptop", "quantity": 50}],
        "assumptions": ["Contract reference may apply."],
        "missing_information": ["Delivery deadline"],
        "confidence": 0.81,
        "requires_human_review": True,
    }


def test_parser_accepts_valid_json_object() -> None:
    parsed = parse_structured_output(
        _response(json.dumps(_valid_payload())),
        RequirementExtractionOutput,
    )

    assert parsed.summary == "Customer requests 50 laptops."
    assert parsed.extracted_items[0].quantity == 50


def test_parser_accepts_simple_fenced_json_object() -> None:
    parsed = parse_structured_output(
        _response(f"```json\n{json.dumps(_valid_payload())}\n```"),
        RequirementExtractionOutput,
    )

    assert parsed.domain == "it_equipment"


def test_parser_rejects_malformed_json_with_safe_category() -> None:
    with pytest.raises(LLMProviderError) as exc_info:
        parse_structured_output(
            _response('{"summary": "missing end"'),
            RequirementExtractionOutput,
        )

    assert exc_info.value.category is LLMErrorCategory.INVALID_RESPONSE
    assert exc_info.value.request_id == "parse-request"
    assert len(exc_info.value.details["snippet"]) <= 243


def test_parser_rejects_missing_required_fields() -> None:
    with pytest.raises(LLMProviderError) as exc_info:
        parse_structured_output(
            _response('{"summary":"Only summary"}'),
            RequirementExtractionOutput,
        )

    assert exc_info.value.category is LLMErrorCategory.INVALID_RESPONSE
    assert "RequirementExtractionOutput" in str(exc_info.value)


def test_parser_rejects_non_object_json() -> None:
    with pytest.raises(LLMProviderError) as exc_info:
        parse_structured_output(
            _response('["not", "an", "object"]'),
            RequirementExtractionOutput,
        )

    assert exc_info.value.category is LLMErrorCategory.INVALID_RESPONSE


def test_parser_error_snippet_is_bounded_and_does_not_dump_giant_payload() -> None:
    secret_like_payload = "sk-test-" + ("x" * 2000)

    with pytest.raises(LLMProviderError) as exc_info:
        parse_structured_output(
            _response(secret_like_payload),
            RequirementExtractionOutput,
        )

    snippet = exc_info.value.details["snippet"]
    assert len(snippet) <= 243
    assert secret_like_payload not in str(exc_info.value)
