"""Tests for preview-only outbound communication service foundation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.approvals.schemas import ApprovalDecisionType, ApprovalRecord
from app.models import Workflow
from app.models.enums import WorkflowStatus
from app.outbound import (
    OutboundCommunicationDisabledError,
    OutboundCommunicationPolicyError,
    OutboundCommunicationService,
    OutboundCommunicationUnavailableError,
    OutboundSendDisabledError,
    has_approved_decision,
    has_resume_completed,
    validate_preview_allowed,
)


def _now() -> datetime:
    return datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def _approval_record(
    *,
    workflow_id: UUID,
    decision: ApprovalDecisionType = ApprovalDecisionType.APPROVE,
) -> dict[str, object]:
    return ApprovalRecord(
        decision_id=uuid4(),
        workflow_id=workflow_id,
        decision=decision,
        actor_id=uuid4(),
        actor_email="manager@example.test",
        actor_roles=("Manager",),
        comment="Approved for preview.",
        decided_at=_now(),
        previous_status=WorkflowStatus.WAITING_APPROVAL,
        next_status=(
            WorkflowStatus.APPROVED
            if decision is ApprovalDecisionType.APPROVE
            else WorkflowStatus.REJECTED
        ),
    ).model_dump(mode="json")


def _workflow(
    *,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    state_payload: dict[str, object] | None = None,
    workflow_id: UUID | None = None,
) -> Workflow:
    workflow_id = workflow_id or uuid4()
    payload = (
        state_payload
        if state_payload is not None
        else _completed_approved_state(workflow_id)
    )
    return Workflow(
        id=workflow_id,
        workflow_type="procurement_quotation",
        domain="it_equipment",
        status=status,
        request_payload={"source": "unit_test"},
        state_payload=payload,
    )


def _completed_approved_state(workflow_id: UUID) -> dict[str, object]:
    return {
        "approval": {
            "approval_history": [_approval_record(workflow_id=workflow_id)],
            "approval_state": {
                "latest_decision": "approve",
                "has_final_decision": True,
            },
        },
        "runtime_context": {
            "resume_state": {
                "resumed": True,
                "completed_stages": ["email_preparation"],
            },
        },
        "email_preview": {
            "subject": "Approved quotation preview",
            "body": "Dear customer, this preview is ready for manual review.",
            "recipients": [
                {
                    "name": "Demo Customer",
                    "email": "customer@example.test",
                    "role": "buyer",
                },
            ],
        },
    }


def _service(
    *,
    enabled: bool = True,
    send_enabled: bool = False,
    provider: str = "preview",
    require_approval: bool = True,
    max_body_chars: int = 5000,
    max_subject_chars: int = 180,
    max_recipients: int = 10,
) -> OutboundCommunicationService:
    return OutboundCommunicationService(
        enabled=enabled,
        send_enabled=send_enabled,
        provider=provider,
        require_approval=require_approval,
        max_body_chars=max_body_chars,
        max_subject_chars=max_subject_chars,
        max_recipients=max_recipients,
    )


def test_service_disabled_by_default() -> None:
    workflow = _workflow()

    with pytest.raises(OutboundCommunicationDisabledError):
        OutboundCommunicationService().build_preview(workflow)


def test_policy_rejects_non_completed_statuses() -> None:
    blocked_statuses = (
        WorkflowStatus.CREATED,
        WorkflowStatus.PLANNING,
        WorkflowStatus.RETRIEVING,
        WorkflowStatus.CALCULATING,
        WorkflowStatus.CHECKING_COMPLIANCE,
        WorkflowStatus.VALIDATING,
        WorkflowStatus.WAITING_APPROVAL,
        WorkflowStatus.APPROVED,
        WorkflowStatus.REJECTED,
        WorkflowStatus.GENERATING_EMAIL,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    )

    for status in blocked_statuses:
        with pytest.raises(OutboundCommunicationPolicyError):
            validate_preview_allowed(_workflow(status=status))


def test_policy_accepts_completed_with_approval_and_resume_evidence() -> None:
    workflow = _workflow()

    assert validate_preview_allowed(workflow) == ()
    assert has_approved_decision(workflow) is True
    assert has_resume_completed(workflow) is True


def test_policy_rejects_completed_without_approval_evidence() -> None:
    workflow = _workflow(
        state_payload={
            "runtime_context": {"resume_state": {"resumed": True}},
            "email_preview": {
                "subject": "Approved quotation preview",
                "body": "Preview body.",
            },
        },
    )

    with pytest.raises(OutboundCommunicationPolicyError, match="approved"):
        validate_preview_allowed(workflow)


def test_policy_rejects_completed_without_resume_evidence() -> None:
    workflow_id = uuid4()
    workflow = _workflow(
        workflow_id=workflow_id,
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "email_preview": {
                "subject": "Approved quotation preview",
                "body": "Preview body.",
            },
        },
    )

    with pytest.raises(OutboundCommunicationPolicyError, match="resume"):
        validate_preview_allowed(workflow)


def test_service_builds_preview_from_explicit_email_preview_only() -> None:
    workflow = _workflow()

    preview = _service().build_preview(workflow, actor_role="Manager")

    assert preview.workflow_id == workflow.id
    assert preview.subject == "Approved quotation preview"
    assert preview.body == "Dear customer, this preview is ready for manual review."
    assert preview.source == "email_preview"
    assert preview.approval_status == "approved_and_resumed"
    assert preview.workflow_status is WorkflowStatus.COMPLETED
    assert preview.is_sent is False
    assert preview.is_sendable is False
    assert preview.requires_human_approval is False
    assert preview.recipients[0].email == "customer@example.test"
    assert "Preview only; no outbound message was sent." in preview.warnings
    assert "Preview requested by role: Manager." in preview.warnings


def test_service_refuses_when_no_explicit_preview_source_exists() -> None:
    workflow_id = uuid4()
    workflow = _workflow(
        workflow_id=workflow_id,
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "runtime_context": {"resume_state": {"resumed": True}},
            "outputs": {
                "stage_outputs": {
                    "email_preparation": {
                        "status": "completed",
                        "summary": "A runtime event mentioned email preparation.",
                    },
                },
            },
        },
    )

    with pytest.raises(OutboundCommunicationUnavailableError):
        _service().build_preview(workflow)


def test_service_refuses_preview_source_without_subject_or_body() -> None:
    workflow_id = uuid4()
    workflow = _workflow(
        workflow_id=workflow_id,
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "runtime_context": {"resume_state": {"resumed": True}},
            "email_preview": {
                "summary": "Not enough explicit customer-ready content.",
            },
        },
    )

    with pytest.raises(OutboundCommunicationUnavailableError):
        _service().build_preview(workflow)


def test_service_refuses_approved_but_not_resumed_workflow() -> None:
    workflow = _workflow(status=WorkflowStatus.APPROVED)

    with pytest.raises(OutboundCommunicationPolicyError):
        _service().build_preview(workflow)


def test_service_never_sends_and_rejects_send_enabled_or_provider() -> None:
    workflow = _workflow()

    with pytest.raises(OutboundSendDisabledError):
        _service(send_enabled=True).build_preview(workflow)

    with pytest.raises(OutboundSendDisabledError):
        _service(provider="file").build_preview(workflow)


@pytest.mark.asyncio
async def test_send_preview_always_raises() -> None:
    with pytest.raises(OutboundSendDisabledError):
        await _service().send_preview()


def test_service_rejects_approval_bypass_configuration() -> None:
    workflow = _workflow()

    with pytest.raises(OutboundCommunicationPolicyError):
        _service(require_approval=False).build_preview(workflow)


def test_service_sanitizes_and_bounds_preview_output() -> None:
    workflow_id = uuid4()
    workflow = _workflow(
        workflow_id=workflow_id,
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "runtime_context": {"resume_state": {"resumed": True}},
            "email_preview": {
                "subject": "A" * 300,
                "body": "B" * 800,
            },
        },
    )

    preview = _service(max_subject_chars=80, max_body_chars=200).build_preview(
        workflow,
    )

    assert len(preview.subject) == 80
    assert len(preview.body) == 200


def test_service_rejects_sensitive_preview_content() -> None:
    workflow_id = uuid4()
    workflow = _workflow(
        workflow_id=workflow_id,
        state_payload={
            "approval": {
                "approval_history": [_approval_record(workflow_id=workflow_id)],
            },
            "runtime_context": {"resume_state": {"resumed": True}},
            "email_preview": {
                "subject": "Approved preview",
                "body": "raw_prompt provider_payload must not render",
            },
        },
    )

    with pytest.raises(ValueError, match="sensitive"):
        _service().build_preview(workflow)


def test_service_does_not_create_final_quote_for_unapproved_workflow() -> None:
    workflow = _workflow(status=WorkflowStatus.WAITING_APPROVAL)

    with pytest.raises(OutboundCommunicationPolicyError):
        _service().build_preview(workflow)


def test_preview_serialization_has_no_send_or_provider_side_effect_claims() -> None:
    preview = _service().build_preview(_workflow())
    serialized = json.dumps(preview.model_dump(mode="json")).lower()

    forbidden = (
        "email sent",
        "sent successfully",
        "final quote",
        "approved quotation sent",
        "smtp",
        "gmail",
        "authorization",
        "provider_payload",
        "raw_prompt",
        "secret",
        "token",
        "chain_of_thought",
    )
    for claim in forbidden:
        assert claim not in serialized
