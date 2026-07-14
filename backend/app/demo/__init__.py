"""Demo dataset seed contracts for local board-ready walkthroughs."""

from app.demo.contracts import (
    DATASET_REFERENCES,
    DEMO_CREDENTIALS,
    DEMO_ROLES,
    DEMO_SEED_CONTRACT,
    DEMO_USERS,
    DEMO_WORKFLOW_EVENTS,
    DEMO_WORKFLOWS,
    DemoCredential,
    DemoDatasetReference,
    DemoRoleDefinition,
    DemoSeedContract,
    DemoUserDefinition,
    DemoWorkflowDefinition,
    DemoWorkflowEventDefinition,
    deterministic_demo_uuid,
)
from app.demo.user_seed import DemoUserSeedResult, seed_demo_roles_and_users
from app.demo.workflow_seed import (
    DemoWorkflowSeedResult,
    seed_demo_workflows_and_events,
)

__all__ = [
    "DATASET_REFERENCES",
    "DEMO_CREDENTIALS",
    "DEMO_ROLES",
    "DEMO_SEED_CONTRACT",
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
    "DemoWorkflowSeedResult",
    "DemoUserSeedResult",
    "deterministic_demo_uuid",
    "seed_demo_roles_and_users",
    "seed_demo_workflows_and_events",
]
