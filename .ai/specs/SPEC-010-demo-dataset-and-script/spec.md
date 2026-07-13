# SPEC-010 - Demo Dataset Seeding and Demo Script

## Status

Draft

## Context

Enterprise Multi-Agent OS now has the end-to-end foundation needed for a
board-ready local demonstration:

- SPEC-005 provides durable workflow state, lifecycle rules, workflow events,
  and audit integration.
- SPEC-006 provides deterministic runtime execution that runs a workflow to
  `WAITING_APPROVAL`.
- SPEC-007 exposes authenticated workflow REST APIs.
- SPEC-008 exposes workflow event streaming over WebSocket.
- SPEC-009 provides the first frontend dashboard for login, workflow browsing,
  workflow creation, runtime execution, and live event timeline viewing.

The repository also contains a static `datasets/` folder with customers,
products, pricing rules, contracts, policies, sample RFQs, document index data,
and expected quotation outputs. SPEC-010 turns those assets into a controlled
local demo experience through deterministic seeding and a clear runbook. It
does not implement real Agent intelligence, real procurement pricing logic,
RAG, or production seed management.

## Goals

- Make the project ready for a repeatable board/demo walkthrough.
- Define deterministic local seed data for demo users, roles, workflows, and
  workflow event history.
- Use existing models, services, auth/RBAC, workflow APIs, runtime, streaming,
  and frontend behavior.
- Seed demo users for existing roles: Admin, Manager, Sales, Legal, Finance,
  and Viewer.
- Seed procurement workflow examples that support workflow list/detail,
  persisted events, runtime run, and live event timeline demonstrations.
- Use existing dataset RFQs and expected outputs as reference/demo payloads
  where practical.
- Provide a documented demo runbook from Docker startup through frontend
  walkthrough.
- Keep seeding idempotent, local/demo-safe, and explicitly non-production.

## Non-goals

- Real LLM provider behavior.
- Real Agents or autonomous reasoning.
- RAG, embeddings, document indexing, or vector search population.
- Real procurement pricing, compliance, retrieval, validation, or policy
  engines.
- `/resume` or human approval continuation.
- Approval/rejection UI.
- Admin user-management UI.
- Production seed management.
- Deployment automation.
- Screenshot or video generation.
- New backend API endpoints.
- Frontend feature changes.
- Database model changes or migrations.

## Demo Goal

The demo should show Enterprise Procurement Workflow Automation through a
bounded, repeatable flow:

1. Start backend infrastructure.
2. Apply database migrations.
3. Run a deterministic demo seed command.
4. Start the frontend.
5. Log in as Admin or Manager.
6. View seeded workflows.
7. Create a new procurement quotation workflow.
8. Run the workflow to `WAITING_APPROVAL`.
9. Watch persisted events and live timeline updates.
10. Briefly demonstrate RBAC with a read-only or denied action role.

The primary demo narrative is based on RFQ-001:

```text
We would like to purchase 50 standard business laptops for a new operations
team. We signed a master agreement in May 2026. Please provide your best
quotation with the applicable discount.
```

Expected demo reference points:

- Domain: `it_equipment`
- Customer: Acme Manufacturing Group
- Contract: `CON-2026-ACME-IT`
- Expected total: `47628 USD`
- Runtime stopping point: `WAITING_APPROVAL`

Because real Agent/tool implementations are deferred, SPEC-010 seed data may
show reference outputs as static demo metadata or event payloads. It must not
claim that real pricing, retrieval, compliance, or email generation logic has
been implemented.

## Demo Data Scope

SPEC-010 should define and seed only local deterministic demo records.

### Demo Users

Seed one user for each existing role:

| Role | Purpose |
| --- | --- |
| Admin | Full system walkthrough and validation |
| Manager | Runtime run and approval-stage narrative |
| Sales | Workflow creation and tracking |
| Legal | Read-only compliance-review perspective |
| Finance | Read-only pricing-review perspective |
| Viewer | Read-only observer perspective |

Demo credentials must be documented only as local demo credentials with obvious
demo-only passwords. They must not be presented as production guidance.

### Demo Workflows

Seed examples should be deterministic and generic enough to survive future
runtime changes:

- Clean procurement workflow based on RFQ-001, ready to run or already at
  `CREATED`.
- Workflow that has already reached `WAITING_APPROVAL` with representative
  persisted event history.
- Optional conflict/precondition example, if useful, such as a terminal workflow
  that demonstrates the UI/API handling a run conflict.
- Optional workflow with a richer existing event history for timeline demo.

Seeded workflow state should use existing `WorkflowState` schemas and existing
`WorkflowStatus` enum values. Workflow events should use the existing
`WorkflowEvent` model and event service behavior where practical.

### Static Reference Data

Existing static dataset files may be used as source/reference material:

- `datasets/customers.csv` and `datasets/customers.json`
- `datasets/products.csv` and `datasets/products.json`
- `datasets/pricing_rules.csv` and `datasets/pricing_rules.json`
- `datasets/contracts/*.md`
- `datasets/policies/*.md`
- `datasets/rfqs/rfq_samples.json`
- `datasets/expected_outputs/expected_quotes.json`
- `datasets/index/document_index.json`

SPEC-010 must not turn this into real retrieval, pricing, compliance, or RAG
logic. Static reference values may be embedded into seed workflow metadata,
stage outputs, or event payloads only when clearly marked as demo/reference
data.

