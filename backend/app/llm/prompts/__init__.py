"""Provider-independent prompt templates for LLM-assisted workflow stages."""

from app.llm.prompts.procurement import (
    build_approval_package_request,
    build_finance_risk_analysis_request,
    build_legal_compliance_analysis_request,
    build_requirement_extraction_request,
    build_supplier_pricing_analysis_request,
)

__all__ = [
    "build_approval_package_request",
    "build_finance_risk_analysis_request",
    "build_legal_compliance_analysis_request",
    "build_requirement_extraction_request",
    "build_supplier_pricing_analysis_request",
]
