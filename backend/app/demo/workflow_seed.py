"""Local-demo workflow and event seeding helpers.

This module creates deterministic demo workflow and event rows only when called
explicitly. It does not run workflows, publish live stream messages, expose
public APIs, or own transaction commits.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.contracts import (
    DEMO_SEED_CONTRACT,
    DemoSeedContract,
    DemoWorkflowDefinition,
    DemoWorkflowEventDefinition,
)
from app.demo.user_seed import seed_demo_roles_and_users
from app.models import User, Workflow, WorkflowEvent
from app.workflows.schemas import (
    WorkflowState,
    WorkflowStateMetadata,
    WorkflowStepState,
)

DEMO_EVENT_BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


class DemoWorkflowSeedResult(BaseModel):
    """Bounded summary for local demo workflow/event seed execution."""

    model_config = ConfigDict(frozen=True)

    workflows_created: int = 0
    workflows_reused: int = 0
    workflows_updated: int = 0
    events_created: int = 0
    events_reused: int = 0
    events_updated: int = 0
    workflow_ids: tuple[UUID, ...] = Field(default_factory=tuple)
    event_ids: tuple[UUID, ...] = Field(default_factory=tuple)


async def seed_demo_workflows_and_events(
    session: AsyncSession,
    *,
    contract: DemoSeedContract = DEMO_SEED_CONTRACT,
) -> DemoWorkflowSeedResult:
    """Seed deterministic demo workflows and workflow events idempotently.

    The caller owns transaction boundaries. This helper flushes but never
    commits. Demo users/roles are ensured through TASK 010.2's helper so
    workflow ownership can point at the seeded Sales user.
    """
    await seed_demo_roles_and_users(session, contract=contract)
    creator = await _get_demo_creator(session)

    workflows_created = 0
    workflows_reused = 0
    workflows_updated = 0
    events_created = 0
    events_reused = 0
    events_updated = 0
    workflow_ids: list[UUID] = []
    event_ids: list[UUID] = []
    workflow_by_key: dict[str, Workflow] = {}

    for workflow_definition in contract.workflows:
        workflow = await _get_workflow(session, workflow_definition.stable_workflow_id)
        request_payload = _workflow_request_payload(workflow_definition)
        state_payload = _workflow_state_payload(
            workflow_definition,
            created_by_id=creator.id,
        )

        if workflow is None:
            workflow = Workflow(
                id=workflow_definition.stable_workflow_id,
                workflow_type=workflow_definition.workflow_type.value,
                domain=workflow_definition.domain,
                status=workflow_definition.initial_status,
                created_by_id=creator.id,
                request_payload=request_payload,
                state_payload=state_payload,
            )
            session.add(workflow)
            workflows_created += 1
        else:
            workflows_reused += 1
            if _refresh_demo_workflow(
                workflow,
                workflow_definition,
                creator_id=creator.id,
                request_payload=request_payload,
                state_payload=state_payload,
            ):
                workflows_updated += 1

        workflow_ids.append(workflow_definition.stable_workflow_id)
        workflow_by_key[workflow_definition.key] = workflow

    await session.flush()

    for event_index, event_definition in enumerate(contract.workflow_events):
        workflow = workflow_by_key[event_definition.workflow_key]
        event = await _get_event(session, event_definition.stable_event_id)
        payload = _workflow_event_payload(event_definition)
        event_time = DEMO_EVENT_BASE_TIME + timedelta(seconds=event_index)

        if event is None:
            event = WorkflowEvent(
                id=event_definition.stable_event_id,
                workflow_id=workflow.id,
                event_type=event_definition.event_type,
                actor_type="seed",
                actor_id=creator.id,
                agent_name=event_definition.agent_name,
                status=event_definition.status,
                message=event_definition.message,
                payload=payload,
                created_at=event_time,
                updated_at=event_time,
            )
            session.add(event)
            events_created += 1
        else:
            events_reused += 1
            if _refresh_demo_event(
                event,
                event_definition,
                workflow_id=workflow.id,
                actor_id=creator.id,
                payload=payload,
                event_time=event_time,
            ):
                events_updated += 1

        event_ids.append(event_definition.stable_event_id)

    await session.flush()

    return DemoWorkflowSeedResult(
        workflows_created=workflows_created,
        workflows_reused=workflows_reused,
        workflows_updated=workflows_updated,
        events_created=events_created,
        events_reused=events_reused,
        events_updated=events_updated,
        workflow_ids=tuple(workflow_ids),
        event_ids=tuple(event_ids),
    )


async def _get_demo_creator(session: AsyncSession) -> User:
    statement = select(User).where(User.email == "sales@example.test")
    result = await session.scalars(statement)
    user = result.one_or_none()
    if user is None:
        raise ValueError("sales demo user was not seeded")
    return user


async def _get_workflow(session: AsyncSession, workflow_id: UUID) -> Workflow | None:
    return await session.get(Workflow, workflow_id)


async def _get_event(session: AsyncSession, event_id: UUID) -> WorkflowEvent | None:
    return await session.get(WorkflowEvent, event_id)


def _workflow_request_payload(
    workflow_definition: DemoWorkflowDefinition,
) -> dict[str, Any]:
    return {
        "raw_text": workflow_definition.request_text,
        "source": "demo_seed",
        "rfq_id": workflow_definition.rfq_id,
        "uploaded_document_ids": [],
        "demo": {
            "seed_key": workflow_definition.key,
            "idempotency_key": workflow_definition.idempotency_key,
            "reference_only": True,
        },
    }


def _workflow_state_payload(
    workflow_definition: DemoWorkflowDefinition,
    *,
    created_by_id: UUID,
) -> dict[str, Any]:
    state = WorkflowState(
        workflow_id=str(workflow_definition.stable_workflow_id),
        workflow_type=workflow_definition.workflow_type,
        domain=workflow_definition.domain,
        status=workflow_definition.initial_status,
        request=_workflow_request_payload(workflow_definition),
        metadata=WorkflowStateMetadata(
            created_by_id=str(created_by_id),
            tags={
                "demo": "true",
                "rfq_id": workflow_definition.rfq_id,
                "seed_key": workflow_definition.key,
            },
            attributes={
                "demo_seed": True,
                "demo_seed_key": workflow_definition.key,
                "demo_idempotency_key": workflow_definition.idempotency_key,
                "demo_reference_only": True,
                "expected_contract_id": workflow_definition.expected_contract_id,
                "expected_output_key": workflow_definition.expected_output_key,
                "title": workflow_definition.title,
                "notes": workflow_definition.notes,
            },
        ),
        customer=_customer_payload(workflow_definition),
        items=_item_payloads(workflow_definition),
        planner=_stage_payload(workflow_definition, "planner"),
        retrieval=_stage_payload(workflow_definition, "retrieval"),
        quotation=_quotation_payload(workflow_definition),
        compliance=_stage_payload(workflow_definition, "compliance"),
        validation=_stage_payload(workflow_definition, "validation"),
        approval=_approval_payload(workflow_definition),
        current_step=_current_step(workflow_definition),
        runtime_context={
            "demo_seed": True,
            "demo_reference_only": True,
            "expected_contract_id": workflow_definition.expected_contract_id,
        },
        outputs={
            "demo_reference_only": True,
            "expected_output_key": workflow_definition.expected_output_key,
        },
        steps=_step_states(workflow_definition),
        retry_count=0,
        events=[],
    )
    return state.model_dump(mode="json", exclude_none=True)


def _customer_payload(
    workflow_definition: DemoWorkflowDefinition,
) -> dict[str, str]:
    return {
        "customer_id": workflow_definition.customer_id,
        "name": "Acme Manufacturing Group",
        "contact_name": "Emily Carter",
        "contact_email": "emily.carter@acme-mfg.example",
        "risk_tier": "LOW",
    }


def _item_payloads(
    workflow_definition: DemoWorkflowDefinition,
) -> list[dict[str, object]]:
    return [
        {
            "product_id": product_id,
            "name": "Business Laptop Standard 14 inch",
            "quantity": 50,
            "demo_reference_only": True,
        }
        for product_id in workflow_definition.product_ids
    ]


def _stage_payload(
    workflow_definition: DemoWorkflowDefinition,
    stage: str,
) -> dict[str, object]:
    if workflow_definition.initial_status.value in {"CREATED", "COMPLETED"}:
        return {"demo_reference_only": True}
    return {
        "stage": stage,
        "status": "completed",
        "summary": f"Demo {stage} stage reference output.",
        "demo_reference_only": True,
    }


def _quotation_payload(
    workflow_definition: DemoWorkflowDefinition,
) -> dict[str, object]:
    payload = _stage_payload(workflow_definition, "quotation")
    if workflow_definition.initial_status.value != "CREATED":
        payload.update(
            {
                "currency": "USD",
                "grand_total": 47628,
                "approval_required": True,
            },
        )
    return payload


def _approval_payload(
    workflow_definition: DemoWorkflowDefinition,
) -> dict[str, object]:
    if workflow_definition.initial_status.value == "WAITING_APPROVAL":
        return {
            "status": "waiting_approval",
            "summary": "Demo workflow is waiting for manager approval.",
            "demo_reference_only": True,
        }
    return {"demo_reference_only": True}


def _current_step(workflow_definition: DemoWorkflowDefinition) -> str | None:
    status = workflow_definition.initial_status.value
    if status == "CREATED":
        return "created"
    if status == "WAITING_APPROVAL":
        return "approval"
    if status == "COMPLETED":
        return "completed"
    return None


def _step_states(
    workflow_definition: DemoWorkflowDefinition,
) -> list[WorkflowStepState]:
    if workflow_definition.initial_status.value == "CREATED":
        return []
    completed_steps = ("planner", "retrieval", "quotation", "compliance", "validation")
    return [
        WorkflowStepState(
            name=step,
            status=workflow_definition.initial_status,
            output={
                "summary": f"Demo {step} stage reference output.",
                "demo_reference_only": True,
            },
        )
        for step in completed_steps
    ]


def _workflow_event_payload(
    event_definition: DemoWorkflowEventDefinition,
) -> dict[str, Any]:
    return {
        **event_definition.payload,
        "demo_seed": True,
        "demo_seed_key": event_definition.key,
        "demo_idempotency_key": event_definition.idempotency_key,
        "demo_reference_only": True,
    }


def _refresh_demo_workflow(
    workflow: Workflow,
    workflow_definition: DemoWorkflowDefinition,
    *,
    creator_id: UUID,
    request_payload: dict[str, Any],
    state_payload: dict[str, Any],
) -> bool:
    updated = False
    updates: dict[str, Any] = {
        "workflow_type": workflow_definition.workflow_type.value,
        "domain": workflow_definition.domain,
        "status": workflow_definition.initial_status,
        "created_by_id": creator_id,
        "request_payload": request_payload,
        "state_payload": state_payload,
    }
    for field_name, value in updates.items():
        if getattr(workflow, field_name) != value:
            setattr(workflow, field_name, value)
            updated = True
    return updated


def _refresh_demo_event(
    event: WorkflowEvent,
    event_definition: DemoWorkflowEventDefinition,
    *,
    workflow_id: UUID,
    actor_id: UUID,
    payload: dict[str, Any],
    event_time: datetime,
) -> bool:
    updated = False
    updates: dict[str, Any] = {
        "workflow_id": workflow_id,
        "event_type": event_definition.event_type,
        "actor_type": "seed",
        "actor_id": actor_id,
        "agent_name": event_definition.agent_name,
        "status": event_definition.status,
        "message": event_definition.message,
        "payload": payload,
        "created_at": event_time,
        "updated_at": event_time,
    }
    for field_name, value in updates.items():
        if getattr(event, field_name) != value:
            setattr(event, field_name, value)
            updated = True
    return updated


__all__ = ["DemoWorkflowSeedResult", "seed_demo_workflows_and_events"]
