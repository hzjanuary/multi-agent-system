# SPEC-007 - Workflow API Endpoints

## Status

Draft

## Context

Enterprise Multi-Agent OS is a state-driven workflow orchestration platform.
SPEC-005 completed the workflow state foundation: typed workflow schemas,
lifecycle helpers, transition validation, workflow services, event services,
audit integration, and repository support.

The backend API currently exposes health and authentication routes. SPEC-007
adds REST API endpoints for workflow state operations by adapting the completed
SPEC-005 service layer into FastAPI routes with authentication, RBAC, typed
request/response schemas, and API integration tests.

This spec does not run workflows. LangGraph runtime execution, workflow run and
resume behavior, event streaming, Agents, LLM providers, frontend integration,
and audit query APIs are deferred to later specs.

## Goals

- Define REST API endpoints for workflow state operations.
- Reuse existing SPEC-005 workflow schemas and services where practical.
- Define request and response schemas only where the API boundary needs them.
- Define API error mapping for workflow service and lifecycle exceptions.
- Define the workflow API router structure under `/api/v1/workflows`.
- Integrate existing authentication and RBAC dependencies.
- Add tests for success paths, authentication failures, RBAC failures,
  validation errors, missing workflow behavior, and invalid transitions.

## Non-goals

- LangGraph runtime execution.
- `POST /api/v1/workflows/{workflow_id}/run`.
- `POST /api/v1/workflows/{workflow_id}/resume`.
- WebSocket or server-sent event streaming.
- Agents or Agent execution.
- LLM providers.
- RAG or document indexing.
- Frontend implementation.
- Audit query APIs.
- Procurement-specific runtime logic or domain-specific transition policies.
- Global response envelope rollout.
- Complex workflow search, sorting, cursor pagination, or advanced filtering.

## API Endpoint List

SPEC-007 defines these REST endpoints:

```text
POST /api/v1/workflows
GET /api/v1/workflows
GET /api/v1/workflows/{workflow_id}
POST /api/v1/workflows/{workflow_id}/transition
PATCH /api/v1/workflows/{workflow_id}/state
GET /api/v1/workflows/{workflow_id}/events
```

Endpoint responsibilities:

- `POST /api/v1/workflows` creates a workflow record using typed workflow state
  input and returns the created workflow state.
- `GET /api/v1/workflows` lists workflow states with minimal pagination and
  optional simple status filtering.
- `GET /api/v1/workflows/{workflow_id}` returns one workflow state or a clear
  missing-workflow error.
- `POST /api/v1/workflows/{workflow_id}/transition` transitions a workflow to a
  requested status using SPEC-005 transition validation.
- `PATCH /api/v1/workflows/{workflow_id}/state` updates persisted workflow
  state payload where the state id and status match the persisted workflow.
- `GET /api/v1/workflows/{workflow_id}/events` lists persisted workflow events
  in deterministic chronological order.

## RBAC Policy

SPEC-007 uses existing authentication and RBAC dependencies.

Baseline role access:

| Role | Allowed access |
| --- | --- |
| Admin | Full access to all SPEC-007 workflow API endpoints |
| Manager | Full access to all SPEC-007 workflow API endpoints |
| Sales | Create workflow, read workflow, list workflows, list workflow events |
| Legal | Read workflow, list workflows, list workflow events |
| Finance | Read workflow, list workflows, list workflow events |
| Viewer | Read workflow, list workflows, list workflow events only |

Write endpoints:

- `POST /api/v1/workflows`: Admin, Manager, Sales.
- `POST /api/v1/workflows/{workflow_id}/transition`: Admin, Manager.
- `PATCH /api/v1/workflows/{workflow_id}/state`: Admin, Manager.

Read endpoints:

- `GET /api/v1/workflows`: Admin, Manager, Sales, Legal, Finance, Viewer.
- `GET /api/v1/workflows/{workflow_id}`: Admin, Manager, Sales, Legal,
  Finance, Viewer.
- `GET /api/v1/workflows/{workflow_id}/events`: Admin, Manager, Sales, Legal,
  Finance, Viewer.

Fine-grained domain approval policies are deferred to a later domain/policy
spec. SPEC-007 must not encode procurement-specific transition authorization.

## Request/Response Strategy

SPEC-007 follows the current backend API style for now: direct Pydantic response
models. It must not introduce a global response envelope in this spec.

Schema guidance:

- Reuse `WorkflowState`, `WorkflowStateCreate`, `WorkflowEventRead`, and
  `WorkflowStatus` where they match the API boundary.
- Add API-specific request schemas only where needed, such as workflow status
  transition payloads and state patch payloads.
