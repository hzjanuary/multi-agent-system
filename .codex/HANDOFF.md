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

Current active spec:

- SPEC-008 Event Streaming

## Current SPEC-008 Planning State

Planning files:

- `.ai/specs/SPEC-008-event-streaming/spec.md`
- `.ai/specs/SPEC-008-event-streaming/tasks.md`

Planned tasks:

- `TASK 008.1 - Event Stream Schemas and Publisher Contracts` - Approved
- `TASK 008.2 - Redis Pub/Sub Event Publisher` - Approved
- `TASK 008.3 - WorkflowEvent Publish Integration` - Approved
- `TASK 008.4 - WebSocket Stream Endpoint` - Implemented, awaiting review
- `TASK 008.5 - Stream Auth/RBAC and Recovery Tests`
- `TASK 008.6 - Event Streaming Hardening and SPEC-008 Final Review`

TASK 008.1 deliverables:

- `backend/app/streaming/__init__.py`
- `backend/app/streaming/schemas.py`
- `backend/app/streaming/contracts.py`
- `backend/app/tests/test_event_stream_schemas.py`
- `backend/app/tests/test_event_stream_contracts.py`
- `backend/README.md` streaming contract notes
- `.codex/HANDOFF.md` current-task update

TASK 008.1 behavior:

- Adds `WorkflowEventStreamMessage`, a Pydantic v2 stream DTO for persisted
  workflow event delivery.
- Adds `workflow_event_to_stream_message()` to convert `WorkflowEventRead` into
  a stream-safe DTO without exposing ORM objects.
- Adds payload sanitization that removes sensitive key names, bounds strings,
  lists, nesting depth, and object counts, and coerces non-JSON values into
  bounded strings.
- Adds implementation-agnostic async publisher/subscriber protocols:
  `WorkflowEventPublisher` and `WorkflowEventSubscriber`.
- Adds deterministic workflow-scoped channel helper
  `workflow_events_channel()` using `workflow-events:{workflow_id}`.
- Keeps Redis implementation, WebSocket/SSE endpoints, WorkflowEventService
  publish integration, RuntimeService behavior changes, migrations, model
  changes, auth/RBAC policy changes, frontend, `/resume`, real LLM token
  streaming, Agent thought streaming, RAG, and document indexing out of scope.

TASK 008.2 deliverables:

- `backend/app/streaming/redis_pubsub.py`
- `backend/app/streaming/__init__.py`
- `backend/app/tests/test_event_stream_redis_pubsub.py`
- `backend/README.md` Redis pub/sub adapter notes
- `.codex/HANDOFF.md` current-task update

TASK 008.2 behavior:

- Adds `RedisWorkflowEventPublisher`, a Redis-backed implementation of the
  `WorkflowEventPublisher` contract.
- Adds `RedisWorkflowEventSubscriber`, a Redis-backed implementation of the
  `WorkflowEventSubscriber` contract.
- Adds factory helpers that create Redis pub/sub adapters from `REDIS_URL`
  settings without connecting at import time.
- Publishes typed `WorkflowEventStreamMessage` payloads as JSON to
  `workflow-events:{workflow_id}`.
- Decodes subscriber JSON payloads back into typed stream messages and ignores
  malformed Redis messages safely.
- Wraps Redis publish/subscribe failures in typed stream adapter exceptions.
- Uses fake Redis clients in unit tests; no live Redis service is required for
  TASK 008.2 unit coverage.
- Keeps WorkflowEventService publish integration, RuntimeService changes,
  WebSocket/SSE endpoints, migrations, model changes, auth/RBAC policy changes,
  frontend, `/resume`, real LLM token streaming, Agent thought streaming, RAG,
  and document indexing out of scope.

TASK 008.3 deliverables:

- `backend/app/workflows/events.py`
- `backend/app/core/dependencies.py`
- `backend/app/tests/test_workflow_event_publish_integration.py`
- `backend/README.md` publish integration notes
- `.codex/HANDOFF.md` current-task update

TASK 008.3 behavior:

- Adds optional `WorkflowEventPublisher` injection to `WorkflowEventService`.
- Keeps direct service construction unchanged when no publisher is supplied.
- Converts persisted `WorkflowEventRead` values into sanitized
  `WorkflowEventStreamMessage` DTOs with `workflow_event_to_stream_message()`.
- Attempts publish only after the workflow event and event audit record have
  been flushed.
- Treats publish as best-effort delivery: publisher/conversion failures are
  logged with bounded metadata and do not erase or invalidate persisted
  workflow events.
- Adds FastAPI dependency wiring that lazily creates a Redis workflow event
  publisher from `REDIS_URL` and injects it into `WorkflowEventService`.
- Verifies RuntimeService-emitted events publish through the injected
  `WorkflowEventService` without changing RuntimeService business logic.