## Seed Architecture

Implementation should add an explicit deterministic seed entrypoint, such as a
Python module or CLI script, that can run inside the existing backend
environment.

Requirements:

- Idempotent: rerunning the seed command updates or preserves known demo records
  without creating uncontrolled duplicates.
- Local/demo-safe: it must not run automatically in production.
- Explicit: the user must invoke the seed command.
- Existing-model first: reuse `User`, `Role`, `Workflow`, `WorkflowEvent`, and
  existing enums.
- Existing-service aware: prefer using existing services for workflow creation,
  event append, and status/state behavior where that remains pragmatic.
- Transactionally clear: seed command owns its transaction boundaries and
  reports success or failure.
- Bounded payloads: demo workflow and event payloads must remain JSON-compatible
  and safe.
- No real secrets: demo passwords must be obvious and generated/hashed through
  existing password utilities.

Direct repository/model writes are acceptable for seed setup where services do
not exist yet, especially for demo users and roles, but the plan should prefer
the service layer for workflow behavior when practical.

## Demo Credentials

The runbook should document local demo credentials in this style:

```text
admin@example.test / DemoPassword123!
manager@example.test / DemoPassword123!
sales@example.test / DemoPassword123!
legal@example.test / DemoPassword123!
finance@example.test / DemoPassword123!
viewer@example.test / DemoPassword123!
```

The exact emails may change during implementation, but credentials must be:

- clearly demo-only
- safe to commit
- never reused as production defaults
- clearly scoped to local development/demo environments

## Demo Runbook Scope

SPEC-010 should add a demo runbook that covers:

1. Prerequisites: Docker Desktop, Node.js/npm, and local repo checkout.
2. Start infrastructure and backend.
3. Apply database migrations.
4. Run the demo seed command.
5. Start the frontend.
6. Log in as Manager or Admin.
7. View seeded workflows.
8. Create a new procurement workflow from RFQ-001 text.
9. Run the workflow.
10. Watch workflow status, persisted events, and live timeline updates.
11. Show RBAC behavior with a denied or read-only role.

The runbook should include expected checkpoints rather than generated
screenshots by default.

## Troubleshooting

The runbook should include bounded troubleshooting notes for:

- Docker daemon not running.
- PostgreSQL service not healthy.
- Migrations not applied.
- Seed command rerun behavior.
- Frontend cannot reach backend.
- WebSocket connection rejected because the token is missing or expired.
- Redis unavailable, causing live stream delivery to fail while persisted
  events remain available.
- Demo user password or role mismatch.

## Architecture Notes

SPEC-010 should preserve existing boundaries:

```text
Seed command -> existing backend services/repositories/models -> database
Frontend demo -> existing auth/workflow/runtime/streaming APIs
```

The seed command is an operational tool, not a runtime feature. It should not
modify public API contracts or frontend behavior. It should use the current
backend stack and keep all seeded data typed and explicit.

## User Stories

### Demo Operator - Seed Local Demo Data

As a demo operator, I want one command to seed demo users and workflows so that
the system can be shown without manual database setup.

### Reviewer - Walk Through A Procurement Workflow

As a reviewer, I want to see login, workflow list, workflow creation, runtime
execution, persisted events, and live timeline updates in one coherent demo.

### Evaluator - Understand RBAC And Workflow Roles

As an evaluator, I want to see that different human roles exist and that the
demo can show both allowed and denied workflow operations.

## Acceptance Criteria

```gherkin
Given a clean local database
When the demo seed command runs
Then demo users for Admin, Manager, Sales, Legal, Finance, and Viewer exist
And their roles are assigned deterministically
```

```gherkin
Given demo data has been seeded
When an Admin or Manager logs in through the frontend
Then seeded workflows are visible in the workflow list
```

```gherkin
Given a seeded workflow has event history
When the workflow detail page is opened
Then persisted events appear in the timeline
```

```gherkin
Given a created demo workflow is run
When the deterministic runtime completes its pre-approval path
Then the workflow reaches WAITING_APPROVAL
And runtime events are persisted
And live stream delivery can show the event timeline
```

```gherkin
Given a demo user has a role without run permission
When that user attempts a restricted action
Then the backend returns the existing RBAC error behavior
And the frontend displays a bounded error state
```

```gherkin
Given the demo seed command is run more than once
When it completes
Then it does not create uncontrolled duplicate demo users, workflows, or events
```

## Validation Strategy

Planning-only validation for SPEC-010:

```bash
git status --short
docker-compose config
git diff --check
```

Implementation tasks should use focused backend and frontend validation as
appropriate:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

Seed-specific validation should prove:

- seed command can run against a clean local database
- seed command can run twice without duplicate records
- demo users can authenticate
- seeded workflow list/detail data is visible through existing APIs
- seeded events are visible through REST event reads
- runtime run still reaches `WAITING_APPROVAL`
- WebSocket stream remains compatible with existing event delivery

## Out-of-scope List

- Real LLM providers.
- Real Agents or autonomous reasoning.
- RAG, embeddings, document upload, or document indexing.
- Real procurement pricing, retrieval, compliance, validation, or policy logic.
- `/resume` and human approval continuation.
- Email sending.
- Admin user-management UI.
- Production seed management.
- Deployment automation.
- Screenshot or video generation.
- New backend API endpoints.
- Frontend feature changes.
- Database model changes or migrations.
