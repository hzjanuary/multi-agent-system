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

Current active spec:

- SPEC-010 Demo Dataset Seeding and Demo Script

## Current SPEC-010 Planning State

Planning files:

- `.ai/specs/SPEC-010-demo-dataset-and-script/spec.md`
- `.ai/specs/SPEC-010-demo-dataset-and-script/tasks.md`

Planned tasks:

- `TASK 010.1 - Demo Dataset Inventory and Seed Contract` - Implemented,
  awaiting review
- `TASK 010.2 - Demo User and Role Seeding`
- `TASK 010.3 - Demo Workflow and Event Seeding`
- `TASK 010.4 - Demo Seed CLI/Script`
- `TASK 010.5 - Demo Runbook and Frontend Smoke Flow`
- `TASK 010.6 - Demo Hardening and SPEC-010 Final Review`

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
