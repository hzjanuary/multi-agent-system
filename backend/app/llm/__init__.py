"""Provider-independent LLM contracts for Enterprise Multi-Agent OS."""

from app.llm.contracts import (
    LLMChatMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMFinishReason,
    LLMMessageRole,
    LLMModelCapabilities,
    LLMProvider,
    LLMResponseFormat,
    LLMStructuredResponseMetadata,
    LLMUsage,
)
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.factory import (
    LLMClientFactory,
    SettingsLLMClientFactory,
    create_llm_client,
)
from app.llm.output_parser import parse_structured_output
from app.llm.retry import (
    is_fallback_eligible_llm_error,
    is_retryable_llm_error,
)
from app.llm.service import LLMService
from app.llm.settings import LLMSettings
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

__all__ = [
    "ApprovalDecisionDraft",
    "ApprovalPackageOutput",
    "ExtractedItem",
    "FinanceRiskAnalysisOutput",
    "Finding",
    "LLMChatMessage",
    "LLMChatRequest",
    "LLMChatResponse",
    "LLMClientFactory",
    "LLMConfigurationError",
    "LLMErrorCategory",
    "LLMFinishReason",
    "LLMMessageRole",
    "LLMModelCapabilities",
    "LLMProvider",
    "LLMProviderError",
    "LLMResponseFormat",
    "LLMService",
    "LLMSettings",
    "LLMStructuredResponseMetadata",
    "LLMUsage",
    "LegalComplianceAnalysisOutput",
    "Recommendation",
    "RecommendationAction",
    "RequirementExtractionOutput",
    "RiskAssessment",
    "RiskLevel",
    "SettingsLLMClientFactory",
    "SupplierPricingAnalysisOutput",
    "create_llm_client",
    "is_fallback_eligible_llm_error",
    "is_retryable_llm_error",
    "parse_structured_output",
]
