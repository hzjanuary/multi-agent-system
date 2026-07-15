"""Typed contracts for deterministic local demo seed data.

This module defines seed data contracts only. It does not create database
records, open sessions, hash passwords, append events, or run workflows.
"""

from __future__ import annotations

from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.approvals.events import (
    APPROVAL_APPROVED_EVENT,
    APPROVAL_CHANGES_REQUESTED_EVENT,
    APPROVAL_REJECTED_EVENT,
    WORKFLOW_RESUME_REQUESTED_EVENT,
    WORKFLOW_RESUMED_EVENT,
)
from app.auth.rbac import RoleName
from app.models.enums import WorkflowEventStatus, WorkflowStatus
from app.workflows.schemas import WorkflowType

DEMO_SEED_NAMESPACE = UUID("9b46b9ec-4a7d-43b5-9b73-1f7f6b548b1f")
DEMO_PASSWORD = "DemoPassword123!"


def deterministic_demo_uuid(key: str) -> UUID:
    """Return a stable UUID for a demo seed idempotency key."""
    return uuid5(DEMO_SEED_NAMESPACE, key)


class DemoDatasetReference(BaseModel):
    """Reference to a static dataset file used by the demo contract."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=500)
    required_for_primary_demo: bool = False


class DemoCredential(BaseModel):
    """Local-only demo credential metadata."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    is_demo_only: bool = True
    usage_note: str = Field(min_length=1, max_length=500)

    @field_validator("email")
    @classmethod
    def require_demo_email_domain(cls, value: str) -> str:
        """Ensure committed credentials are visibly non-production."""
        if not value.endswith("@example.test"):
            raise ValueError("demo credential emails must use @example.test")
        return value

    @field_validator("password")
    @classmethod
    def require_demo_password_marker(cls, value: str) -> str:
        """Ensure committed passwords are obvious local demo passwords."""
        if "Demo" not in value:
            raise ValueError("demo credential passwords must be visibly demo-only")
        return value


class DemoRoleDefinition(BaseModel):
    """Role contract for local demo users."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1, max_length=100)
    role_name: RoleName
    description: str = Field(min_length=1, max_length=500)

    @property
    def idempotency_key(self) -> str:
        """Stable natural key for role seed upsert behavior."""
        return f"demo:role:{self.role_name.value}"


class DemoUserDefinition(BaseModel):
    """User contract for local demo credentials and RBAC role assignment."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=255)
    role_name: RoleName
    credential_key: str = Field(min_length=1, max_length=100)
    is_demo_only: bool = True

    @property
    def idempotency_key(self) -> str:
        """Stable natural key for user seed upsert behavior."""
        return f"demo:user:{self.email}"

    @property
    def stable_user_id(self) -> UUID:
        """Stable UUID available to future seed implementations if needed."""
        return deterministic_demo_uuid(self.idempotency_key)


class DemoWorkflowDefinition(BaseModel):
    """Workflow seed contract for deterministic demo examples."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    workflow_type: WorkflowType = WorkflowType.PROCUREMENT_QUOTATION
    domain: str = Field(min_length=1, max_length=100)
    initial_status: WorkflowStatus
    rfq_id: str = Field(min_length=1, max_length=50)
    customer_id: str = Field(min_length=1, max_length=50)
    request_text: str = Field(min_length=1, max_length=2000)
    product_ids: tuple[str, ...] = Field(min_length=1)
    expected_contract_id: str = Field(min_length=1, max_length=100)
    expected_output_key: str = Field(min_length=1, max_length=50)
    seed_event_history: bool = False
    notes: str = Field(min_length=1, max_length=500)

    @property
    def idempotency_key(self) -> str:
        """Stable natural key for workflow seed upsert behavior."""
        return f"demo:workflow:{self.key}"

    @property
    def stable_workflow_id(self) -> UUID:
        """Stable UUID available to future seed implementations if needed."""
        return deterministic_demo_uuid(self.idempotency_key)


class DemoWorkflowEventDefinition(BaseModel):
    """Workflow event seed contract for timeline/backlog examples."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1, max_length=100)
    workflow_key: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    status: WorkflowEventStatus
    message: str = Field(min_length=1, max_length=500)
    agent_name: str | None = Field(default=None, min_length=1, max_length=100)
    payload: dict[str, str | bool | int | float] = Field(default_factory=dict)

    @property
    def idempotency_key(self) -> str:
        """Stable natural key for workflow event seed upsert behavior."""
        return f"demo:event:{self.workflow_key}:{self.key}"

    @property
    def stable_event_id(self) -> UUID:
        """Stable UUID available to future seed implementations if needed."""
        return deterministic_demo_uuid(self.idempotency_key)


