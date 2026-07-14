# Context Handoff

## Current Project Status

Closed specs:

- SPEC-001 Bootstrap Backend - Approved / Closed
- SPEC-002 Database Foundation - Approved / Closed
- SPEC-003 Authentication and RBAC - Approved / Closed
- SPEC-004 Storage Infrastructure - Approved / Closed
- SPEC-005 Workflow State - Approved / Closed
- SPEC-006 LangGraph Runtime - Approved / Closed
- SPEC-007 Workflow API Endpoints - Approved / Closed
- SPEC-008 Event Streaming - Approved / Closed
- SPEC-009 Frontend Dashboard - Approved / Closed
- SPEC-010 Demo Dataset Seeding and Demo Script - Approved / Closed

Current active spec:

- None

## Current SPEC-010 Planning State

Planning files:

- `.ai/specs/SPEC-010-demo-dataset-and-script/spec.md`
- `.ai/specs/SPEC-010-demo-dataset-and-script/tasks.md`

Planned tasks:

- `TASK 010.1 - Demo Dataset Inventory and Seed Contract` - Approved
- `TASK 010.2 - Demo User and Role Seeding` - Approved
- `TASK 010.3 - Demo Workflow and Event Seeding` - Approved
- `TASK 010.4 - Demo Seed CLI/Script` - Approved
- `TASK 010.5 - Demo Runbook and Frontend Smoke Flow` - Approved
- `TASK 010.6 - Demo Hardening and SPEC-010 Final Review` - Approved

## TASK 010.1 Implementation State

Deliverables:

- `backend/app/demo/__init__.py`
- `backend/app/demo/contracts.py`
- `backend/app/tests/test_demo_seed_contracts.py`
- `docs/demo/DATASET_INVENTORY.md`

Behavior:

- Adds immutable Pydantic v2 contracts for demo dataset references, demo
  credentials, demo roles, demo users, demo workflow definitions, and demo
  workflow event definitions.
- Defines local-demo-only credentials for Admin, Manager, Sales, Legal, Finance,
  and Viewer using `@example.test` emails and the obvious
  `DemoPassword123!` password.
- Defines deterministic natural idempotency keys:
  `demo:role:{role_name}`, `demo:user:{email}`,
  `demo:workflow:{workflow_key}`, and
  `demo:event:{workflow_key}:{event_key}`.
- Defines deterministic UUID helper `deterministic_demo_uuid()` for future seed
  implementations.
- Inventories the existing dataset files and primary RFQ-001 demo path.
- Adds unit tests for role coverage, credential safety, unique keys, stable
  UUID behavior, workflow/event definitions, dataset path declarations, and
  JSON serialization.
- Does not implement database seeding, seed CLI/script execution, auth/RBAC
  behavior changes, workflow/event persistence, backend API changes, frontend
  behavior changes, migrations, or database model changes.

## TASK 010.2 Implementation State

Deliverables:

- `backend/app/demo/user_seed.py`
- `backend/app/tests/test_demo_user_seed.py`
- `docs/demo/DATASET_INVENTORY.md` updated with helper notes

Behavior:

- Adds explicit `seed_demo_roles_and_users(session)` helper for local/demo
  roles and users only.
- Uses existing `User` and `Role` SQLAlchemy models.
- Uses existing Argon2 password utilities for password hashing and verification.
- Seeds/reuses the six existing RBAC roles: Admin, Manager, Sales, Legal,
  Finance, and Viewer.
- Seeds/reuses one local-demo user per role from the TASK 010.1 contracts.
- Flushes changes but does not commit; callers own transaction boundaries.
- Idempotently reuses existing roles/users and avoids duplicate role
  assignments.
- Refreshes only safe local-demo user fields when needed: full name, active
  state, superuser flag, and demo password hash.
- Does not delete or modify non-demo users/roles.
- Does not seed workflows, seed workflow events, expose a public API, implement
  a seed CLI/script, change auth/RBAC policy, change backend/frontend behavior,
  add migrations, or modify database models.

## TASK 010.3 Implementation State

Deliverables:

- `backend/app/demo/workflow_seed.py`
- `backend/app/tests/test_demo_workflow_seed.py`
- `docs/demo/DATASET_INVENTORY.md` updated with workflow/event seed notes

Behavior:

- Adds explicit `seed_demo_workflows_and_events(session)` helper for local/demo
  workflows and persisted workflow events only.
- Ensures demo users/roles through the TASK 010.2 helper before assigning
  workflow creator ownership to the Sales demo user.
- Uses existing `Workflow` and `WorkflowEvent` SQLAlchemy models.
- Uses existing `WorkflowState` and `WorkflowStateMetadata` schemas to validate
  JSON-compatible state payloads before persistence.
- Seeds/reuses the contract-defined deterministic RFQ-001 workflow examples:
  `CREATED`, `WAITING_APPROVAL` with event history, and terminal `COMPLETED`.
- Seeds/reuses deterministic workflow events for the waiting-approval history
  workflow.
- Uses stable UUIDv5 IDs from the TASK 010.1 contract for workflow/event
  idempotency without adding model columns or migrations.
- Stores demo idempotency keys and `demo_reference_only` markers in workflow
  metadata/request payloads and event payloads.
- Assigns deterministic event timestamps so event readback order is stable.
- Flushes changes but does not commit; callers own transaction boundaries.
- Does not call RuntimeService, run workflows, publish Redis events, expose a
  public API, implement a seed CLI/script, change backend/frontend behavior,
  add migrations, or modify database models.

## TASK 010.4 Implementation State

Deliverables:

