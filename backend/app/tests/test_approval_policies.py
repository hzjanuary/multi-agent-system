"""Tests for approval RBAC policy helpers."""

import pytest

from app.approvals import (
    APPROVAL_FINAL_DECISION_ROLES,
    APPROVAL_READ_ROLES,
    APPROVAL_RESUME_ROLES,
    ApprovalDecisionType,
    can_read_approval_history,
    can_resume_workflow,
    can_submit_approval_decision,
)
from app.auth.rbac import RoleName


@pytest.mark.parametrize("role", (RoleName.ADMIN, RoleName.MANAGER))
def test_admin_and_manager_can_submit_final_decisions(role: RoleName) -> None:
    assert can_submit_approval_decision([role], ApprovalDecisionType.APPROVE) is True
    assert can_submit_approval_decision([role], ApprovalDecisionType.REJECT) is True
    assert (
        can_submit_approval_decision([role], ApprovalDecisionType.REQUEST_CHANGES)
        is True
    )
    assert can_resume_workflow([role]) is True


@pytest.mark.parametrize(
    "role",
    (RoleName.SALES, RoleName.LEGAL, RoleName.FINANCE, RoleName.VIEWER),
)
def test_non_approval_roles_cannot_mutate_approval(role: RoleName) -> None:
    assert can_submit_approval_decision([role], ApprovalDecisionType.APPROVE) is False
    assert can_submit_approval_decision([role], ApprovalDecisionType.REJECT) is False
    assert (
        can_submit_approval_decision([role], ApprovalDecisionType.REQUEST_CHANGES)
        is False
    )
    assert can_resume_workflow([role]) is False


def test_viewer_is_read_only_for_approval_history() -> None:
    assert can_read_approval_history([RoleName.VIEWER]) is True
    assert (
        can_submit_approval_decision(
            [RoleName.VIEWER],
            ApprovalDecisionType.REQUEST_CHANGES,
        )
        is False
    )


def test_unknown_or_empty_roles_are_denied() -> None:
    assert can_submit_approval_decision([], ApprovalDecisionType.APPROVE) is False
    assert can_resume_workflow(["Unknown"]) is False
    assert can_read_approval_history(["Unknown"]) is False


def test_policy_constants_use_existing_roles_only() -> None:
    assert {RoleName.ADMIN, RoleName.MANAGER} == APPROVAL_FINAL_DECISION_ROLES
    assert {RoleName.ADMIN, RoleName.MANAGER} == APPROVAL_RESUME_ROLES
    assert set(RoleName) == APPROVAL_READ_ROLES
