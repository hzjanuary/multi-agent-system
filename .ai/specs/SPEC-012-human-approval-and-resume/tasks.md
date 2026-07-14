# SPEC-012 Tasks - Human Approval and Workflow Resume

## Task List

### TASK 012.1 - Approval Contracts, Lifecycle Rules, and Planning Fixtures

Goal: Define typed approval/resume contracts and lifecycle helper rules without
implementing service behavior, API routes, frontend UI, migrations, or runtime
resume execution.

Scope:

- Add approval decision enums/contracts.
- Add approval request/response schemas.
- Add resume response schema if the existing runtime response does not fully
  fit the boundary.
- Add pure lifecycle helper functions for approval eligibility, duplicate
  decision detection against state/event evidence, terminal protection, and
  resume eligibility.
- Decide whether request changes is implemented as a non-final decision/event
  or deferred.
- Add tests for schema validation and pure lifecycle rules.
- Update README/handoff only if appropriate.

Acceptance criteria:

- Approval contracts exist and import cleanly.
- Approve/reject/request-changes semantics are explicit.
- Helpers reject non-`WAITING_APPROVAL`, terminal, and duplicate-decision
  states.
- Resume helpers require `APPROVED`.
- No service, API route, frontend, migration, or model changes are added.
- Quality gate passes.

Validation:

```bash
git status --short
docker-compose config
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 012.2 - Backend Approval Service and Audit/Event Persistence

Goal: Implement approval decision use cases using existing workflow state,
workflow events, and audit foundations where possible.

Scope:

- Add `ApprovalService` or equivalent workflow-domain service.
- Use `WorkflowService` for status transitions.
- Use `WorkflowEventService` for approval events.
- Persist approval summary/history in `WorkflowState` payload if sufficient.
- Avoid direct commits; caller owns transaction boundary.
- Prevent duplicate final decisions.
- Reject invalid status/terminal workflows safely.
- Add tests for approve, reject, request-changes if supported, duplicate
  prevention, event payload safety, audit behavior, and non-commit behavior.
- Do not add API routes yet.

Acceptance criteria:

- Approval service exists and imports cleanly.
- Admin/Manager actor metadata can be passed into decisions.
- Approval transitions to `APPROVED` only through `WorkflowService`.
- Rejection transitions to `REJECTED` only through `WorkflowService`.
- Approval/rejection events are persisted through `WorkflowEventService`.
- Approval history is readable from workflow state/events.
- Service does not call `commit()`.
- No migrations or model changes are added unless a documented blocker requires
  an explicit later review.

Validation:

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

### TASK 012.3 - Approval and Resume API Endpoints with RBAC

Goal: Expose approval decision and resume endpoints using existing auth/RBAC,
typed responses, and API transaction boundaries.

Scope:

- Add `POST /api/v1/workflows/{workflow_id}/approval`.
- Add `POST /api/v1/workflows/{workflow_id}/resume`, wired to a placeholder or
  not-yet-implemented safe service only if TASK 012.4 has not landed.
- Use Admin/Manager RBAC for approval/resume mutations.
- Keep workflow read roles unchanged.
- Map known approval/runtime errors to safe 404/409 responses.
- Commit only after successful service return.
- Do not change `/run` behavior.
- Add API tests for auth, RBAC matrix, success, missing workflow, invalid
  status, duplicate decision, terminal workflow, transaction boundaries, and
  direct Pydantic response safety.

Acceptance criteria:

- Approval endpoint exists.
- Resume endpoint exists only as scoped and safe.
- Admin/Manager can approve/reject.
- Sales/Legal/Finance/Viewer cannot approve/reject/resume.
- Unauthenticated requests return 401.
- Existing workflow endpoints still pass.
- No global response envelope is introduced.
- No frontend code is changed.

Validation:

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

### TASK 012.4 - Runtime Resume Implementation

Goal: Implement bounded post-approval runtime continuation from `APPROVED` to
`COMPLETED` without redesigning LangGraph or changing `/run`.

Scope:

- Add `RuntimeService.resume_workflow_after_approval()` or equivalent.
- Require workflow status `APPROVED`.
- Execute only `email_preparation` continuation initially.
- Use existing graph/node patterns where practical.
- Transition `APPROVED -> GENERATING_EMAIL -> COMPLETED` through
  `WorkflowService`.
- Persist state updates through `WorkflowService`.
- Append safe runtime/node/resume events through `WorkflowEventService`.
- Preserve `LLM_RUNTIME_ENABLED` behavior and no-key deterministic default.
- Do not send email.
- Add tests for success, invalid status, rejected workflow, terminal workflow,
  failure handling, event emission, transaction boundary, and no service commit.

Acceptance criteria:

- Resume runtime path exists and is bounded to approved workflows.
- `/run` behavior remains unchanged.
- Rejected/terminal/non-approved workflows cannot resume.
- Email-preparation output is safe placeholder output.
- Workflow reaches `COMPLETED` when continuation succeeds.
- Runtime events stream through existing event publisher path.
- Tests use fake/mock LLM only if LLM path is enabled.

Validation:

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

### TASK 012.5 - Frontend Approval Panel and API Client

Goal: Add workflow detail approval/resume UI and typed API client functions
without changing backend behavior beyond the already implemented endpoints.

Scope:

- Add frontend types for approval request/response and resume response.
- Add API client functions for approval and resume endpoints.
- Add approval panel on workflow detail.
- Show approve/reject actions for `WAITING_APPROVAL`.
- Add bounded comment field and validation.
- Add resume action for `APPROVED` if endpoint is separate.
- Refresh workflow detail/events after approval/resume.
- Handle loading, success, 401, 403, 404, 409, and generic error states.
- Keep backend 403 as source of truth.
- Add tests for API client paths, bearer token attachment, panel rendering,
  approve/reject/resume behavior, and error states.

Acceptance criteria:

- Approval panel exists on workflow detail.
- Approval client uses existing token/session helpers.
- No fake approval/resume success is shown.
- Existing run panel and event timeline remain functional.
- No admin policy builder UI, email sending UI, provider UI, RAG UI, or
  document upload UI is added.

Validation:

```bash
git status --short
docker-compose config
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