- `backend/app/demo/seed.py`
- `backend/app/tests/test_demo_seed_cli.py`
- `backend/README.md` updated with the seed command
- `docs/demo/DATASET_INVENTORY.md` updated with the seed command

Behavior:

- Adds explicit `python -m app.demo.seed --confirm-local-demo` CLI for local
  demo seeding only.
- Adds `run_demo_seed()` orchestration that runs
  `seed_demo_roles_and_users(session)` and
  `seed_demo_workflows_and_events(session)` inside one session/transaction.
- Commits once after all seed steps succeed.
- Rolls back if any seed step fails.
- Supports `--dry-run` to execute seed steps and rollback instead of committing.
- Supports `--json` for a bounded machine-readable summary.
- Requires `--confirm-local-demo` for mutating execution.
- Does not run on import, backend startup, or through a public API endpoint.
- Does not add backend/frontend behavior changes, migrations, or model changes.

## TASK 010.5 Implementation State

Deliverables:

- `docs/demo/DEMO_RUNBOOK.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
- `backend/README.md` updated with runbook links
- `frontend/README.md` updated with runbook links
- `README.md` updated with runbook links

Behavior:

- Documents the local board-ready demo purpose, prerequisites, backend setup,
  migrations, seed command, frontend setup, demo credentials, seeded workflow
  IDs, board walkthrough steps, expected checkpoints, and troubleshooting.
- Documents a deterministic frontend smoke checklist for login, navigation,
  workflow list/detail, persisted event backlog, live timeline, workflow
  creation, runtime run, and RBAC denial behavior.
- Documents known limitations: no `/resume`, no real LLM provider behavior, no
  RAG/document upload UI, no admin user-management UI, no production deployment
  automation, and no fake live events.
- Does not add backend/frontend behavior changes, migrations, model changes,
  seed data changes, runtime changes, or new dependencies.

## TASK 010.6 Final Review State

Status:

- SPEC-010 approved and ready to close.

Evidence:

- Verified dataset inventory, contracts, demo credentials, deterministic keys,
  deterministic UUIDs, user/role seed helper, workflow/event seed helper, seed
  CLI, runbook, smoke flow, README links, and out-of-scope boundaries.
- Hardened tests so the full backend suite passes after demo seed data has
  already been committed to the local database.
- Validation passed: `docker-compose config`, Postgres startup, Alembic
  upgrade, `docker-compose build backend-test`, backend pytest, Ruff, Black,
  MyPy, seed CLI help, two confirmed JSON seed runs, dry-run JSON seed run,
  frontend install, lint, build, typecheck, tests, and `git diff --check`.

Non-blocking notes:

- Existing LangGraph pending deprecation warning remains non-blocking.
- Existing Starlette TestClient deprecation warning remains non-blocking.
- Existing frontend npm audit advisories remain a future dependency
  maintenance item.
- Optional live browser smoke was not run because no frontend dev server was
  already listening; frontend build generated the documented routes.

## SPEC-010 Scope

- Deterministic local/demo seed data for Enterprise Procurement Workflow
  Automation.
- Demo users for existing roles: Admin, Manager, Sales, Legal, Finance, and
  Viewer.
- Seeded procurement workflow examples using existing WorkflowState,
  WorkflowStatus, WorkflowService, WorkflowEventService, auth, and RBAC
  foundations where practical.
- Demo event history for workflow list/detail, persisted event reads, and live
  WebSocket timeline demonstration.
- A clear local demo runbook covering backend startup, migrations, seed command,
  frontend startup, login, workflow list/detail, create workflow, run workflow,
  event timeline, and RBAC behavior.

## SPEC-010 Deferrals

- Real LLM provider behavior.
- Real Agents or autonomous reasoning.
- RAG, embeddings, document upload, or document indexing.
- Real procurement pricing, retrieval, compliance, validation, or policy
  engines.
- `/resume` and human approval continuation.
- Approval/rejection UI.
- Admin user-management UI.
- Production seed management.
- Deployment automation.
- Screenshot or video generation.
- Backend API changes.
- Frontend feature changes.
- Database model changes or migrations.

## Existing Dataset Assets

The repository already contains static demo data under `datasets/`:

- `customers.csv` and `customers.json`
- `products.csv` and `products.json`
- `pricing_rules.csv` and `pricing_rules.json`
- `contracts/*.md`
- `policies/*.md`
- `rfqs/rfq_samples.json`
- `expected_outputs/expected_quotes.json`
- `index/document_index.json`

RFQ-001 is the recommended primary demo path:

- Domain: `it_equipment`
- Contract: `CON-2026-ACME-IT`
- Expected total: `47628 USD`
- Runtime endpoint should still stop at `WAITING_APPROVAL`

## Expected SPEC-010 Planning Quality Gate

```bash
git status --short
docker-compose config
git diff --check
```

Implementation tasks should add backend seed tests, frontend smoke checks, and
idempotency validation after seed code exists.

## Harness State

- SPEC-005 final review recorded and approved.
- SPEC-006 final review recorded and approved.
- SPEC-007 final review recorded and approved.
- SPEC-008 final validation approved.
- SPEC-009 final review recorded and approved with Harness trace #85.
- SPEC-010 planning recorded with Harness intake #73.

## Known Warnings

- Existing FastAPI/TestClient StarletteDeprecationWarning is non-blocking.
- Frontend npm audit findings from SPEC-009 are non-blocking until addressed by
  a dependency-maintenance task.
- LF/CRLF warnings from `git diff --check` are non-blocking when no whitespace
  errors are reported.
