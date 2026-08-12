"""Tests for deterministic fake LLM client behavior."""

import pytest

from app.llm.clients import FakeLLMClient, LLMClient
from app.llm.contracts import (
    LLMChatMessage,
    LLMChatRequest,
    LLMMessageRole,
    LLMProvider,
    LLMResponseFormat,
)
from app.llm.output_parser import parse_structured_output
from app.llm.structured_outputs import (
    ApprovalPackageOutput,
    FinanceRiskAnalysisOutput,
    LegalComplianceAnalysisOutput,
    RequirementExtractionOutput,
    SupplierPricingAnalysisOutput,
)

type StageOutputModel = (
    type[RequirementExtractionOutput]
    | type[SupplierPricingAnalysisOutput]
    | type[LegalComplianceAnalysisOutput]
    | type[FinanceRiskAnalysisOutput]
    | type[ApprovalPackageOutput]
)

_RUNTIME_STAGE_CASES = [
    (
        "intake_requirement_extraction",
        "RequirementExtractionOutput",
        RequirementExtractionOutput,
    ),
    (
        "supplier_pricing_analysis",
        "SupplierPricingAnalysisOutput",
        SupplierPricingAnalysisOutput,
    ),
    (
        "legal_compliance_analysis",
        "LegalComplianceAnalysisOutput",
        LegalComplianceAnalysisOutput,
    ),
    (
        "finance_risk_analysis",
        "FinanceRiskAnalysisOutput",
        FinanceRiskAnalysisOutput,
    ),
    (
        "approval_package_preparation",
        "ApprovalPackageOutput",
        ApprovalPackageOutput,
    ),
]


async def test_fake_client_conforms_to_client_protocol() -> None:
    client = FakeLLMClient()

    assert isinstance(client, LLMClient)
    assert client.provider is LLMProvider.FAKE
    client.validate_ready()


async def test_fake_client_returns_deterministic_text_response() -> None:
    client = FakeLLMClient(model="fake-model")
    request = LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.USER, content="Summarize RFQ-001"),
        ),
        request_id="request-1",
    )

    first_response = await client.complete(request)
    second_response = await client.complete(request)

    assert first_response == second_response
    assert first_response.provider is LLMProvider.FAKE
    assert first_response.model == "fake-model"
    assert first_response.request_id == "fake:request-1"
    assert "Summarize RFQ-001" in first_response.content
    assert first_response.metadata == {
        "fake": True,
        "provider_response_id": "fake:request-1",
    }


async def test_fake_client_returns_structured_json_when_requested() -> None:
    client = FakeLLMClient()
    request = LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.SYSTEM, content="Return JSON."),
            LLMChatMessage(role=LLMMessageRole.USER, content="Classify request."),
        ),
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
    )

    response = await client.complete(request)

    assert response.structured_json == {
        "last_user_message": "Classify request.",
        "message_count": 2,
        "provider": "fake",
        "status": "deterministic",
    }
    assert response.structured_metadata is not None
    assert response.structured_metadata.schema_name == "json_object"


@pytest.mark.parametrize(
    ("stage", "schema_name", "output_schema"),
    _RUNTIME_STAGE_CASES,
)
async def test_fake_client_returns_schema_valid_stage_output_for_runtime_stage(
    stage: str,
    schema_name: str,
    output_schema: StageOutputModel,
) -> None:
    client = FakeLLMClient()
    request = LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.USER, content="Summarize RFQ-001"),
        ),
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
        request_id="request-1",
        metadata={"stage": stage, "expected_schema": schema_name},
    )

    first_response = await client.complete(request)
    second_response = await client.complete(request)

    assert first_response == second_response
    assert first_response.structured_json is not None
    assert first_response.structured_metadata is not None
    parsed = parse_structured_output(first_response, output_schema)
    assert isinstance(parsed, output_schema)
    assert parsed.requires_human_review is True


async def test_fake_client_returns_generic_payload_for_unknown_stage_metadata() -> None:
    client = FakeLLMClient()
    request = LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.USER, content="Classify request."),
        ),
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
        metadata={
            "stage": "unknown_stage",
            "expected_schema": "RequirementExtractionOutput",
        },
    )

    response = await client.complete(request)

    assert response.structured_json == {
        "last_user_message": "Classify request.",
        "message_count": 1,
        "provider": "fake",
        "status": "deterministic",
    }


async def test_fake_client_returns_generic_payload_for_mismatched_schema() -> None:
    client = FakeLLMClient()
    request = LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.USER, content="Classify request."),
        ),
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
        metadata={
            "stage": "intake_requirement_extraction",
            "expected_schema": "ApprovalPackageOutput",
        },
    )

    response = await client.complete(request)

    assert response.structured_json == {
        "last_user_message": "Classify request.",
        "message_count": 1,
        "provider": "fake",
        "status": "deterministic",
    }
