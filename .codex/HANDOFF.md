# Context Handoff

## Current Project Status

Closed specs:

- SPEC-001 Bootstrap Backend - Approved / Closed
- SPEC-002 Database Foundation - Approved / Closed
- SPEC-003 Authentication and RBAC - Approved / Closed
- SPEC-004 Storage Infrastructure - Approved / Closed
- SPEC-005 Workflow State - Approved / Closed
- SPEC-007 Workflow API Endpoints - Approved / Closed

Current active spec:

- SPEC-006 LangGraph Runtime - TASK 006.5 implemented, awaiting review

## Current SPEC-006 Implementation State

Planning files:

- `.ai/specs/SPEC-006-langgraph-runtime/spec.md`
- `.ai/specs/SPEC-006-langgraph-runtime/tasks.md`

Completed tasks:

- `TASK 006.1 - Runtime State Adapter and Contracts`
- `TASK 006.2 - LangGraph Dependency and Graph Skeleton`
- `TASK 006.3 - Deterministic Runtime Nodes`
- `TASK 006.4 - Runtime Service`
- `TASK 006.5 - Run Workflow API Endpoint`

TASK 006.1 deliverables:

- `backend/app/runtime/__init__.py`
- `backend/app/runtime/schemas.py`
- `backend/app/runtime/state_adapter.py`
- `backend/app/tests/test_runtime_state_adapter.py`
- `backend/README.md` runtime adapter notes

TASK 006.1 behavior:

- Defines deterministic runtime stages: planner, retrieval, quotation,
  compliance, validation, approval, and email_preparation.
- Defines `RuntimeWorkflowState` and `RuntimeWorkflowResult` Pydantic v2
  contracts.
- Provides pure adapter functions between persisted `WorkflowState` and runtime
  state:
  - `workflow_state_to_runtime_state`
  - `runtime_state_to_workflow_state`
- Preserves workflow id, workflow type, domain, request, status, metadata,
  runtime context, outputs, stage outputs, steps, error, retry count, and
  events.
- Keeps adapters side-effect free and JSON-compatible.

TASK 006.2 deliverables:

- `backend/app/runtime/graph.py`
- `backend/app/tests/test_runtime_graph.py`
- `backend/app/runtime/__init__.py` graph exports
- `backend/pyproject.toml` LangGraph dependency
- `backend/poetry.lock` dependency lock update
- `backend/README.md` graph skeleton notes

TASK 006.2 behavior:

- Adds `langgraph` as the backend runtime graph dependency.
- Defines a typed `RuntimeStatePayload` TypedDict at the LangGraph boundary.
- Defines runtime graph type aliases and `CompiledWorkflowGraph`.
- Defines deterministic stage sequence and linear topology:
  `START -> planner -> retrieval -> quotation -> compliance -> validation ->
  approval -> email_preparation -> END`.
- Provides `validate_runtime_node_handlers` to require handlers for every
  `RuntimeStage`.
- Provides `build_workflow_graph` to compile a LangGraph `StateGraph` from
  injected handlers.
- Keeps production runtime node logic, runtime service persistence, and API
  route behavior out of scope.

TASK 006.3 deliverables:

- `backend/app/runtime/nodes.py`
- `backend/app/tests/test_runtime_nodes.py`
- `backend/app/runtime/__init__.py` node exports
- `backend/README.md` deterministic node notes

TASK 006.3 behavior:

- Adds deterministic, no-LLM runtime node handlers for planner, retrieval,
  quotation, compliance, validation, approval, and email_preparation.
- Adds `create_deterministic_node_handlers` to provide a complete
  `RuntimeStage -> RuntimeNodeHandler` mapping for the graph builder.
- Each node returns a new `RuntimeWorkflowState` with current stage, completed
  stages, small JSON-compatible placeholder output, and runtime progress
  metadata.
- Nodes preserve unrelated workflow/runtime fields and do not mutate input
  state.
- Approval placeholder does not make an approval decision.
- Email preparation placeholder does not send email.
- Keeps runtime service persistence, API route behavior, WorkflowService calls,
  WorkflowEventService calls, external services, Agents, LLMs, RAG, event
  streaming, frontend behavior, migrations, and model changes out of scope.

TASK 006.4 deliverables:

- `backend/app/runtime/service.py`
- `backend/app/tests/test_runtime_service.py`
- `backend/app/runtime/__init__.py` service exports
- `backend/app/runtime/graph.py` optional stage subset support for runtime
  service subgraphs
- `backend/README.md` runtime service notes

TASK 006.4 behavior:

- Adds `RuntimeService` initialized with `WorkflowService`,
  `WorkflowEventService`, and optional runtime node handlers for tests.
- Runs a deterministic LangGraph subgraph from planner through approval and
  stops at `WAITING_APPROVAL`.
- Uses `WorkflowService.get_workflow`, `transition_workflow_status`, and
  `update_workflow_state` for persisted workflow state and lifecycle behavior.