- Keep response models typed, JSON-compatible, and implementation-agnostic.
- Do not expose ORM models directly from route handlers.
- Do not log raw request payloads or secrets.

A global response envelope should be considered as a future API consistency
backlog item, not part of SPEC-007.

## Error Mapping Strategy

SPEC-007 should map known service and validation failures into clear HTTP
responses:

- Unauthenticated request: `401 Unauthorized`.
- Authenticated user without required role: `403 Forbidden`.
- Missing workflow: `404 Not Found`.
- Missing workflow event, if exposed: `404 Not Found`.
- Invalid workflow transition: `409 Conflict` or `400 Bad Request`, with one
  consistent choice documented in implementation.
- Workflow state id/status mismatch: `400 Bad Request`.
- Pydantic request validation failure: FastAPI `422 Unprocessable Entity`.
- Unexpected service errors: generic `500 Internal Server Error` without
  leaking secrets or raw payloads.

Error responses should follow existing FastAPI project conventions until a
global response envelope is introduced by a later spec.

## Pagination/Filtering Strategy

Workflow listing stays minimal in SPEC-007:

- `limit` and `offset` may be included.
- An optional `status` filter is allowed if simple.
- Default and maximum limits should be explicit in implementation.
- Complex filtering, search, sorting, cursor pagination, and cross-domain query
  policy are out of scope.

## Architecture Notes

SPEC-007 keeps the established backend layering:

```text
API -> Service -> Repository/Tool -> External System
```

API routes parse and authorize HTTP requests, call workflow services, map
domain/service exceptions to HTTP responses, and return typed Pydantic models.
API routes must not call repositories directly.

Transactions should follow existing FastAPI database session conventions. The
workflow service remains responsible for lifecycle decisions and audit side
effects. SPEC-007 routes must not implement LangGraph runtime behavior or Agent
execution.

## User Stories

### US-003 - Create Workflow from Text Request API

As a Sales user, I want to create a workflow through the REST API so that the
workflow is persisted with status `CREATED`.

### US-018 - View Workflow Progress API Foundation

As an authenticated user with read access, I want to list and inspect workflow
state so that later UI work can show workflow progress.

### US-019 - View Agent Errors API Foundation

As an authenticated user with read access, I want to read workflow state and
events so that workflow failures can be inspected when they are persisted.

### US-023 - Audit Foundation Preservation

As an Admin or Manager, I want lifecycle API actions to use the existing
workflow service so that existing service-level audit writes remain intact.

## Acceptance Criteria

```gherkin
Given an authenticated Sales user
When the user posts a valid workflow creation payload
Then the API creates a workflow
And the response includes workflow state with status CREATED
```

```gherkin
Given an unauthenticated request
When it calls any workflow API endpoint
Then the API returns 401 Unauthorized
```

```gherkin
Given an authenticated Viewer
When the user attempts to transition workflow status
Then the API returns 403 Forbidden
```

```gherkin
Given a workflow exists
When an authorized reader requests the workflow by id
Then the API returns the typed workflow state
```

```gherkin
Given a workflow does not exist
When an authorized reader requests the workflow by id
Then the API returns 404 Not Found
```

```gherkin
Given a workflow has status CREATED
When an Admin or Manager transitions it to PLANNING
Then the API returns the updated workflow state
```

```gherkin
Given a workflow has status CREATED
When an Admin or Manager attempts to transition it directly to COMPLETED
Then the API rejects the transition
```

```gherkin
Given workflow events have been appended
When an authorized reader requests workflow events
Then the API returns events in deterministic chronological order
```

## Validation Strategy

SPEC-007 implementation tasks should use the Docker backend quality gate:

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

Focused API tests should cover:

- Route import and router registration.
- Workflow create/get/list success paths.
- Workflow transition success and invalid transition failures.
- Workflow state update success and mismatch failures.
- Workflow events list success and empty-list behavior.
- Missing workflow behavior.
- Authentication failures.
- RBAC failures for read and write endpoints.
- Pydantic validation failures.
- Confirmation that run/resume routes, streaming routes, Agents, LangGraph
  runtime, frontend, and audit query APIs are not implemented in SPEC-007.

## Out-of-scope List

- `POST /api/v1/workflows/{workflow_id}/run`.
- `POST /api/v1/workflows/{workflow_id}/resume`.
- LangGraph runtime.
- Workflow runtime execution.
- Agents.
- LLM providers.
- RAG.
- Document indexing.
- WebSocket or server-sent event streaming.
- Frontend.
- Audit query APIs.
- Approval API endpoints.
- Email generation.
- Procurement-specific runtime logic.
- Fine-grained domain approval policies.
- Global response envelope rollout.
- Complex filtering, search, sorting, or cursor pagination.
