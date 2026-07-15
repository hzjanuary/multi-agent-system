"""Tests for SPEC-010 demo seed contracts."""

from pathlib import Path
from uuid import UUID

import pytest

from app.approvals import (
    APPROVAL_APPROVED_EVENT,
    APPROVAL_CHANGES_REQUESTED_EVENT,
    APPROVAL_REJECTED_EVENT,
    WORKFLOW_RESUME_REQUESTED_EVENT,
    WORKFLOW_RESUMED_EVENT,
)
from app.auth.rbac import RoleName
from app.demo import (
    DATASET_REFERENCES,
    DEMO_CREDENTIALS,
    DEMO_ROLES,
    DEMO_SEED_CONTRACT,
    DEMO_USERS,
    DEMO_WORKFLOW_EVENTS,
    DEMO_WORKFLOWS,
    DemoCredential,
    deterministic_demo_uuid,
)
from app.models.enums import WorkflowStatus


def test_demo_roles_cover_existing_rbac_roles() -> None:
    assert {role.role_name for role in DEMO_ROLES} == set(RoleName)
    assert {user.role_name for user in DEMO_USERS} == set(RoleName)


def test_demo_credentials_are_local_demo_only() -> None:
    for credential in DEMO_CREDENTIALS:
        assert credential.is_demo_only is True
        assert credential.email.endswith("@example.test")
        assert "Demo" in credential.password
        assert "production" in credential.usage_note.lower()


def test_demo_credential_rejects_non_demo_email() -> None:
    with pytest.raises(ValueError, match="@example.test"):
        DemoCredential(
            key="bad",
            email="admin@example.com",
            password="DemoPassword123!",
            usage_note="Local demo only.",
        )


def test_demo_contract_keys_are_unique() -> None:
    key_sets = (
        [reference.key for reference in DATASET_REFERENCES],
        [credential.key for credential in DEMO_CREDENTIALS],
        [role.key for role in DEMO_ROLES],
        [user.key for user in DEMO_USERS],
        [workflow.key for workflow in DEMO_WORKFLOWS],
        [event.key for event in DEMO_WORKFLOW_EVENTS],
    )

    for keys in key_sets:
        assert len(keys) == len(set(keys))


def test_demo_idempotency_keys_are_unique_and_stable() -> None:
    idempotency_keys = [
        *(role.idempotency_key for role in DEMO_ROLES),
        *(user.idempotency_key for user in DEMO_USERS),
        *(workflow.idempotency_key for workflow in DEMO_WORKFLOWS),
        *(event.idempotency_key for event in DEMO_WORKFLOW_EVENTS),
    ]

    assert len(idempotency_keys) == len(set(idempotency_keys))
    assert deterministic_demo_uuid("demo:user:admin@example.test") == UUID(
        "42c3a4bd-9523-586b-8ed9-99b301e7dff5",
    )
    assert DEMO_USERS[0].stable_user_id == deterministic_demo_uuid(
        DEMO_USERS[0].idempotency_key,
    )
    assert DEMO_WORKFLOWS[0].stable_workflow_id == deterministic_demo_uuid(
        DEMO_WORKFLOWS[0].idempotency_key,
    )


def test_demo_workflow_definitions_have_required_demo_shapes() -> None:
    workflow_by_key = {workflow.key: workflow for workflow in DEMO_WORKFLOWS}

    assert workflow_by_key["rfq-001-clean-created"].initial_status is (
        WorkflowStatus.CREATED
    )
    assert (
        workflow_by_key["rfq-001-waiting-approval-history"].initial_status
        is WorkflowStatus.WAITING_APPROVAL
    )
    assert (
        workflow_by_key["rfq-001-approved-ready-to-resume"].initial_status
        is WorkflowStatus.APPROVED
    )
    assert (
        workflow_by_key["rfq-001-completed-resumed-history"].initial_status
        is WorkflowStatus.COMPLETED
    )
    assert workflow_by_key["rfq-001-rejected-history"].initial_status is (
        WorkflowStatus.REJECTED
    )
    assert workflow_by_key["rfq-001-completed-conflict"].initial_status is (
        WorkflowStatus.COMPLETED
    )

    for workflow in DEMO_WORKFLOWS:
        assert workflow.rfq_id == "RFQ-001"
        assert workflow.customer_id == "CUST-001"
        assert workflow.product_ids == ("IT-LAP-001",)
        assert workflow.expected_contract_id == "CON-2026-ACME-IT"
        assert workflow.expected_output_key == "RFQ-001"
        assert workflow.request_text


def test_demo_event_definitions_reference_seeded_workflow() -> None:
    workflow_keys = {workflow.key for workflow in DEMO_WORKFLOWS}
    approval_event_types = {
        APPROVAL_APPROVED_EVENT,
        APPROVAL_CHANGES_REQUESTED_EVENT,
        APPROVAL_REJECTED_EVENT,
        WORKFLOW_RESUME_REQUESTED_EVENT,
        WORKFLOW_RESUMED_EVENT,
    }

    for event in DEMO_WORKFLOW_EVENTS:
        assert event.workflow_key in workflow_keys
        assert event.payload["demo_reference"] is True
        assert event.idempotency_key.startswith("demo:event:")

    event_types = {event.event_type for event in DEMO_WORKFLOW_EVENTS}
    assert approval_event_types <= event_types


def test_dataset_references_are_declared_and_exist_when_available() -> None:
    assert {reference.key for reference in DATASET_REFERENCES} >= {
        "customers-json",
        "products-json",
        "pricing-rules-json",
        "contracts",
        "policies",
        "rfq-samples",
        "expected-quotes",
    }

    repo_root = _repo_root_if_available()
    if repo_root is None:
        pytest.skip("repository dataset directory is not available in this image")

    for reference in DATASET_REFERENCES:
        assert (repo_root / reference.path).exists()


def test_demo_seed_contract_is_json_serializable() -> None:
    dumped = DEMO_SEED_CONTRACT.model_dump(mode="json")

    assert dumped["credentials"][0]["email"] == "admin@example.test"
    assert dumped["roles"][0]["role_name"] == RoleName.ADMIN.value
    assert dumped["workflows"][0]["initial_status"] == WorkflowStatus.CREATED.value


def _repo_root_if_available() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "datasets").exists():
            return parent
    return None
