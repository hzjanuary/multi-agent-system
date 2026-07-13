# SPEC-010 - Demo Dataset Seeding and Demo Script Tasks

## TASK 010.1 - Demo Dataset Inventory and Seed Contract

### Objective

Inventory the existing static demo dataset and define the typed seed contract
for demo users, workflows, events, and runbook expectations.

### Scope

- Inspect `datasets/` files and identify the records needed for the primary
  demo flow.
- Define deterministic demo user identities and role mapping.
- Define deterministic workflow examples and event history shape.
- Define idempotency keys or natural identifiers for seeded records.
- Define seed safety rules for local/demo-only execution.
- Add or update documentation for the seed data contract.

### Deliverables

- Demo seed contract documentation or module-level plan.
- Confirmed demo user matrix.
- Confirmed workflow/event seed inventory.
- Test plan for seed idempotency and local safety.
- README or runbook notes if useful.

### Acceptance Criteria

- Existing dataset assets are inventoried.
- Demo users for Admin, Manager, Sales, Legal, Finance, and Viewer are planned.
- Demo workflow examples are clearly named and bounded.
- Seed idempotency approach is documented.
- No seed execution code is added unless explicitly scoped by a later task.
- No backend/frontend app behavior, migrations, or model changes are made.

### Out-of-scope

- Executable seed script.
- Demo user creation code.
- Workflow/event seeding code.
- Real pricing, retrieval, compliance, RAG, or LLM behavior.
- Backend API or frontend feature changes.

### Validation Commands

```bash
git status --short
docker-compose config
git diff --check
```

## TASK 010.2 - Demo User and Role Seeding

### Objective

Implement deterministic local/demo user and role seeding using existing auth,
password, user, and role models.

### Scope

- Add a backend-local seed helper for demo users.
- Ensure roles exist for Admin, Manager, Sales, Legal, Finance, and Viewer.
- Create or update one demo user per role.
- Hash demo passwords through existing password utilities.
- Make reruns idempotent.
- Keep the command local/demo-safe and clearly documented.
- Add tests for user creation, role assignment, idempotency, and password
  authentication where practical.

### Deliverables

- Demo user seed implementation.
- Tests for demo user/role seed behavior.
- Documentation of local demo credentials.
- Safety notes that credentials are development-only.

### Acceptance Criteria

- Demo users can be seeded into a clean database.
- Re-running the seed does not create duplicate demo users or roles.
- Demo passwords are hashed with existing auth utilities.
- Demo credentials are documented as local-only.
- Existing auth/RBAC behavior is reused and not changed.

### Out-of-scope

- User management API.
- Production seed management.
- New roles or permissions.
- Auth backend changes.
- Frontend auth behavior changes.

### Validation Commands

```bash
git status --short
docker-compose config
docker-compose up -d postgres
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

## TASK 010.3 - Demo Workflow and Event Seeding

### Objective

Seed deterministic procurement workflow examples and event history using
existing workflow state, service, and event foundations.

### Scope

- Build demo workflow payloads from existing RFQ dataset records.
- Seed at least one clean workflow ready to run.
- Seed at least one workflow with existing event history.
- Optionally seed a conflict/precondition example if it remains small.
- Use existing `WorkflowStatus`, `WorkflowState`, `WorkflowService`, and
  `WorkflowEventService` where practical.
- Keep seeded payloads JSON-compatible, bounded, and explicitly demo/reference
  only.
- Add tests for seeded workflow visibility, event ordering, and idempotency.

### Deliverables

- Demo workflow seed implementation.
- Demo event seed implementation.
- Tests for seeded workflow/event behavior.
- README/runbook notes if useful.

### Acceptance Criteria

- Seeded workflows use existing workflow models and status enum values.
- Seeded event history appears through existing event read behavior.
- Seeded workflow examples are deterministic and idempotent.
- Payloads do not claim real Agent, pricing, retrieval, compliance, or email
  behavior.
- No migrations or database model changes are added.

### Out-of-scope

- Real Agent/tool execution.
- Real procurement calculations or policy engine.
- RAG/document indexing.
- Workflow runtime logic changes.
- New workflow API endpoints.
- Frontend changes.

### Validation Commands

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
git diff --check
```

