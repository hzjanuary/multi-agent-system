"""Pure RBAC policy helpers for approval and resume actions."""

from collections.abc import Iterable

from app.approvals.schemas import ApprovalDecisionType
from app.auth.rbac import RoleName, normalize_role_name

APPROVAL_FINAL_DECISION_ROLES: frozenset[RoleName] = frozenset(
    {
        RoleName.ADMIN,
        RoleName.MANAGER,
    },
)
APPROVAL_REQUEST_CHANGES_ROLES: frozenset[RoleName] = APPROVAL_FINAL_DECISION_ROLES
APPROVAL_RESUME_ROLES: frozenset[RoleName] = APPROVAL_FINAL_DECISION_ROLES
APPROVAL_READ_ROLES: frozenset[RoleName] = frozenset(RoleName)


def can_submit_approval_decision(
    role_names: Iterable[str | RoleName],
    decision: ApprovalDecisionType,
) -> bool:
    """Return whether any role can submit the requested decision."""
    normalized_roles = _normalize_roles(role_names)
    if decision is ApprovalDecisionType.REQUEST_CHANGES:
        allowed_roles = _role_values(APPROVAL_REQUEST_CHANGES_ROLES)
    else:
        allowed_roles = _role_values(APPROVAL_FINAL_DECISION_ROLES)
    return not normalized_roles.isdisjoint(allowed_roles)


def can_resume_workflow(role_names: Iterable[str | RoleName]) -> bool:
    """Return whether any role can resume a post-approval workflow."""
    return not _normalize_roles(role_names).isdisjoint(
        _role_values(APPROVAL_RESUME_ROLES)
    )


def can_read_approval_history(role_names: Iterable[str | RoleName]) -> bool:
    """Return whether any role can read approval history via workflow read access."""
    return not _normalize_roles(role_names).isdisjoint(
        _role_values(APPROVAL_READ_ROLES)
    )


def _normalize_roles(role_names: Iterable[str | RoleName]) -> set[str]:
    return {normalize_role_name(role) for role in role_names}


def _role_values(role_names: Iterable[RoleName]) -> set[str]:
    return {role.value for role in role_names}