class DemoSeedContract(BaseModel):
    """Top-level immutable contract for local demo seed planning."""

    model_config = ConfigDict(frozen=True)

    dataset_references: tuple[DemoDatasetReference, ...]
    credentials: tuple[DemoCredential, ...]
    roles: tuple[DemoRoleDefinition, ...]
    users: tuple[DemoUserDefinition, ...]
    workflows: tuple[DemoWorkflowDefinition, ...]
    workflow_events: tuple[DemoWorkflowEventDefinition, ...]


DATASET_REFERENCES: tuple[DemoDatasetReference, ...] = (
    DemoDatasetReference(
        key="customers-json",
        path="datasets/customers.json",
        description="Demo customers used to populate workflow customer metadata.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="products-json",
        path="datasets/products.json",
        description="Demo product catalog used for RFQ item references.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="pricing-rules-json",
        path="datasets/pricing_rules.json",
        description="Static discount references for demo metadata only.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="contracts",
        path="datasets/contracts",
        description="Markdown contract references for demo retrieval context.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="policies",
        path="datasets/policies",
        description="Markdown policy references for demo compliance context.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="rfq-samples",
        path="datasets/rfqs/rfq_samples.json",
        description="Sample procurement RFQs used by the demo workflows.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="expected-quotes",
        path="datasets/expected_outputs/expected_quotes.json",
        description="Expected quote outputs used as static demo references.",
        required_for_primary_demo=True,
    ),
    DemoDatasetReference(
        key="document-index",
        path="datasets/index/document_index.json",
        description="Static document lookup index for future retrieval demos.",
    ),
)

DEMO_CREDENTIALS: tuple[DemoCredential, ...] = (
    DemoCredential(
        key="admin",
        email="admin@example.test",
        password=DEMO_PASSWORD,
        usage_note="Local demo Admin account; never use in production.",
    ),
    DemoCredential(
        key="manager",
        email="manager@example.test",
        password=DEMO_PASSWORD,
        usage_note="Local demo Manager account; never use in production.",
    ),
    DemoCredential(
        key="sales",
        email="sales@example.test",
        password=DEMO_PASSWORD,
        usage_note="Local demo Sales account; never use in production.",
    ),
    DemoCredential(
        key="legal",
        email="legal@example.test",
        password=DEMO_PASSWORD,
        usage_note="Local demo Legal account; never use in production.",
    ),
    DemoCredential(
        key="finance",
        email="finance@example.test",
        password=DEMO_PASSWORD,
        usage_note="Local demo Finance account; never use in production.",
    ),
    DemoCredential(
        key="viewer",
        email="viewer@example.test",
        password=DEMO_PASSWORD,
        usage_note="Local demo Viewer account; never use in production.",
    ),
)

DEMO_ROLES: tuple[DemoRoleDefinition, ...] = (
    DemoRoleDefinition(
        key="admin",
        role_name=RoleName.ADMIN,
        description="Full demo operator access.",
    ),
    DemoRoleDefinition(
        key="manager",
        role_name=RoleName.MANAGER,
        description="Runs workflows and explains approval wait state.",
    ),
    DemoRoleDefinition(
        key="sales",
        role_name=RoleName.SALES,
        description="Creates procurement quotation workflows.",
    ),
    DemoRoleDefinition(
        key="legal",
        role_name=RoleName.LEGAL,
        description="Reads workflow detail from compliance reviewer perspective.",
    ),
    DemoRoleDefinition(
        key="finance",
        role_name=RoleName.FINANCE,
        description="Reads workflow detail from finance reviewer perspective.",
    ),
    DemoRoleDefinition(
        key="viewer",
        role_name=RoleName.VIEWER,
        description="Read-only observer for RBAC demonstration.",
    ),
)

