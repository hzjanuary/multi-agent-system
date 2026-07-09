# SPEC-007 Tasks - Workflow API Endpoints

## TASK 007.1 - Workflow API Schemas and Error Mapping

### Objective

Define API boundary schemas and HTTP error mapping for workflow endpoints.

### Scope

- Reuse existing workflow schemas where practical.
- Add request schemas for status transition and state update if needed.
- Define typed API response models where route-specific wrappers are useful.
- Define helper functions or exception handlers for workflow API errors.
- Map workflow service exceptions and transition errors to HTTP responses.

### Deliverables

- Workflow API schema module or additions to an existing schema package.
- Workflow API error mapping helper or route-local mapping pattern.
- Unit tests for schema validation and error mapping if practical.
- README notes only if schema/error behavior needs user-facing documentation.

### Acceptance Criteria

- API request schemas can be imported.
- Existing workflow state/event schemas are reused where practical.
- Missing workflow errors map to `404 Not Found`.
- Invalid transition errors map to one documented client error response.
- State mismatch errors map to `400 Bad Request`.
- No global response envelope is introduced.

### Out-of-scope

- API route implementation beyond what is necessary to support schema/error
  imports.
- LangGraph runtime.
- Workflow run or resume behavior.
- Event streaming.
- Agents.
- Audit query APIs.
- Frontend.

### Validation Commands

```bash
docker-compose config
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

## TASK 007.2 - Workflow API Router Foundation

### Objective

Create the workflow API router structure and wire it into the existing API v1
router without implementing endpoint business behavior beyond minimal imports.

### Scope

- Add a FastAPI router under `/api/v1/workflows`.
- Wire the workflow router into the existing API v1 exports/main router pattern.
- Add dependency helpers for workflow API database session and current user use
  if useful.
- Establish route-level RBAC dependency patterns for later endpoint tasks.
- Add import/router registration tests.

### Deliverables

- Workflow API router module.
- Router export/wiring update.
- Minimal tests proving app import and route registration.
- README notes only if route surface documentation is useful.

### Acceptance Criteria

- Workflow router can be imported.
- App includes the workflow router under `/api/v1/workflows`.
- Existing health and auth routes continue to import.
- Router foundation uses existing auth/RBAC dependencies.
- No workflow runtime, run/resume, streaming, Agent, or frontend behavior is
  implemented.

### Out-of-scope

- Endpoint business behavior beyond router foundation.
- Workflow run/resume endpoints.
- WebSocket or server-sent event streaming.
- LangGraph runtime.
- Agents.
- LLM providers.
- Audit query APIs.
- Frontend.

### Validation Commands

```bash
docker-compose config
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

## TASK 007.3 - Create/Get/List Workflow Endpoints

### Objective

Implement create, get, and list workflow REST endpoints using the existing
WorkflowService.

### Scope

- Implement `POST /api/v1/workflows`.
- Implement `GET /api/v1/workflows`.
- Implement `GET /api/v1/workflows/{workflow_id}`.
- Use `WorkflowService` for all workflow state operations.
- Apply RBAC:
  - Admin, Manager, Sales may create.
  - Admin, Manager, Sales, Legal, Finance, Viewer may read and list.
- Include minimal `limit`/`offset` pagination and optional simple status filter
  if practical.
- Add API integration tests for success, auth, RBAC, validation, and missing
  workflow behavior.

### Deliverables

- Workflow API route implementations for create/get/list.
- API tests for create/get/list behavior.
- README notes for workflow API usage if appropriate.

### Acceptance Criteria

- Authorized Sales user can create a workflow.
- Created workflow response includes status `CREATED`.
- Authorized readers can get an existing workflow.
- Missing workflow returns `404 Not Found`.
- Authorized readers can list workflows.
- Unauthenticated requests return `401 Unauthorized`.
- Disallowed roles for creation return `403 Forbidden`.
- API routes call the service layer instead of repositories directly.

### Out-of-scope

- Status transition endpoint.
- State update endpoint.
- Workflow events endpoint.
- Workflow run/resume endpoints.
- LangGraph runtime.
- Agents.
- Event streaming.
- Complex filtering or cursor pagination.
- Frontend.

### Validation Commands

```bash
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

## TASK 007.4 - Workflow Status Transition Endpoint

### Objective

Implement the workflow status transition REST endpoint using existing SPEC-005
transition validation through WorkflowService.

### Scope

- Implement `POST /api/v1/workflows/{workflow_id}/transition`.
- Accept a target workflow status and optional reason.
- Use `WorkflowService.transition_workflow_status`.
- Apply RBAC: Admin and Manager only.
- Map invalid transitions to a documented client error response.
- Add API tests for valid transition, invalid transition, missing workflow,
  authentication failure, and RBAC failure.

### Deliverables

- Workflow transition endpoint.
- Transition request schema if not already added.
- API tests for transition behavior.
- README notes if useful.

### Acceptance Criteria

- Admin or Manager can transition a workflow from `CREATED` to `PLANNING`.
- Invalid transitions are rejected.
- Terminal status transitions are rejected by existing lifecycle validation.
- Missing workflow returns `404 Not Found`.
- Sales, Legal, Finance, and Viewer receive `403 Forbidden` for transition.
- Invalid transition does not create a successful lifecycle result.
- No procurement-specific transition policy is encoded.

### Out-of-scope

- Workflow runtime execution.
- Run/resume endpoints.
- Approval domain policies.
- LangGraph runtime.
- Agents.
- Event streaming.
- Audit query APIs.
- Frontend.

### Validation Commands

```bash
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