- Keeps WebSocket/SSE endpoints, stream auth/RBAC, RuntimeService business
  changes, `/run` behavior changes, migrations, model changes, frontend,
  `/resume`, real LLM token streaming, Agent thought streaming, RAG, and
  document indexing out of scope.

TASK 008.4 deliverables:

- `backend/app/api/v1/workflows.py`
- `backend/app/core/dependencies.py`
- `backend/app/tests/test_workflow_event_stream_websocket.py`
- `backend/app/tests/test_workflow_api_router.py`
- `backend/app/tests/test_workflow_api_create_get_list.py`
- `backend/README.md`
- `.codex/HANDOFF.md`

TASK 008.4 behavior:

- Adds `WS /api/v1/workflows/{workflow_id}/stream` under the existing workflow
  API router.
- Adds lazy `WorkflowEventSubscriber` dependency wiring backed by the Redis
  subscriber factory and `REDIS_URL` settings.
- Authenticates WebSocket clients using existing JWT/AuthService behavior from
  an `Authorization: Bearer <token>` header or `access_token` query parameter.
- Applies the existing workflow read/events role set: Admin, Manager, Sales,
  Legal, Finance, and Viewer.
- Verifies workflow existence by reading bounded persisted backlog events
  through `WorkflowEventService.list_events_for_workflow()`.
- Sends backlog events as sanitized `WorkflowEventStreamMessage` JSON DTOs,
  then forwards live subscriber messages for the workflow.
- Keeps the stream endpoint read/delivery-only: it does not append events, run
  workflows, mutate workflow status, mutate runtime state, change `/run`
  behavior, add SSE, add `/resume`, add migrations, or modify database models.

Overall SPEC-008 scope:

- `WorkflowEvent` remains the source of truth.
- RuntimeService continues appending persisted events through
  `WorkflowEventService`.
- The streaming layer delivers workflow events to clients in near real time.
- Transport decision: implement WebSocket endpoint
  `WS /api/v1/workflows/{workflow_id}/stream`.
- Redis pub/sub is the near-real-time notification mechanism because SPEC-004
  already provides Redis infrastructure.
- On WebSocket connect, the stream can deliver recent/backlog persisted events
  through `WorkflowEventService`, then forward newly published events.
- Stream auth/RBAC matches SPEC-007 workflow event read behavior:
  Admin, Manager, Sales, Legal, Finance, and Viewer.
- Stream messages must be typed, JSON-compatible, bounded, and sanitized.

Explicit SPEC-008 deferrals:

- Server-sent events.
- Frontend live UI.
- Real LLM token streaming.
- Agent thought streaming or hidden reasoning exposure.
- Multi-workflow dashboard fanout.
- Cross-tenant event bus.
- Durable replay cursor beyond basic event id or created timestamp recovery.
- Production horizontal scaling beyond Redis pub/sub.
- Advanced notification delivery.
- `/resume` and human approval continuation.
- RAG, document indexing, real Agents, and procurement policy engine.
- New migrations or database model changes.

## Next Task

- Review `TASK 008.4 - WebSocket Stream Endpoint`.
- Then implement `TASK 008.5 - Stream Auth/RBAC and Recovery Tests` only after
  TASK 008.4 is approved.

## Expected SPEC-008 Quality Gate

- `git status --short`
- `docker-compose config`
- `docker-compose up -d postgres redis`
- `docker-compose run --rm backend-test alembic upgrade head`
- `docker-compose build backend-test`
- `docker-compose run --rm backend-test pytest`
- `docker-compose run --rm backend-test ruff check .`
- `docker-compose run --rm backend-test black --check .`
- `docker-compose run --rm backend-test mypy app`
- `git diff --check`

## Important Constraints For SPEC-008

- Use existing SPEC-005 `WorkflowEventService` and persisted `WorkflowEvent`
  records as source of truth.
- Use existing SPEC-007 workflow router/auth/RBAC patterns for stream access.
- Use existing SPEC-004 Redis settings and infrastructure for pub/sub.
- Do not replace database event persistence with pub/sub.
- Do not mutate workflow state/status from the streaming layer.
- Do not implement `/resume`, SSE, frontend live UI, real LLM token streaming,
  Agent thought streaming, RAG, document indexing, migrations, or model changes.

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
- TASK 006.6 implementation recorded with Harness intake #55 and trace #64.
- TASK 006.7 final review recorded with Harness intake #56 and trace #65.
- SPEC-008 planning recorded with Harness intake #57.
- TASK 008.1 implementation recorded with Harness intake #58.
- TASK 008.2 implementation recorded with Harness intake #59.
- TASK 008.3 implementation recorded with Harness intake #60.
- TASK 008.4 implementation recorded with Harness intake #61.
