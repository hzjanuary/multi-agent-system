"""Tests for procurement structured output schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.llm.structured_outputs import (
    ApprovalDecisionDraft,
    ApprovalPackageOutput,
    ExtractedItem,
    FinanceRiskAnalysisOutput,
    Finding,
    LegalComplianceAnalysisOutput,
    Recommendation,
    RecommendationAction,
    RequirementExtractionOutput,
    RiskAssessment,
    RiskLevel,
    SupplierPricingAnalysisOutput,
)


def _finding() -> Finding:
    return Finding(
        title="Contract available",
        detail="A matching contract reference was provided.",
        severity=RiskLevel.LOW,
        citation="CON-2026-ACME-IT",
    )


def _risk() -> RiskAssessment:
    return RiskAssessment(
        risk="Missing final approver",
        level=RiskLevel.MEDIUM,
        rationale="The requester did not name the approving manager.",
        mitigation="Route package to Manager role.",
    )


def _recommendation() -> Recommendation:
    return Recommendation(
        action=RecommendationAction.REVIEW,
        rationale="Human review is required before customer-facing output.",
        owner_role="Manager",
    )


def test_requirement_extraction_schema_accepts_valid_output() -> None:
    output = RequirementExtractionOutput(
        summary="Customer requests 50 standard business laptops.",
        domain="it_equipment",
        customer_name="Acme Manufacturing Group",
        extracted_items=[
            ExtractedItem(name="Standard business laptop", quantity=50),
        ],
        assumptions=["Master agreement reference is relevant."],
        missing_information=["Delivery deadline"],
        confidence=0.82,
        requires_human_review=True,
    )

    assert output.extracted_items[0].quantity == 50
    assert output.requires_human_review is True


def test_all_stage_schemas_accept_valid_minimal_outputs() -> None:
    SupplierPricingAnalysisOutput(
        summary="Static pricing references are available.",
        pricing_basis="Use provided pricing references only.",
        findings=[_finding()],
        risks=[_risk()],
        assumptions=["No arithmetic performed by LLM."],
        missing_information=[],
        recommendations=[_recommendation()],
        confidence=0.7,
        requires_human_review=True,
    )
    LegalComplianceAnalysisOutput(
        summary="Warranty clause should be reviewed.",
        compliance_status="needs_review",
        findings=[_finding()],
        risks=[_risk()],
        missing_information=["Final payment terms"],
        recommendations=[_recommendation()],
        confidence=0.64,
        requires_human_review=True,
    )
    FinanceRiskAnalysisOutput(
        summary="Budget impact needs manager review.",
        budget_impact="Potential capex impact based on quantity.",
        findings=[_finding()],
        risks=[_risk()],
        assumptions=["Budget owner not provided."],
        recommendations=[_recommendation()],
        confidence=0.74,
        requires_human_review=True,
    )
    ApprovalPackageOutput(
        summary="Ready for manager review.",
        decision_draft=ApprovalDecisionDraft.READY_FOR_REVIEW,
        key_points=["RFQ requests 50 laptops."],
        risks=[_risk()],
        recommendations=[_recommendation()],
        missing_information=["Approval comment"],
        confidence=0.79,
    )


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_confidence_bounds_are_validated(confidence: float) -> None:
    with pytest.raises(ValidationError):
        RequirementExtractionOutput(
            summary="Summary",
            confidence=confidence,
            requires_human_review=True,
        )


def test_list_bounds_are_validated() -> None:
    with pytest.raises(ValidationError):
        RequirementExtractionOutput(
            summary="Summary",
            assumptions=[f"assumption-{index}" for index in range(13)],
            confidence=0.5,
            requires_human_review=True,
        )


def test_text_bounds_and_extra_fields_are_validated() -> None:
    with pytest.raises(ValidationError):
        RequirementExtractionOutput(
            summary="x" * 1201,
            confidence=0.5,
            requires_human_review=True,
        )

    with pytest.raises(ValidationError):
        RequirementExtractionOutput.model_validate(
            {
                "summary": "Valid summary",
                "confidence": 0.5,
                "requires_human_review": True,
                "raw_provider_payload": {"unsafe": True},
            },
        )
