"""Deterministic offline fake LLM client."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.llm.clients.base import build_chat_response, resolve_model, usage_from_values
from app.llm.contracts import (
    LLMChatRequest,
    LLMChatResponse,
    LLMFinishReason,
    LLMMessageRole,
    LLMProvider,
)

_RUNTIME_STAGE_SCHEMAS: Mapping[str, str] = {
    "intake_requirement_extraction": "RequirementExtractionOutput",
    "supplier_pricing_analysis": "SupplierPricingAnalysisOutput",
    "legal_compliance_analysis": "LegalComplianceAnalysisOutput",
    "finance_risk_analysis": "FinanceRiskAnalysisOutput",
    "approval_package_preparation": "ApprovalPackageOutput",
}


class FakeLLMClient:
    """Deterministic fake provider for tests and no-key local development."""

    def __init__(self, *, model: str = "fake-deterministic-model") -> None:
        self._model = model

    @property
    def provider(self) -> LLMProvider:
        """Return this client's provider identifier."""
        return LLMProvider.FAKE

    @property
    def model(self) -> str:
        """Return this client's configured default model."""
        return self._model

    def validate_ready(self) -> None:
        """Fake provider is always ready and never needs credentials."""

    async def complete(self, request: LLMChatRequest) -> LLMChatResponse:
        """Return deterministic content derived from the request shape."""
        model = resolve_model(
            provider=self.provider,
            configured_model=self.model,
            request=request,
        )
        content = self._content_for_request(request)
        response_id = (
            f"fake:{request.request_id}" if request.request_id else "fake:deterministic"
        )
        return build_chat_response(
            provider=self.provider,
            model=model,
            content=content,
            request=request,
            finish_reason=LLMFinishReason.STOP,
            usage=usage_from_values(
                prompt_tokens=sum(
                    len(message.content.split()) for message in request.messages
                ),
                completion_tokens=len(content.split()),
            ),
            response_id=response_id,
            metadata={"fake": True},
        )

    def _content_for_request(self, request: LLMChatRequest) -> str:
        if request.structured_json:
            payload = self._structured_payload_for_request(request)
            return json.dumps(payload, sort_keys=True)
        return (
            "Deterministic fake response: "
            f"{len(request.messages)} messages; "
            f"last_user={self._last_user_message(request)[:200]}"
        )

    def _structured_payload_for_request(
        self,
        request: LLMChatRequest,
    ) -> dict[str, Any]:
        stage = request.metadata.get("stage")
        if isinstance(stage, str) and _is_runtime_stage_request(request):
            return _stage_payload(stage)
        return {
            "provider": self.provider.value,
            "status": "deterministic",
            "message_count": len(request.messages),
            "last_user_message": self._last_user_message(request)[:200],
        }

    def _last_user_message(self, request: LLMChatRequest) -> str:
        for message in reversed(request.messages):
            if message.role is LLMMessageRole.USER:
                return message.content
        return request.messages[-1].content


def _is_runtime_stage_request(request: LLMChatRequest) -> bool:
    stage = request.metadata.get("stage")
    expected_schema = request.metadata.get("expected_schema")
    if not isinstance(stage, str) or not isinstance(expected_schema, str):
        return False
    return _RUNTIME_STAGE_SCHEMAS.get(stage) == expected_schema


def _stage_payload(stage: str) -> dict[str, Any]:
    payloads: Mapping[str, dict[str, Any]] = {
        "intake_requirement_extraction": {
            "summary": (
                "Extracted requirements from the deterministic fake "
                "workflow request."
            ),
            "domain": "it_equipment",
            "customer_name": "Acme Manufacturing Group",
            "extracted_items": [
                {"name": "Standard business laptop", "quantity": 50},
            ],
            "assumptions": ["Fake provider output; verify before approval."],
            "missing_information": ["Delivery deadline"],
            "confidence": 0.8,
            "requires_human_review": True,
        },
        "supplier_pricing_analysis": {
            "summary": "Summarized supplier and pricing considerations.",
            "pricing_basis": (
                "Provided references only; fake provider performs no arithmetic."
            ),
            "findings": [
                {
                    "title": "Pricing reference available",
                    "detail": "Static pricing context was provided.",
                    "severity": "low",
                },
            ],
            "risks": [],
            "assumptions": ["Final quotation arithmetic remains deterministic."],
            "missing_information": [],
            "recommendations": [
                {"action": "review", "rationale": "Review pricing before approval."},
            ],
            "confidence": 0.8,
            "requires_human_review": True,
        },
        "legal_compliance_analysis": {
            "summary": "Summarized legal and compliance considerations.",
            "compliance_status": "needs_review",
            "findings": [],
            "risks": [],
            "missing_information": ["Final payment terms"],
            "recommendations": [
                {"action": "review", "rationale": "Legal review required."},
            ],
            "confidence": 0.8,
            "requires_human_review": True,
        },
        "finance_risk_analysis": {
            "summary": "Summarized finance and risk considerations.",
            "budget_impact": "Budget owner should verify available budget.",
            "findings": [],
            "risks": [],
            "assumptions": ["Budget line not provided."],
            "recommendations": [
                {"action": "review", "rationale": "Finance review required."},
            ],
            "confidence": 0.8,
            "requires_human_review": True,
        },
        "approval_package_preparation": {
            "summary": "Prepared a non-binding approval review package.",
            "decision_draft": "ready_for_review",
            "key_points": ["Workflow request extracted from fake provider."],
            "risks": [],
            "recommendations": [
                {"action": "review", "rationale": "Manager approval required."},
            ],
            "missing_information": [],
            "confidence": 0.8,
            "requires_human_review": True,
        },
    }
    return dict(payloads[stage])
