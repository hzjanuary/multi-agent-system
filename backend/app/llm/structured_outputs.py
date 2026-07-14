"""Structured procurement LLM output schemas.

These schemas are provider-independent DTOs for validating LLM output before a
future runtime task can merge it into workflow state.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    """Normalized risk levels used by procurement structured outputs."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class RecommendationAction(StrEnum):
    """Normalized recommendation actions."""

    PROCEED = "proceed"
    REVIEW = "review"
    REQUEST_INFORMATION = "request_information"
    BLOCK = "block"


class ApprovalDecisionDraft(StrEnum):
    """Non-binding draft approval direction for human review packages."""

    READY_FOR_REVIEW = "ready_for_review"
    NEEDS_MORE_INFORMATION = "needs_more_information"
    NOT_RECOMMENDED = "not_recommended"


class ExtractedItem(BaseModel):
    """A requested procurement item extracted from source text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    quantity: int | None = Field(default=None, ge=1, le=100000)
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    product_id: str | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = Field(default=None, min_length=1, max_length=500)


class Finding(BaseModel):
    """A bounded finding produced by a stage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(min_length=1, max_length=1000)
    severity: RiskLevel = RiskLevel.UNKNOWN
    citation: str | None = Field(default=None, min_length=1, max_length=300)


class RiskAssessment(BaseModel):
    """A bounded risk assessment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    risk: str = Field(min_length=1, max_length=200)
    level: RiskLevel = RiskLevel.UNKNOWN
    rationale: str = Field(min_length=1, max_length=1000)
    mitigation: str | None = Field(default=None, min_length=1, max_length=1000)


class Recommendation(BaseModel):
    """A bounded recommendation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: RecommendationAction
    rationale: str = Field(min_length=1, max_length=1000)
    owner_role: str | None = Field(default=None, min_length=1, max_length=80)


class RequirementExtractionOutput(BaseModel):
    """Structured output for intake and requirement extraction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1, max_length=1200)
    domain: str | None = Field(default=None, min_length=1, max_length=100)
    customer_name: str | None = Field(default=None, min_length=1, max_length=200)
    extracted_items: list[ExtractedItem] = Field(default_factory=list, max_length=20)
    assumptions: list[str] = Field(default_factory=list, max_length=12)
    missing_information: list[str] = Field(default_factory=list, max_length=12)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool


class SupplierPricingAnalysisOutput(BaseModel):
    """Structured output for supplier/pricing analysis placeholders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1, max_length=1200)
    pricing_basis: str = Field(min_length=1, max_length=800)
    findings: list[Finding] = Field(default_factory=list, max_length=15)
    risks: list[RiskAssessment] = Field(default_factory=list, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=12)
    missing_information: list[str] = Field(default_factory=list, max_length=12)
    recommendations: list[Recommendation] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool


class LegalComplianceAnalysisOutput(BaseModel):
    """Structured output for legal and compliance analysis placeholders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1, max_length=1200)
    compliance_status: str = Field(min_length=1, max_length=120)
    findings: list[Finding] = Field(default_factory=list, max_length=15)
    risks: list[RiskAssessment] = Field(default_factory=list, max_length=12)
    missing_information: list[str] = Field(default_factory=list, max_length=12)
    recommendations: list[Recommendation] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool


class FinanceRiskAnalysisOutput(BaseModel):
    """Structured output for finance and risk analysis placeholders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1, max_length=1200)
    budget_impact: str = Field(min_length=1, max_length=800)
    findings: list[Finding] = Field(default_factory=list, max_length=15)
    risks: list[RiskAssessment] = Field(default_factory=list, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=12)
    recommendations: list[Recommendation] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool


class ApprovalPackageOutput(BaseModel):
    """Structured output for manager approval package preparation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1, max_length=1200)
    decision_draft: ApprovalDecisionDraft
    key_points: list[str] = Field(default_factory=list, max_length=12)
    risks: list[RiskAssessment] = Field(default_factory=list, max_length=12)
    recommendations: list[Recommendation] = Field(default_factory=list, max_length=8)
    missing_information: list[str] = Field(default_factory=list, max_length=12)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool = True


__all__ = [
    "ApprovalDecisionDraft",
    "ApprovalPackageOutput",
    "ExtractedItem",
    "FinanceRiskAnalysisOutput",
    "Finding",
    "LegalComplianceAnalysisOutput",
    "Recommendation",
    "RecommendationAction",
    "RequirementExtractionOutput",
    "RiskAssessment",
    "RiskLevel",
    "SupplierPricingAnalysisOutput",
]
