"""Tests for feature-flagged LLM runtime integration."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.approvals import (
    ApprovalDecisionRequest,
    ApprovalDecisionType,
    ApprovalService,
    WorkflowResumeRequest,
)
from app.auth import hash_password
from app.auth.rbac import RoleName
from app.config import get_settings
from app.db import create_database_engine, create_session_factory
from app.llm.contracts import (
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMProvider,
)
from app.llm.errors import LLMProviderError
from app.llm.service import LLMService
from app.llm.settings import LLMSettings
from app.llm.structured_outputs import (
    ApprovalPackageOutput,
    FinanceRiskAnalysisOutput,
    LegalComplianceAnalysisOutput,
    RequirementExtractionOutput,
    SupplierPricingAnalysisOutput,
)
from app.models import Role, User
from app.models.enums import WorkflowStatus
from app.runtime import (
    POST_APPROVAL_RUNTIME_STAGES,
    PRE_APPROVAL_RUNTIME_STAGES,
    RuntimeService,
    RuntimeStage,
    WorkflowRuntimeNodeError,
)
from app.workflows import WorkflowEventService, WorkflowService, WorkflowStateCreate


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a rollback-only database session for LLM runtime tests."""
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            transaction = await session.begin()
            try:
                yield session
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()


class FailingLLMService:
    """LLM service double that fails if called."""

    calls: list[LLMChatRequest]

    def __init__(self) -> None:
        self.calls = []

    async def complete_json(self, request: LLMChatRequest) -> LLMChatResponse:
        self.calls.append(request)
        raise AssertionError("LLM service should not be called")


class ScriptedLLMService:
    """LLM service double returning schema-specific JSON responses."""

    def __init__(
        self,
        *,
        malformed_stage: str | None = None,
        provider_error_stage: str | None = None,
    ) -> None:
        self.calls: list[LLMChatRequest] = []
        self.malformed_stage = malformed_stage
        self.provider_error_stage = provider_error_stage

    async def complete_json(self, request: LLMChatRequest) -> LLMChatResponse:
        self.calls.append(request)
        stage = str(request.metadata["stage"])
        if stage == self.provider_error_stage:
            raise LLMProviderError(
                "provider authentication failed",
                category=LLMErrorCategory.AUTHENTICATION,
                provider=LLMProvider.GROQ,
                request_id=request.request_id,
                details={"api_key": "sk-should-not-leak"},
            )
        content = (
            "{}"
            if stage == self.malformed_stage
            else json.dumps(
                _stage_payload(str(request.metadata["expected_schema"])),
            )
        )
        return LLMChatResponse(
            provider=LLMProvider.FAKE,
            model="fake-runtime-model",
            content=content,
            request_id=f"fake:{request.request_id}",
        )


class TrackingFakeLLMService(LLMService):
    """Real LLMService over FakeLLMClient that records complete_json calls."""

    def __init__(self) -> None:
        super().__init__(settings=_llm_settings(enabled=True))
        self.complete_json_calls: list[LLMChatRequest] = []

    async def complete_json(self, request: LLMChatRequest) -> LLMChatResponse:
        self.complete_json_calls.append(request)
        return await super().complete_json(request)


_RUNTIME_STAGE_SCHEMAS: dict[RuntimeStage, type[BaseModel]] = {
    RuntimeStage.PLANNER: RequirementExtractionOutput,
    RuntimeStage.RETRIEVAL: SupplierPricingAnalysisOutput,
    RuntimeStage.COMPLIANCE: LegalComplianceAnalysisOutput,
    RuntimeStage.VALIDATION: FinanceRiskAnalysisOutput,
    RuntimeStage.APPROVAL: ApprovalPackageOutput,
}


def _workflow_state_create() -> WorkflowStateCreate:
    return WorkflowStateCreate.model_validate(
        {
            "workflow_type": "procurement_quotation",
            "domain": "it_equipment",
            "request": {
                "raw_text": "Need 50 business laptops.",
                "source": "manual_text",
            },
        },
    )