DEMO_USERS: tuple[DemoUserDefinition, ...] = tuple(
    DemoUserDefinition(
        key=credential.key,
        email=credential.email,
        full_name=f"Demo {credential.key.title()}",
        role_name=role.role_name,
        credential_key=credential.key,
    )
    for credential, role in zip(DEMO_CREDENTIALS, DEMO_ROLES, strict=True)
)

RFQ_001_TEXT = (
    "We would like to purchase 50 standard business laptops for a new operations "
    "team. We signed a master agreement in May 2026. Please provide your best "
    "quotation with the applicable discount."
)

DEMO_WORKFLOWS: tuple[DemoWorkflowDefinition, ...] = (
    DemoWorkflowDefinition(
        key="rfq-001-clean-created",
        title="RFQ-001 clean workflow ready to run",
        domain="it_equipment",
        initial_status=WorkflowStatus.CREATED,
        rfq_id="RFQ-001",
        customer_id="CUST-001",
        request_text=RFQ_001_TEXT,
        product_ids=("IT-LAP-001",),
        expected_contract_id="CON-2026-ACME-IT",
        expected_output_key="RFQ-001",
        notes="Primary board demo workflow; runtime should stop at WAITING_APPROVAL.",
    ),
    DemoWorkflowDefinition(
        key="rfq-001-waiting-approval-history",
        title="RFQ-001 workflow with persisted event history",
        domain="it_equipment",
        initial_status=WorkflowStatus.WAITING_APPROVAL,
        rfq_id="RFQ-001",
        customer_id="CUST-001",
        request_text=RFQ_001_TEXT,
        product_ids=("IT-LAP-001",),
        expected_contract_id="CON-2026-ACME-IT",
        expected_output_key="RFQ-001",
        seed_event_history=True,
        notes=(
            "Live approval walkthrough workflow; no final approval is seeded so "
            "Manager/Admin can approve it during the demo."
        ),
    ),
    DemoWorkflowDefinition(
        key="rfq-001-approved-ready-to-resume",
        title="RFQ-001 workflow approved and ready to resume",
        domain="it_equipment",
        initial_status=WorkflowStatus.APPROVED,
        rfq_id="RFQ-001",
        customer_id="CUST-001",
        request_text=RFQ_001_TEXT,
        product_ids=("IT-LAP-001",),
        expected_contract_id="CON-2026-ACME-IT",
        expected_output_key="RFQ-001",
        seed_event_history=True,
        notes=(
            "Approved workflow with final approval history; ready for explicit "
            "resume."
        ),
    ),
    DemoWorkflowDefinition(
        key="rfq-001-completed-resumed-history",
        title="RFQ-001 workflow completed after approval resume",
        domain="it_equipment",
        initial_status=WorkflowStatus.COMPLETED,
        rfq_id="RFQ-001",
        customer_id="CUST-001",
        request_text=RFQ_001_TEXT,
        product_ids=("IT-LAP-001",),
        expected_contract_id="CON-2026-ACME-IT",
        expected_output_key="RFQ-001",
        seed_event_history=True,
        notes="Read-only example with request-changes, approval, and resume history.",
    ),
    DemoWorkflowDefinition(
        key="rfq-001-rejected-history",
        title="RFQ-001 workflow rejected after approval review",
        domain="it_equipment",
        initial_status=WorkflowStatus.REJECTED,
        rfq_id="RFQ-001",
        customer_id="CUST-001",
        request_text=RFQ_001_TEXT,
        product_ids=("IT-LAP-001",),
        expected_contract_id="CON-2026-ACME-IT",
        expected_output_key="RFQ-001",
        seed_event_history=True,
        notes="Read-only rejected approval history example.",
    ),
    DemoWorkflowDefinition(
        key="rfq-001-completed-conflict",
        title="RFQ-001 terminal workflow for run conflict demo",
        domain="it_equipment",
        initial_status=WorkflowStatus.COMPLETED,
        rfq_id="RFQ-001",
        customer_id="CUST-001",
        request_text=RFQ_001_TEXT,
        product_ids=("IT-LAP-001",),
        expected_contract_id="CON-2026-ACME-IT",
        expected_output_key="RFQ-001",
        notes="Optional conflict example for existing run precondition behavior.",
    ),
)

