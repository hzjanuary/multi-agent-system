"""Tests for provider-independent procurement prompt builders."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest

from app.llm.contracts import (
    LLMChatRequest,
    LLMMessageRole,
    LLMResponseFormat,
)
from app.llm.prompts import (
    build_approval_package_request,
    build_finance_risk_analysis_request,
    build_legal_compliance_analysis_request,
    build_requirement_extraction_request,
    build_supplier_pricing_analysis_request,
)
from app.llm.prompts.base import MAX_CONTEXT_VALUE_LENGTH, MAX_PROMPT_VALUE_LENGTH

PromptBuilder = Callable[
    [Mapping[str, Any] | str],
    LLMChatRequest,
]


def _workflow_request() -> dict[str, Any]:
    return {
        "domain": "it_equipment",
        "request": "Please quote 50 business laptops.",
        "api_key": "should-not-appear",
        "metadata": {"token": "secret-token"},
    }


@pytest.mark.parametrize(
    ("builder", "stage", "schema_name"),
    [
        (
            build_requirement_extraction_request,
            "intake_requirement_extraction",
            "RequirementExtractionOutput",
        ),
        (
            build_supplier_pricing_analysis_request,
            "supplier_pricing_analysis",
            "SupplierPricingAnalysisOutput",
        ),
        (
            build_legal_compliance_analysis_request,
            "legal_compliance_analysis",
            "LegalComplianceAnalysisOutput",
        ),
        (
            build_finance_risk_analysis_request,
            "finance_risk_analysis",
            "FinanceRiskAnalysisOutput",
        ),
        (
            build_approval_package_request,
            "approval_package_preparation",
            "ApprovalPackageOutput",
        ),
    ],
)
def test_procurement_prompt_builders_return_structured_llm_requests(
    builder: PromptBuilder,
    stage: str,
    schema_name: str,
) -> None:
    request = builder(_workflow_request())

    assert request.response_format is LLMResponseFormat.JSON_OBJECT
    assert request.structured_json is True
    assert request.temperature == 0
    assert request.metadata["stage"] == stage
    assert request.metadata["expected_schema"] == schema_name
    assert [message.role for message in request.messages] == [
        LLMMessageRole.SYSTEM,
        LLMMessageRole.USER,
    ]
    assert schema_name in request.messages[0].content
    assert "Return JSON only." in request.messages[1].content


def test_prompt_rendering_is_deterministic() -> None:
    first = build_requirement_extraction_request(
        {"b": 2, "a": 1},
        context={"z": "last", "a": "first"},
        request_id="prompt-1",
    )
    second = build_requirement_extraction_request(
        {"b": 2, "a": 1},
        context={"z": "last", "a": "first"},
        request_id="prompt-1",
    )

    assert first == second


def test_prompt_redacts_sensitive_keys_and_does_not_read_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-secret-that-must-not-appear")
    monkeypatch.setenv("OPENROUTER_API_KEY", "another-env-secret")

    request = build_requirement_extraction_request(_workflow_request())
    rendered = "\n".join(message.content for message in request.messages)

    assert "should-not-appear" not in rendered
    assert "secret-token" not in rendered
    assert "env-secret-that-must-not-appear" not in rendered
    assert "another-env-secret" not in rendered
    assert "[redacted]" in rendered


def test_prompt_bounds_large_inputs() -> None:
    request = build_supplier_pricing_analysis_request(
        {"request": "x" * (MAX_PROMPT_VALUE_LENGTH + 2000)},
        context={"notes": "y" * (MAX_CONTEXT_VALUE_LENGTH + 2000)},
    )
    user_message = request.messages[1].content

    assert len(user_message) < MAX_PROMPT_VALUE_LENGTH + MAX_CONTEXT_VALUE_LENGTH + 800
    assert "..." in user_message