- Uses `WorkflowEventService.append_event` for runtime started, node started,
  node completed, runtime waiting-for-approval, and failure events.
- Keeps transactions caller-owned and does not call `commit()`.
- Rejects non-`CREATED` runtime starts with a runtime precondition error.
- Handles node failures by appending failure events, persisting safe error
  state where practical, and transitioning to `FAILED` through
  `WorkflowService` when lifecycle rules allow it.
- Does not add `/run`, `/resume`, API route behavior, external service calls,
  real Agents, LLMs, RAG, streaming, frontend behavior, distributed workers,
  retry scheduler, migrations, model changes, workflow API behavior changes,
  auth/RBAC changes, or procurement-specific business logic.

TASK 006.5 deliverables:

- `backend/app/core/dependencies.py`
- `backend/app/api/v1/workflows.py`
- `backend/app/schemas/workflows_api.py`
- `backend/app/tests/test_workflow_api_runtime_run.py`
- `backend/app/tests/test_workflow_api_router.py`
- `backend/app/tests/test_workflow_api_create_get_list.py`
- `backend/README.md`

TASK 006.5 behavior:

- Adds a request-scoped `RuntimeService` dependency composed from
  `WorkflowService` and `WorkflowEventService`.
- Adds `WorkflowRunResponse` as the direct API response model for runtime run
  results.
- Exposes `POST /api/v1/workflows/{workflow_id}/run` under the existing
  workflow router.
- Requires Admin or Manager RBAC through the existing full-access workflow
  dependency.
- Passes authenticated user actor metadata to `RuntimeService.run_workflow`.
- Commits only at the API boundary after successful runtime service execution.
- Maps missing workflows to `404` through the existing workflow error mapper
  and maps runtime precondition failures to a safe `409` response.
- Keeps `/resume`, streaming, real Agents, LLM calls, RAG, frontend behavior,
  distributed workers, retry scheduling, email sending, approval decisioning,
  migrations, model changes, and auth/RBAC policy changes out of scope.

Overall SPEC-006 scope:

- LangGraph-based workflow runtime foundation.
- Runtime state adapter between persisted `WorkflowState` and LangGraph state.
- Deterministic placeholder graph nodes for planner, retrieval, quotation,
  compliance, validation, approval wait, and email preparation.
- Runtime service using existing `WorkflowService` and `WorkflowEventService`.
- Event append behavior through existing workflow event service.
- Audit preservation through existing workflow service behavior.
- `POST /api/v1/workflows/{workflow_id}/run` with Admin/Manager RBAC.

Explicit SPEC-006 deferrals:

- `POST /api/v1/workflows/{workflow_id}/resume`.
- WebSocket/SSE event streaming.
- Real Agents.
- LLM provider calls and multi-provider routing.
- RAG and document indexing.
- Frontend.
- Advanced human approval UI.
- Procurement-specific policy engine.
- Distributed worker queue.
- Production retry scheduler.
- Audit query APIs.
- Migrations or database model changes.

## Next Task

- Review `TASK 006.5 - Run Workflow API Endpoint`.
- Then implement `TASK 006.6 - Runtime Events and Failure Handling Hardening`
  only after TASK 006.5 is approved.

## Expected SPEC-006 Quality Gate

- `git status --short`
- `docker-compose config`
- `docker-compose up -d postgres`
- `docker-compose run --rm backend-test alembic upgrade head`
- `docker-compose build backend-test`
- `docker-compose run --rm backend-test pytest`
- `docker-compose run --rm backend-test ruff check .`
- `docker-compose run --rm backend-test black --check .`
- `docker-compose run --rm backend-test mypy app`
- `git diff --check`

## Important Constraints For SPEC-006

- Use existing SPEC-005 `WorkflowState`, lifecycle helpers, `WorkflowService`,
  and `WorkflowEventService`.
- Use existing SPEC-007 workflow API router, auth dependencies, RBAC role sets,
  and direct Pydantic response model style.
- Runtime status transitions must go through `WorkflowService`.
- Runtime events must go through `WorkflowEventService`.
- Keep placeholder nodes deterministic and no-LLM.
- Do not implement real Agent reasoning, retrieval, pricing, compliance,
  email generation, streaming, frontend, queues, migrations, or model changes.

## Known Warnings

- Existing FastAPI/TestClient StarletteDeprecationWarning is non-blocking.
- LF/CRLF warnings from `git diff --check` are non-blocking when no whitespace
  errors are reported.

## Harness State

- SPEC-005 final review recorded and approved.
- SPEC-007 final review recorded and approved.
- SPEC-006 planning recorded.
- TASK 006.1 implementation recorded and approved.
- TASK 006.2 implementation recorded and approved.
- TASK 006.3 implementation recorded and approved.
- TASK 006.4 implementation recorded and approved.
- TASK 006.5 implementation recorded with Harness intake #54 and trace #63.