DEMO_WORKFLOW_EVENTS: tuple[DemoWorkflowEventDefinition, ...] = (
    DemoWorkflowEventDefinition(
        key="runtime-started",
        workflow_key="rfq-001-waiting-approval-history",
        event_type="workflow.runtime.started",
        status=WorkflowEventStatus.STARTED,
        message="Demo runtime started.",
        payload={"stage": "runtime", "demo_reference": True},
    ),
    DemoWorkflowEventDefinition(
        key="planner-completed",
        workflow_key="rfq-001-waiting-approval-history",
        event_type="workflow.node.completed",
        status=WorkflowEventStatus.COMPLETED,
        agent_name="planner",
        message="Demo planner stage completed.",
        payload={
            "stage": "planner",
            "workflow_status": WorkflowStatus.PLANNING.value,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="retrieval-completed",
        workflow_key="rfq-001-waiting-approval-history",
        event_type="workflow.node.completed",
        status=WorkflowEventStatus.COMPLETED,
        agent_name="retrieval",
        message="Demo retrieval stage completed with static contract reference.",
        payload={
            "stage": "retrieval",
            "workflow_status": WorkflowStatus.RETRIEVING.value,
            "contract_id": "CON-2026-ACME-IT",
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="quotation-completed",
        workflow_key="rfq-001-waiting-approval-history",
        event_type="workflow.node.completed",
        status=WorkflowEventStatus.COMPLETED,
        agent_name="quotation",
        message="Demo quotation stage completed with static expected output.",
        payload={
            "stage": "quotation",
            "workflow_status": WorkflowStatus.CALCULATING.value,
            "expected_total": 47628,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="waiting-approval",
        workflow_key="rfq-001-waiting-approval-history",
        event_type="workflow.runtime.waiting_for_approval",
        status=WorkflowEventStatus.COMPLETED,
        message="Demo workflow is waiting for approval.",
        payload={
            "stage": "approval",
            "workflow_status": WorkflowStatus.WAITING_APPROVAL.value,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="approved-ready-waiting-approval",
        workflow_key="rfq-001-approved-ready-to-resume",
        event_type="workflow.runtime.waiting_for_approval",
        status=WorkflowEventStatus.COMPLETED,
        message="Demo workflow reached approval before the seeded approval decision.",
        payload={
            "stage": "approval",
            "workflow_status": WorkflowStatus.WAITING_APPROVAL.value,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="approved-ready-approval-approved",
        workflow_key="rfq-001-approved-ready-to-resume",
        event_type=APPROVAL_APPROVED_EVENT,
        status=WorkflowEventStatus.COMPLETED,
        message="Demo workflow was approved and is ready to resume.",
        payload={
            "decision": "approve",
            "actor_email": "manager@example.test",
            "previous_status": WorkflowStatus.WAITING_APPROVAL.value,
            "next_status": WorkflowStatus.APPROVED.value,
            "can_resume": True,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="completed-history-approval-changes-requested",
        workflow_key="rfq-001-completed-resumed-history",
        event_type=APPROVAL_CHANGES_REQUESTED_EVENT,
        status=WorkflowEventStatus.COMPLETED,
        message="Demo manager requested changes before final approval.",
        payload={
            "decision": "request_changes",
            "actor_email": "manager@example.test",
            "previous_status": WorkflowStatus.WAITING_APPROVAL.value,
            "next_status": WorkflowStatus.WAITING_APPROVAL.value,
            "can_resume": False,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="completed-history-approval-approved",
        workflow_key="rfq-001-completed-resumed-history",
        event_type=APPROVAL_APPROVED_EVENT,
        status=WorkflowEventStatus.COMPLETED,
        message="Demo workflow was approved for post-approval continuation.",
        payload={
            "decision": "approve",
            "actor_email": "manager@example.test",
            "previous_status": WorkflowStatus.WAITING_APPROVAL.value,
            "next_status": WorkflowStatus.APPROVED.value,
            "can_resume": True,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="completed-history-resume-requested",
        workflow_key="rfq-001-completed-resumed-history",
        event_type=WORKFLOW_RESUME_REQUESTED_EVENT,
        status=WorkflowEventStatus.STARTED,
        message="Demo workflow resume was requested after approval.",
        payload={
            "workflow_status": WorkflowStatus.APPROVED.value,
            "request_id": "demo-resume-completed",
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="completed-history-email-preparation-started",
        workflow_key="rfq-001-completed-resumed-history",
        event_type="workflow.node.started",
        status=WorkflowEventStatus.STARTED,
        agent_name="email_preparation",
        message="Demo email preparation stage started.",
        payload={
            "stage": "email_preparation",
            "workflow_status": WorkflowStatus.GENERATING_EMAIL.value,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="completed-history-email-preparation-completed",
        workflow_key="rfq-001-completed-resumed-history",
        event_type="workflow.node.completed",
        status=WorkflowEventStatus.COMPLETED,
        agent_name="email_preparation",
        message="Demo email preparation stage completed without sending email.",
        payload={
            "stage": "email_preparation",
            "workflow_status": WorkflowStatus.GENERATING_EMAIL.value,
            "email_sent": False,
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="completed-history-workflow-resumed",
        workflow_key="rfq-001-completed-resumed-history",
        event_type=WORKFLOW_RESUMED_EVENT,
        status=WorkflowEventStatus.COMPLETED,
        message="Demo workflow resume completed.",
        payload={
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "request_id": "demo-resume-completed",
            "completed_stages": "email_preparation",
            "demo_reference": True,
        },
    ),
    DemoWorkflowEventDefinition(
        key="rejected-history-approval-rejected",
        workflow_key="rfq-001-rejected-history",
        event_type=APPROVAL_REJECTED_EVENT,
        status=WorkflowEventStatus.COMPLETED,
        message="Demo workflow was rejected during approval review.",
        payload={
            "decision": "reject",
            "actor_email": "manager@example.test",
            "previous_status": WorkflowStatus.WAITING_APPROVAL.value,
            "next_status": WorkflowStatus.REJECTED.value,
            "can_resume": False,
            "demo_reference": True,
        },
    ),
)

DEMO_SEED_CONTRACT = DemoSeedContract(
    dataset_references=DATASET_REFERENCES,
    credentials=DEMO_CREDENTIALS,
    roles=DEMO_ROLES,
    users=DEMO_USERS,
    workflows=DEMO_WORKFLOWS,
    workflow_events=DEMO_WORKFLOW_EVENTS,
)

__all__ = [
    "DATASET_REFERENCES",
    "DEMO_CREDENTIALS",
    "DEMO_PASSWORD",
    "DEMO_ROLES",
    "DEMO_SEED_CONTRACT",
    "DEMO_SEED_NAMESPACE",
    "DEMO_USERS",
    "DEMO_WORKFLOW_EVENTS",
    "DEMO_WORKFLOWS",
    "DemoCredential",
    "DemoDatasetReference",
    "DemoRoleDefinition",
    "DemoSeedContract",
    "DemoUserDefinition",
    "DemoWorkflowDefinition",
    "DemoWorkflowEventDefinition",
    "deterministic_demo_uuid",
]