async def _created_workflow_id(session: AsyncSession) -> UUID:
    workflow_service = WorkflowService(session)
    workflow = await workflow_service.create_workflow(_workflow_state_create())
    return UUID(workflow.workflow_id)


def _llm_settings(*, enabled: bool) -> LLMSettings:
    return LLMSettings(runtime_enabled=enabled, provider=LLMProvider.FAKE)


@pytest.mark.asyncio
async def test_default_runtime_flag_disabled_does_not_call_llm_service(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    workflow_id = await _created_workflow_id(db_session)
    llm_service = FailingLLMService()
    runtime_service = RuntimeService(
        workflow_service,
        WorkflowEventService(db_session),
        llm_settings=_llm_settings(enabled=False),
        llm_service=llm_service,
    )

    result = await runtime_service.run_workflow(workflow_id)

    assert result.state.status is WorkflowStatus.WAITING_APPROVAL
    assert result.state.stage_outputs[RuntimeStage.PLANNER]["placeholder"] is True
    assert result.state.runtime_context["deterministic_runtime"] is True
    assert llm_service.calls == []


@pytest.mark.asyncio
async def test_llm_enabled_runtime_writes_validated_structured_outputs(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    event_service = WorkflowEventService(db_session)
    workflow_id = await _created_workflow_id(db_session)
    llm_service = ScriptedLLMService()
    runtime_service = RuntimeService(
        workflow_service,
        event_service,
        llm_settings=_llm_settings(enabled=True),
        llm_service=llm_service,
    )

    result = await runtime_service.run_workflow(workflow_id)
    persisted_state = await workflow_service.get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)

    assert result.state.status is WorkflowStatus.WAITING_APPROVAL
    assert result.state.current_stage is RuntimeStage.APPROVAL
    assert result.state.completed_stages == PRE_APPROVAL_RUNTIME_STAGES
    assert len(llm_service.calls) == 5
    assert [request.metadata["stage"] for request in llm_service.calls] == [
        "intake_requirement_extraction",
        "supplier_pricing_analysis",
        "legal_compliance_analysis",
        "finance_risk_analysis",
        "approval_package_preparation",
    ]
    assert all(request.structured_json for request in llm_service.calls)
    assert result.state.stage_outputs[RuntimeStage.PLANNER]["placeholder"] is False
    assert (
        result.state.stage_outputs[RuntimeStage.PLANNER]["llm_output_schema"]
        == "RequirementExtractionOutput"
    )
    assert "content" not in result.state.stage_outputs[RuntimeStage.PLANNER]
    assert result.state.stage_outputs[RuntimeStage.QUOTATION]["llm_skipped"] is True
    assert result.state.stage_outputs[RuntimeStage.QUOTATION]["placeholder"] is True
    assert result.state.runtime_context["llm_runtime_enabled"] is True
    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.WAITING_APPROVAL
    assert persisted_state.planner["llm_output"]["summary"].startswith("Extracted")
    completed_events = [
        event for event in events if event.event_type == "workflow.node.completed"
    ]
    llm_completed_event = next(
        event for event in completed_events if event.agent_name == "planner"
    )
    assert llm_completed_event.payload["llm_runtime_enabled"] is True
    assert llm_completed_event.payload["llm_stage_mode"] == "structured_prompt"
    assert llm_completed_event.payload["stage_output"]["llm_provider"] == "fake"
    assert "llm_output" not in llm_completed_event.payload["stage_output"]


@pytest.mark.asyncio
async def test_llm_enabled_runtime_handles_invalid_structured_output_safely(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    event_service = WorkflowEventService(db_session)
    workflow_id = await _created_workflow_id(db_session)
    runtime_service = RuntimeService(
        workflow_service,
        event_service,
        llm_settings=_llm_settings(enabled=True),
        llm_service=ScriptedLLMService(
            malformed_stage="intake_requirement_extraction",
        ),
    )

    with pytest.raises(WorkflowRuntimeNodeError, match="planner"):
        await runtime_service.run_workflow(workflow_id)

    persisted_state = await workflow_service.get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    failed_event = next(
        event for event in events if event.event_type == "workflow.node.failed"
    )

    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.FAILED
    assert persisted_state.error is not None
    assert persisted_state.error.details["llm_error_category"] == "invalid_response"
    assert failed_event.payload["llm_error_category"] == "invalid_response"
    assert "snippet" not in failed_event.payload


@pytest.mark.asyncio
async def test_llm_enabled_runtime_handles_provider_errors_without_secret_leak(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    event_service = WorkflowEventService(db_session)
    workflow_id = await _created_workflow_id(db_session)
    runtime_service = RuntimeService(
        workflow_service,
        event_service,
        llm_settings=_llm_settings(enabled=True),
        llm_service=ScriptedLLMService(
            provider_error_stage="supplier_pricing_analysis",
        ),
    )

    with pytest.raises(WorkflowRuntimeNodeError, match="retrieval"):
        await runtime_service.run_workflow(workflow_id)

    persisted_state = await workflow_service.get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)
    failed_event = next(
        event for event in events if event.event_type == "workflow.node.failed"
    )
    payload_text = json.dumps(failed_event.payload, sort_keys=True)

    assert persisted_state is not None
    assert persisted_state.error is not None
    assert persisted_state.error.details["llm_error_category"] == "authentication"
    assert failed_event.payload["llm_provider"] == "groq"
    assert failed_event.payload["llm_error_category"] == "authentication"
    assert "sk-should-not-leak" not in payload_text
    assert "api_key" not in payload_text


@pytest.mark.asyncio
async def test_real_fake_provider_runs_end_to_end_to_waiting_approval_and_resume(
    db_session: AsyncSession,
) -> None:
    workflow_service = WorkflowService(db_session)
    event_service = WorkflowEventService(db_session)
    workflow_id = await _created_workflow_id(db_session)
    llm_service = TrackingFakeLLMService()
    runtime_service = RuntimeService(
        workflow_service,
        event_service,
        llm_settings=_llm_settings(enabled=True),
        llm_service=llm_service,
    )

    result = await runtime_service.run_workflow(workflow_id)
    persisted_state = await workflow_service.get_workflow(workflow_id)
    events = await event_service.list_events_for_workflow(workflow_id)

    assert result.state.status is WorkflowStatus.WAITING_APPROVAL
    assert result.state.completed_stages == PRE_APPROVAL_RUNTIME_STAGES
    called_stages = [
        str(request.metadata["stage"]) for request in llm_service.complete_json_calls
    ]
    assert called_stages == [
        "intake_requirement_extraction",
        "supplier_pricing_analysis",
        "legal_compliance_analysis",
        "finance_risk_analysis",
        "approval_package_preparation",
    ]
    assert len(llm_service.complete_json_calls) == 5
    for stage in PRE_APPROVAL_RUNTIME_STAGES:
        if stage is RuntimeStage.QUOTATION:
            continue
        output = result.state.stage_outputs[stage]
        assert output["placeholder"] is False
        assert output["llm_runtime_enabled"] is True
        assert output["llm_provider"] == "fake"
        assert output["llm_output_schema"] == _RUNTIME_STAGE_SCHEMAS[stage].__name__
        _RUNTIME_STAGE_SCHEMAS[stage].model_validate(output["llm_output"])
        assert "content" not in output
    quotation = result.state.stage_outputs[RuntimeStage.QUOTATION]
    assert quotation["llm_skipped"] is True
    assert quotation["placeholder"] is True
    assert result.state.runtime_context["llm_runtime_enabled"] is True
    assert persisted_state is not None
    assert persisted_state.status is WorkflowStatus.WAITING_APPROVAL
    RequirementExtractionOutput.model_validate(persisted_state.planner["llm_output"])
    completed_events = [
        event for event in events if event.event_type == "workflow.node.completed"
    ]
    assert len(completed_events) == 6
    llm_completed_events = [
        event
        for event in completed_events
        if event.payload["llm_stage_mode"] == "structured_prompt"
    ]
    assert len(llm_completed_events) == 5
    quotation_event = next(
        event
        for event in completed_events
        if event.payload["llm_stage_mode"] == "deterministic_no_llm"
    )
    assert quotation_event.agent_name == "quotation"

    actor = await _create_user_with_role(db_session, RoleName.MANAGER)
    await ApprovalService(db_session).submit_approval_decision(
        workflow_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecisionType.APPROVE,
            comment="Approved for G2 resume.",
        ),
        actor,
    )
    resume_result = await runtime_service.resume_workflow_after_approval(
        workflow_id,
        WorkflowResumeRequest(
            request_id="resume-fake-001",
            metadata={"operator_note": "G2 fake end-to-end resume"},
        ),
        actor_type="user",
        actor_id=actor.id,
    )

    assert resume_result.state.status is WorkflowStatus.COMPLETED
    assert resume_result.state.current_stage is RuntimeStage.EMAIL_PREPARATION
    assert resume_result.state.completed_stages == (
        *PRE_APPROVAL_RUNTIME_STAGES,
        *POST_APPROVAL_RUNTIME_STAGES,
    )
    email_output = resume_result.state.stage_outputs[RuntimeStage.EMAIL_PREPARATION]
    assert email_output["email_sent"] is False
    assert "llm_output" not in email_output
    assert len(llm_service.complete_json_calls) == 5


def _stage_payload(schema_name: str) -> dict[str, object]:
    payloads: dict[str, dict[str, object]] = {
        "RequirementExtractionOutput": {
            "summary": "Extracted laptop procurement requirements.",
            "domain": "it_equipment",
            "customer_name": "Acme Manufacturing Group",
            "extracted_items": [
                {"name": "Standard business laptop", "quantity": 50},
            ],
            "assumptions": ["Master agreement reference may apply."],
            "missing_information": ["Delivery deadline"],
            "confidence": 0.82,
            "requires_human_review": True,
        },
        "SupplierPricingAnalysisOutput": {
            "summary": "Supplier and pricing references require review.",
            "pricing_basis": "Use provided references only; no LLM arithmetic.",
            "findings": [
                {
                    "title": "Pricing reference available",
                    "detail": "Static pricing context was provided.",
                    "severity": "low",
                },
            ],
            "risks": [],
            "assumptions": ["Final arithmetic remains deterministic."],
            "missing_information": [],
            "recommendations": [
                {"action": "review", "rationale": "Review before approval."},
            ],
            "confidence": 0.7,
            "requires_human_review": True,
        },
        "LegalComplianceAnalysisOutput": {
            "summary": "Compliance review package prepared.",
            "compliance_status": "needs_review",
            "findings": [],
            "risks": [],
            "missing_information": ["Final payment terms"],
            "recommendations": [
                {"action": "review", "rationale": "Legal review required."},
            ],
            "confidence": 0.66,
            "requires_human_review": True,
        },
        "FinanceRiskAnalysisOutput": {
            "summary": "Finance risk review package prepared.",
            "budget_impact": "Budget owner should verify available budget.",
            "findings": [],
            "risks": [],
            "assumptions": ["Budget line not provided."],
            "recommendations": [
                {"action": "review", "rationale": "Finance review required."},
            ],
            "confidence": 0.68,
            "requires_human_review": True,
        },
        "ApprovalPackageOutput": {
            "summary": "Approval package ready for human manager review.",
            "decision_draft": "ready_for_review",
            "key_points": ["RFQ requests 50 laptops."],
            "risks": [],
            "recommendations": [
                {"action": "review", "rationale": "Manager approval required."},
            ],
            "missing_information": [],
            "confidence": 0.78,
            "requires_human_review": True,
        },
    }
    return payloads[schema_name]


async def _create_user_with_role(
    db_session: AsyncSession,
    role_name: RoleName,
) -> User:
    """Create a user with one role for approval decisions."""
    role = await db_session.scalar(select(Role).where(Role.name == role_name.value))
    if role is None:
        role = Role(name=role_name.value, description=f"{role_name.value} role")
        db_session.add(role)
        await db_session.flush()
    user = User(
        email=f"{role_name.value.lower()}-integration@example.test",
        hashed_password=hash_password("not-used-in-integration-tests"),
        roles=[role],
    )
    db_session.add(user)
    await db_session.flush()
    return user