### TASK 012.6 - Approval Timeline, Demo Runbook, and Seed Updates

Goal: Make approval/resume visible in the demo through existing event timeline,
deterministic seed data, and documentation.

Scope:

- Update timeline rendering only if approval/resume events need clearer labels.
- Update demo seed contracts/data only if needed for a stable approval demo.
- Keep seed behavior idempotent and local-demo safe.
- Update demo runbook and frontend smoke flow for approval/resume path.
- Add tests for seeded approval-ready workflows or approval event history if
  seed updates are made.
- Do not add real email sending or production notification behavior.

Acceptance criteria:

- Demo docs include Manager/Admin approval and resume walkthrough.
- Approval/resume events are visible through existing timeline.
- Seed updates, if any, are deterministic and idempotent.
- Existing demo create/run path remains stable.
- Known limitations still document no real email sending, no RAG, no admin
  policy UI, and no production notification integrations.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

### TASK 012.7 - Human Approval Hardening and SPEC-012 Final Review

Goal: Verify SPEC-012 is complete, bounded, audited, tested, and ready to
close.

Scope:

- Review contracts, lifecycle rules, approval service, API endpoints, runtime
  resume, frontend panel, timeline behavior, demo docs, and out-of-scope scan.
- Harden tests/docs only for small blockers.
- Confirm no unplanned migrations/model changes were introduced.
- Confirm `/run` behavior remains stable.
- Confirm LLM runtime remains feature-flagged.
- Confirm no email sending, RAG, document upload, admin policy UI, or
  production notification integration was added.

Acceptance criteria:

- Approval lifecycle is complete for approve/reject.
- Request changes is either implemented safely as scoped or explicitly
  deferred.
- Resume path is bounded and tested.
- Approval/resume events are persisted and streamable.
- RBAC matrix is covered.
- Frontend approval/resume UX is tested.
- Demo runbook is updated.
- Full quality gates pass.

Validation:

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
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```