## TASK 010.4 - Demo Seed CLI/Script

### Objective

Expose demo seeding through one explicit command that seeds users, workflows,
and events in a local/demo environment.

### Scope

- Add a backend seed CLI/script entrypoint.
- Compose demo user and workflow/event seed helpers.
- Guard against accidental production execution.
- Print a bounded seed summary.
- Return non-zero on seed failure.
- Document the command and expected environment.
- Add tests for command import, local-safety checks, and idempotent execution
  where practical.

### Deliverables

- Seed CLI/script entrypoint.
- Tests for command behavior.
- Documentation for running the seed command.
- Updated demo runbook draft.

### Acceptance Criteria

- One documented command seeds all demo data.
- The command is explicit and does not run automatically in production.
- The command can be safely rerun.
- Seed failures are visible and bounded.
- No backend API behavior, frontend behavior, migrations, or models are
  changed.

### Out-of-scope

- Production seed system.
- Deployment automation.
- Background workers.
- New APIs.
- Frontend feature changes.

### Validation Commands

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
git diff --check
```

## TASK 010.5 - Demo Runbook and Frontend Smoke Flow

### Objective

Create a clear local demo runbook and validate the seeded data through the
existing backend and frontend surfaces.

### Scope

- Add a step-by-step demo runbook.
- Document demo credentials and role walkthrough.
- Document backend startup, migrations, seed command, and frontend startup.
- Define expected checkpoints for workflow list, detail, create, run, events,
  and live timeline.
- Add troubleshooting for Docker, migrations, backend/frontend connectivity,
  WebSocket auth, Redis availability, and seed reruns.
- Run frontend/backend smoke checks where practical.

### Deliverables

- Demo runbook documentation.
- README links to the runbook if appropriate.
- Smoke validation notes.
- Optional small test updates if a blocker is found.

### Acceptance Criteria

- A reviewer can follow the runbook from clean local services to dashboard
  demonstration.
- Demo credentials are documented as local-only.
- Workflow create, run, persisted events, and live event timeline checkpoints
  are documented.
- RBAC behavior is represented in the walkthrough.
- Troubleshooting covers common local setup failures.
- No new product features are added.

### Out-of-scope

- Screenshot or video generation.
- Deployment automation.
- New frontend pages or backend endpoints.
- Real Agents, LLM providers, RAG, or approval continuation.

### Validation Commands

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

## TASK 010.6 - Demo Hardening and SPEC-010 Final Review

### Objective

Verify that SPEC-010 is complete, bounded, demo-ready, and safe to close.

### Scope

- Review demo seed code, idempotency, user roles, workflow examples, event
  history, runbook, and validation evidence.
- Verify seeded users can authenticate.
- Verify seeded workflows are visible through existing APIs and frontend.
- Verify runtime run still reaches `WAITING_APPROVAL`.
- Verify persisted events and live event timeline work with seeded data.
- Verify seed command does not run automatically in production.
- Confirm no migrations, model changes, new APIs, or frontend feature changes
  were introduced beyond approved docs/smoke updates.
- Record Harness durable evidence.

### Deliverables

- SPEC-010 final review result.
- Validation evidence.
- Harness story/trace evidence.
- Recommendation for the next SPEC.

### Acceptance Criteria

- Demo users and workflows are deterministic and idempotent.
- Demo runbook can be followed by a reviewer.
- Existing backend/frontend quality gates pass.
- Demo seed behavior is local/demo-safe.
- No real LLM, Agent, RAG, `/resume`, approval continuation, production seed
  management, migrations, model changes, or unapproved backend/frontend feature
  changes are added.

### Out-of-scope

- New product code during final review except tiny blocking fixes explicitly
  scoped to SPEC-010.
- Real Agent/LLM/RAG implementation.
- Human approval continuation.
- Production deployment or seed management.
- Admin user-management UI.

### Validation Commands

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