## TASK 007.5 - Workflow State Update Endpoint

### Objective

Implement a bounded workflow state update endpoint using existing WorkflowState
schemas and WorkflowService.

### Scope

- Implement `PATCH /api/v1/workflows/{workflow_id}/state`.
- Accept typed workflow state update payloads.
- Use `WorkflowService.update_workflow_state`.
- Apply RBAC: Admin and Manager only.
- Reject workflow id/status mismatches.
- Add API tests for success, mismatch failures, missing workflow,
  authentication failure, and RBAC failure.

### Deliverables

- Workflow state update endpoint.
- State update request schema if needed.
- API tests for state update behavior.
- README notes if useful.

### Acceptance Criteria

- Admin or Manager can update persisted workflow state payload for an existing
  workflow.
- State workflow id mismatch returns `400 Bad Request`.
- State status mismatch returns `400 Bad Request`.
- Missing workflow returns `404 Not Found`.
- Sales, Legal, Finance, and Viewer receive `403 Forbidden`.
- Existing WorkflowService and audit behavior are reused.

### Out-of-scope

- Runtime state merging from LangGraph.
- Agent output merge policies.
- Approval-specific state APIs.
- Workflow run/resume endpoints.
- Event streaming.
- Agents.
- Frontend.

### Validation Commands

```bash
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

## TASK 007.6 - Workflow Events Read Endpoint

### Objective

Implement the workflow events read endpoint using existing WorkflowEventService.

### Scope

- Implement `GET /api/v1/workflows/{workflow_id}/events`.
- Use `WorkflowEventService.list_events_for_workflow`.
- Apply RBAC: Admin, Manager, Sales, Legal, Finance, and Viewer.
- Include minimal `limit`/`offset` pagination if practical.
- Add API tests for events list success, empty list, deterministic ordering,
  missing workflow, authentication failure, and RBAC failure.

### Deliverables

- Workflow events read endpoint.
- API tests for workflow event list behavior.
- README notes if useful.

### Acceptance Criteria

- Authorized readers can list workflow events.
- Existing workflow with no events returns an empty list.
- Event ordering remains deterministic.
- Missing workflow returns `404 Not Found`.
- Unauthenticated requests return `401 Unauthorized`.
- Endpoint reuses WorkflowEventService.
- No event streaming is implemented.

### Out-of-scope

- Event append endpoint.
- WebSocket or server-sent event streaming.
- Agent-generated runtime events.
- LangGraph runtime.
- Audit query APIs.
- Frontend.

### Validation Commands

```bash
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

## TASK 007.7 - Workflow API Auth/RBAC Tests and Hardening

### Objective

Harden workflow API behavior with final auth/RBAC, validation, and
out-of-scope regression coverage.

### Scope

- Review SPEC-007 acceptance criteria.
- Add or improve tests for:
  - unauthenticated workflow API calls
  - role-specific allowed and forbidden access
  - invalid request payloads
  - invalid workflow ids
  - missing workflow behavior
  - invalid transitions
  - route registration
  - no run/resume/streaming routes implemented in SPEC-007
- Fix small bugs discovered by tests.
- Clean up README wording for workflow API usage if needed.

### Deliverables

- Hardened workflow API test coverage.
- Small bug fixes limited to SPEC-007 if required.
- README updates if needed.
- Final validation evidence for SPEC-007 implementation.

### Acceptance Criteria

- SPEC-007 acceptance criteria are covered by tests.
- Authenticated and unauthenticated behavior is tested.
- RBAC behavior is tested for all baseline roles where practical.
- Validation and missing-resource behavior are tested.
- Test suite passes.
- Lint, format, type, and diff checks pass.
- No out-of-scope features are added.

### Out-of-scope

- New product features.
- Run/resume endpoints.
- LangGraph runtime.
- Agents.
- LLM providers.
- RAG.
- Document indexing.
- Event streaming.
- Frontend.
- Audit query APIs.
- Procurement-specific runtime logic.

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

## SPEC-007 Final Review

### Objective

Verify SPEC-007 is complete and ready to close.

### Scope

- Review implemented workflow API schemas, router wiring, endpoints, error
  mapping, RBAC behavior, and tests.
- Confirm validation proof.
- Confirm out-of-scope work was not implemented.
- Record Harness evidence.

### Deliverables

- SPEC-007 final review result.
- Harness durable story/trace evidence when available.
- Recommendation for next spec.

### Acceptance Criteria

- All SPEC-007 tasks are implemented and validated.
- Required workflow endpoints exist and use existing SPEC-005 services.
- Auth and RBAC policies match the SPEC-007 baseline.
- Direct Pydantic response models are used; no global response envelope is
  introduced.
- Run/resume endpoints remain deferred to SPEC-006.
- Event streaming remains deferred to SPEC-008.
- No LangGraph runtime, Agents, LLM providers, RAG, document indexing,
  frontend, audit query APIs, or procurement-specific runtime logic were
  implemented.

### Out-of-scope

- Application code changes during review.
- LangGraph runtime implementation.
- Agent implementation.
- Event streaming implementation.
- Frontend implementation.
- Audit query API implementation.

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
