"""Pure policy helpers for preview-only outbound communication."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from app.approvals.schemas import ApprovalDecisionType, ApprovalRecord
from app.models import Workflow
from app.models.enums import WorkflowStatus
from app.outbound.exceptions import OutboundCommunicationPolicyError

APPROVED_PREVIEW_ALLOWED_STATUS = WorkflowStatus.COMPLETED
APPROVAL_HISTORY_KEY = "approval_history"
RESUME_STATE_KEY = "resume_state"
RESUMED_KEY = "resumed"


def validate_preview_allowed(workflow: Workflow) -> tuple[str, ...]:
    """Raise unless workflow has crossed approval and explicit resume boundary.

    Sprint 1 fails closed for every non-COMPLETED status and requires explicit
    workflow-state evidence for both a Manager/Admin approval and resume
    completion. It does not change lifecycle transitions.
    """
    if workflow.status is not APPROVED_PREVIEW_ALLOWED_STATUS:
        raise OutboundCommunicationPolicyError(
            "Outbound preview requires a completed workflow after approval and resume.",
        )

    warnings: list[str] = []
    if not has_approved_decision(workflow):
        raise OutboundCommunicationPolicyError(
            "Outbound preview requires explicit approved decision evidence.",
        )
    if not has_resume_completed(workflow):
        raise OutboundCommunicationPolicyError(
            "Outbound preview requires explicit resume completion evidence.",
        )
    return tuple(warnings)


def has_approved_decision(workflow: Workflow) -> bool:
    """Return true when workflow state has a final approve decision."""
    return any(
        record.workflow_id == workflow.id
        and record.decision is ApprovalDecisionType.APPROVE
        for record in approval_records_from_workflow(workflow)
    )


def has_resume_completed(workflow: Workflow) -> bool:
    """Return true when workflow state contains explicit resume evidence."""
    state_payload = _mapping(workflow.state_payload)
    runtime_context = _mapping(state_payload.get("runtime_context"))
    resume_state = _mapping(runtime_context.get(RESUME_STATE_KEY))
    if resume_state.get(RESUMED_KEY) is True:
        return True

    outputs = _mapping(state_payload.get("outputs"))
    stage_outputs = _mapping(outputs.get("stage_outputs"))
    email_stage = _mapping(stage_outputs.get("email_preparation"))
    return email_stage.get("status") == "completed"


def approval_records_from_workflow(workflow: Workflow) -> tuple[ApprovalRecord, ...]:
    """Extract approval records from the existing workflow state payload."""
    state_payload = _mapping(workflow.state_payload)
    approval_payload = _mapping(state_payload.get("approval"))
    raw_records = approval_payload.get(APPROVAL_HISTORY_KEY, ())
    if not isinstance(raw_records, list | tuple):
        return ()

    records: list[ApprovalRecord] = []
    for raw_record in raw_records:
        try:
            records.append(ApprovalRecord.model_validate(raw_record))
        except ValidationError:
            continue
    return tuple(records)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
