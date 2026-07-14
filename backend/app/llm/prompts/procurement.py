"""Procurement prompt builders for SPEC-011 structured-output stages."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.llm.contracts import LLMChatRequest
from app.llm.prompts.base import build_structured_json_request


def build_requirement_extraction_request(
    workflow_request: Mapping[str, Any] | str,
    *,
    context: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> LLMChatRequest:
    """Build the intake/requirement extraction prompt request."""
    return build_structured_json_request(
        stage_name="intake_requirement_extraction",
        schema_name="RequirementExtractionOutput",
        task_instruction=(
            "Extract procurement requirements, requested items, customer context, "
            "missing information, assumptions, confidence, and human review need."
        ),
        workflow_request=workflow_request,
        context=context,
        request_id=request_id,
        max_tokens=1100,
    )


def build_supplier_pricing_analysis_request(
    workflow_request: Mapping[str, Any] | str,
    *,
    context: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> LLMChatRequest:
    """Build the supplier/pricing analysis placeholder prompt request."""
    return build_structured_json_request(
        stage_name="supplier_pricing_analysis",
        schema_name="SupplierPricingAnalysisOutput",
        task_instruction=(
            "Summarize supplier and pricing considerations using only provided "
            "references. Do not perform arithmetic or invent final prices."
        ),
        workflow_request=workflow_request,
        context=context,
        request_id=request_id,
        max_tokens=1300,
    )


def build_legal_compliance_analysis_request(
    workflow_request: Mapping[str, Any] | str,
    *,
    context: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> LLMChatRequest:
    """Build the legal/compliance analysis placeholder prompt request."""
    return build_structured_json_request(
        stage_name="legal_compliance_analysis",
        schema_name="LegalComplianceAnalysisOutput",
        task_instruction=(
            "Identify compliance considerations, risks, missing clauses, and "
            "recommendations from the provided contracts and policies only."
        ),
        workflow_request=workflow_request,
        context=context,
        request_id=request_id,
        max_tokens=1400,
    )


def build_finance_risk_analysis_request(
    workflow_request: Mapping[str, Any] | str,
    *,
    context: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> LLMChatRequest:
    """Build the finance/risk analysis placeholder prompt request."""
    return build_structured_json_request(
        stage_name="finance_risk_analysis",
        schema_name="FinanceRiskAnalysisOutput",
        task_instruction=(
            "Summarize finance and operational risk considerations. Do not "
            "perform deterministic quotation arithmetic."
        ),
        workflow_request=workflow_request,
        context=context,
        request_id=request_id,
        max_tokens=1300,
    )


def build_approval_package_request(
    workflow_request: Mapping[str, Any] | str,
    *,
    context: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> LLMChatRequest:
    """Build the approval package preparation prompt request."""
    return build_structured_json_request(
        stage_name="approval_package_preparation",
        schema_name="ApprovalPackageOutput",
        task_instruction=(
            "Prepare a concise, non-binding approval review package for a human "
            "manager. Do not approve the workflow or generate customer-facing email."
        ),
        workflow_request=workflow_request,
        context=context,
        request_id=request_id,
        max_tokens=1400,
    )


__all__ = [
    "build_approval_package_request",
    "build_finance_risk_analysis_request",
    "build_legal_compliance_analysis_request",
    "build_requirement_extraction_request",
    "build_supplier_pricing_analysis_request",
]
