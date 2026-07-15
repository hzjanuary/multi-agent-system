# Enterprise Multi-Agent OS Backend

FastAPI backend foundation for Enterprise Multi-Agent OS.

This backend contains the foundation layer for Enterprise Multi-Agent OS:
project structure, settings, logging, middleware, health endpoints, Docker
support, a reproducible Docker-based quality gate, the SPEC-002 database
foundation, SPEC-003 authentication/RBAC foundation, and SPEC-004 storage
provider foundations. Workflow runtime, agents, document management APIs, and
business modules are intentionally out of scope for the current backend
foundation.

## Requirements

- Python 3.12
- Poetry

## Install

```bash
poetry install
```

## Run Locally

```bash
poetry run uvicorn app.main:app --reload
```

The OpenAPI documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Health Endpoints

The backend exposes lightweight service endpoints:

```text
GET /       service metadata and endpoint links
GET /health overall application health
GET /ready  readiness with lightweight placeholder checks
GET /live   liveness status
```

Readiness does not perform database, Redis, Qdrant, or MinIO checks yet. Those
clients are introduced by later implementation tasks.

## Database

The async SQLAlchemy foundation lives in `app/db/session.py`.

It provides:

```text
create_database_engine()  builds an AsyncEngine from DATABASE_URL
create_session_factory()  builds an async_sessionmaker[AsyncSession]
provide_db_session()      FastAPI dependency for request-scoped sessions
```

`DATABASE_URL` is loaded from the typed settings model. This foundation prepares
the async engine/session layer; repositories are introduced by later SPEC-002
tasks.

The declarative model base and shared mixins live in:

```text
app/db/base.py    DeclarativeBase with Alembic-friendly naming conventions
app/db/mixins.py  UUID primary key, timestamp, and soft-delete mixins
```

Models should inherit from `Base` and the relevant mixins. Repositories and
business services are intentionally deferred to later SPEC-002 tasks.

Phase 1 core models are registered through `app/models/__init__.py` so
`Base.metadata` can discover:

```text
users
roles
user_roles
workflows
workflow_events
audit_logs
```

The model layer defines table shape and relationships only. Authentication
services and workflow runtime behavior are separate tasks.

Generic repository primitives live in:

```text
app/repositories/base.py  BaseRepository with caller-owned AsyncSession
app/repositories/crud.py  CRUDRepository with reusable async model operations
```

Repositories receive an `AsyncSession` from the caller. They do not create
sessions and do not commit transactions automatically; transaction boundaries
stay in the service or request layer.

Alembic is configured for async SQLAlchemy in:

```text
alembic.ini
alembic/env.py
alembic/versions/0001_create_phase_1_core_tables.py
```

Run migrations through the Docker test environment from the repository root:

```bash
docker-compose up -d postgres
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test alembic current
docker-compose run --rm backend-test alembic downgrade base
```

## Settings

Application settings live in `app/config/settings.py` and are loaded with
Pydantic v2 through `pydantic-settings`.

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Supported environments are:

```text
development
testing
production
```

Settings can be overridden with environment variables such as:

```bash
APP_ENV=testing
DEBUG=false
LOG_LEVEL=DEBUG
```

Do not commit real API keys, database credentials, or object storage secrets.

### LLM Provider Configuration

Detailed provider setup and local demo guidance live in:

- `../docs/llm/PROVIDER_SETUP.md`
- `../docs/llm/LOCAL_LLM_DEMO.md`

SPEC-011 adds provider-independent LLM contracts, settings, isolated provider
clients, prompt templates, structured output validation, and a feature-flagged
runtime adapter for fake, Groq, OpenRouter, Ollama, and Gemini. Provider clients
live behind a common async interface and use injectable HTTP transport for
mocked tests. SPEC-011 itself does not add public provider-management APIs,
frontend provider settings, RAG, token streaming, migrations, or model changes.
The human approval `/resume` path is documented separately under SPEC-012.

The safe default is offline/deterministic:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_FALLBACK_ENABLED=false
LLM_FALLBACK_PROVIDER=fake
```

Supported provider identifiers are:

```text
fake
groq
openrouter
ollama
gemini
```

Provider-specific environment variables are documented in `.env.example` and in
`../docs/llm/PROVIDER_SETUP.md`:

```text
LLM_MODEL
LLM_RUNTIME_ENABLED
LLM_TIMEOUT_SECONDS
LLM_MAX_RETRIES
LLM_FALLBACK_ENABLED
LLM_FALLBACK_PROVIDER
GROQ_API_KEY
GROQ_MODEL
OPENROUTER_API_KEY
OPENROUTER_MODEL
OLLAMA_BASE_URL
OLLAMA_MODEL
GEMINI_API_KEY
GEMINI_MODEL
```

API keys are optional at settings load time so local tests and the deterministic
demo can run without real credentials. Real remote provider clients perform
explicit readiness checks before use and fail safely when required keys are
missing. Never commit real provider keys.

`LLMService` provides the provider-independent completion API for later runtime
integration. It selects the configured provider, applies bounded retries only
for transient categories (`timeout`, `unavailable`, and `rate_limit`), and can
optionally fallback to a configured provider. Fallback is disabled by default
and does not hide configuration or authentication failures.

Provider-independent procurement prompt templates and structured output schemas
live in `app/llm/prompts`, `app/llm/structured_outputs.py`, and
`app/llm/output_parser.py`. They build bounded JSON-mode `LLMChatRequest`
objects for requirement extraction, supplier/pricing analysis, legal/compliance
analysis, finance/risk analysis, and approval package preparation. Parser
helpers validate returned JSON with Pydantic before runtime tasks write output
to workflow state. These modules do not call providers directly.

`LLM_RUNTIME_ENABLED=false` remains the default. When it is false, workflow
runtime execution uses the existing deterministic LangGraph node handlers and
does not call `LLMService`. When explicitly enabled, the runtime uses
`LLMService` through a narrow runtime adapter, builds procurement prompt
requests, validates structured output, and writes only bounded validated output
into workflow state. The quotation stage still does not use LLM arithmetic; it
records a deterministic skip marker. The `/run` path still stops at
`WAITING_APPROVAL`; the separate `/resume` path can continue an approved
workflow through the bounded email-preparation placeholder.

The fake provider is deterministic and requires no network. Groq and
OpenRouter use non-streaming OpenAI-compatible chat completion request shapes;
Ollama uses the local non-streaming `/api/chat` endpoint; Gemini uses the
non-streaming `generateContent` REST shape. Runtime execution still uses the
existing deterministic path unless LLM runtime mode is explicitly enabled.

For the board-ready demo, keep:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

Real-provider local experiments are opt-in. Configure keys through environment
variables only, restart the backend after changing provider settings, and do
not run live-provider smoke tests as part of the automated quality gate.

## Authentication Utilities

Password hashing utilities live in `app/auth/password.py`.

```text
hash_password()            hashes plain-text passwords with Argon2
verify_password()          verifies plain text against an Argon2 hash
password_needs_rehash()    reports whether an Argon2 hash should be refreshed
```

The password utility layer is intentionally narrow. It does not log plain-text
passwords, create users, implement registration, or expose API endpoints by
itself.

JWT token utilities live in `app/auth/tokens.py`.

```text
create_access_token()   signs an access token with sub, token_type, iat, exp
create_refresh_token()  signs a refresh token with sub, token_type, iat, exp
decode_token()          validates signature, expiration, and token type
verify_token()          returns a payload or None for invalid tokens
```

JWT settings are loaded from environment variables:

```text
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
```

The default JWT secret is for local development only. Production deployments
must provide a strong secret through environment configuration. The token
utility layer does not log tokens, create users, implement registration, or
expose API endpoints by itself.

Auth API routes are mounted under `/api/v1/auth`:

```text
POST /api/v1/auth/login    returns access and refresh tokens
POST /api/v1/auth/refresh  returns a new token pair from a refresh token
POST /api/v1/auth/logout   stateless MVP logout success response
GET  /api/v1/auth/me       returns the current safe user profile
```

The Auth API uses the existing `User` model, Argon2 password verification, JWT
token utilities, and request-scoped `AsyncSession` dependency. It does not log
plain-text passwords or tokens, and it does not return `hashed_password` in
responses. Logout is stateless for now; server-side token revocation can be
added later with Redis-backed storage.

RBAC dependency utilities live in `app/auth/rbac.py`.

```text
RoleName             supported role names: Admin, Manager, Sales, Legal, Finance, Viewer
get_user_role_names  returns case-sensitive role names assigned to a user
require_any_role     allows users with any listed role
require_all_roles    allows users with every listed role
require_admin        convenience dependency for Admin-only access
```

RBAC dependencies build on the existing current-user dependency. Missing or
invalid credentials return `401`; authenticated users without required roles
return `403`. Role comparison is case-sensitive. This layer does not implement
role assignment APIs, user management APIs, registration, permission tables, or
fine-grained permissions.

## Storage Interfaces

Cache provider interfaces live in `app/cache`.

```text
CacheProvider.get()     reads a string value by key
CacheProvider.set()     stores a string value with an optional TTL
CacheProvider.delete()  removes a key if present
CacheProvider.exists()  checks key presence
CacheProvider.expire()  applies or replaces a TTL
CacheProvider.close()   releases provider resources
```

The cache layer is interface-only at this stage. Redis client behavior,
distributed locks, queues, workflow state, Qdrant, MinIO, document indexing, and
RAG are deferred to later SPEC-004 tasks.

Redis-backed cache support lives in `app/cache/redis.py`.

```text
RedisCacheProvider.from_url()      creates a provider from a Redis URL
create_redis_cache_provider()      creates a provider from REDIS_URL settings
RedisCacheProvider.health_check()  verifies Redis responds to ping
```

`RedisCacheProvider` implements the `CacheProvider` contract with async Redis
operations for string values, optional TTL on `set`, `expire`, `exists`,
`delete`, and `close`. Redis operation failures are wrapped as cache operation
errors. The provider does not implement workflow state, distributed locks,
queues, or token blacklists.

Vector store provider interfaces live in `app/vectorstore`.

```text
VectorPoint                 vector id, float vector, and payload metadata
VectorSearchResult          result id, score, and payload metadata
VectorStore.create_collection()
VectorStore.collection_exists()
VectorStore.upsert()
VectorStore.search()
VectorStore.delete()
VectorStore.close()
```

The vector store layer is interface-only at this stage. Qdrant client behavior,
embeddings, document chunking, document indexing, RAG, hybrid search, Retrieval
Agent logic, LangGraph, agents, MinIO, and frontend work are deferred to later
tasks.

Qdrant-backed vector store support lives in `app/vectorstore/qdrant.py`.

```text
QdrantVectorStore.from_url()       creates a provider from a Qdrant URL
create_qdrant_vector_store()       creates a provider from QDRANT_URL settings
QdrantVectorStore.health_check()   verifies Qdrant responds
```

`QdrantVectorStore` implements the `VectorStore` contract with async operations
for collection creation, collection existence checks, point upsert, vector
search, point deletion, and client close. It uses cosine distance for created
collections and supports simple exact-match payload filters. Qdrant operation
failures are wrapped as vector store operation errors. The provider does not
implement embeddings, chunking, indexing, RAG, hybrid search, Retrieval Agent
logic, LangGraph, agents, MinIO, or frontend behavior.

Object storage provider interfaces live in `app/storage`.

```text
StoredObject                         object bucket, name, size, content type, etag
ObjectStorageProvider.bucket_exists()
ObjectStorageProvider.create_bucket()
ObjectStorageProvider.upload_bytes()
ObjectStorageProvider.download_bytes()
ObjectStorageProvider.delete_object()
ObjectStorageProvider.object_exists()
ObjectStorageProvider.close()
```

MinIO-backed object storage support lives in `app/storage/minio.py`.

```text
MinIOStorageProvider.from_settings()  creates a provider from MinIO settings
create_minio_storage_provider()       creates a provider from configured settings
MinIOStorageProvider.health_check()   verifies MinIO responds
```

`MinIOStorageProvider` implements the `ObjectStorageProvider` contract with
async wrapper methods around the MinIO SDK for bucket existence checks, bucket
creation, byte upload, byte download, object existence checks, object deletion,
and close. Each object operation receives an explicit bucket name; the configured
`MINIO_BUCKET_NAME` is used as the default health-check target and factory
configuration. MinIO operation failures are wrapped as object storage operation
errors. The provider does not implement document management APIs, document
metadata persistence, indexing, RAG, Retrieval Agent logic, generated files,
email attachments, LangGraph, agents, or frontend behavior.

## Knowledge Base Contracts

SPEC-013 starts the RAG/document knowledge base with provider-independent
contracts and deterministic chunking helpers only:

```text
app/knowledge/schemas.py    document, chunk, citation, retrieval, and search DTOs
app/knowledge/chunking.py   text normalization, SHA-256 hashing, and chunk IDs
```

The current knowledge package is pure Python/Pydantic. It validates bounded
document metadata, chunk metadata, citation excerpts, retrieval result metadata,
and search filters. Chunking is deterministic, character-based, and preserves
paragraph boundaries where practical while producing stable SHA-256 checksums
and chunk IDs.

This slice does not implement embeddings, Qdrant upserts, MinIO storage,
ingestion commands, retrieval APIs, runtime RAG grounding, frontend evidence
panels, migrations, or database models.

## Workflow State Foundation

Workflow state schemas and lifecycle metadata live in `app/workflows`.

```text
WorkflowState             typed state envelope aligned with SPEC-005
WorkflowStateCreate       initial state creation payload
WorkflowStepState         generic per-step status/output/error shape
WorkflowError             structured workflow error details
WorkflowType              supported workflow type values
workflow_status_values()  approved WorkflowStatus values
is_terminal_status()      terminal status helper
get_allowed_transitions() allowed next statuses for a status
can_transition()          boolean transition check
validate_transition()     raises for invalid transitions
WorkflowService           async service for create/read/list/status/state updates
WorkflowRepository        database access helper for Workflow records
WorkflowEventCreate       typed payload for appending workflow events
WorkflowEventRead         typed read schema for persisted workflow events
WorkflowEventService      async service for event append/read behavior
WorkflowEventRepository   database access helper for WorkflowEvent records
WorkflowAuditLogger       service-level audit log helper
AuditLogRepository        database access helper for AuditLog records
```

The workflow package reuses the existing `WorkflowStatus` enum from
`app.models.enums` so schema status values stay aligned with persisted workflow
records. Transition rules are pure helpers based on the SPEC-005 lifecycle.
`WorkflowService` uses caller-owned `AsyncSession` instances and the
`WorkflowRepository` to create, read, list, transition, and update persisted
workflow state envelopes. The service flushes changes but does not commit
transactions; callers own transaction boundaries. It writes bounded audit logs
for workflow creation, valid status transitions, and state payload updates using
the existing `AuditLog` model.

Workflow event append/read behavior uses the existing `WorkflowEvent` model.
`WorkflowEventService` verifies the workflow exists before appending an event,
persists JSON-compatible payloads through the model `payload` field, and lists
events by `created_at` then `id` for deterministic chronological order. It
flushes changes but does not commit transactions. Appending an event also writes
a bounded audit record with event metadata, not the full event payload. Audit
query APIs, event streaming, workflow API routes, LangGraph runtime, Agents, LLM
providers, RAG, document indexing, email generation, and frontend behavior
remain deferred to later specs.

Workflow API schemas and error mapping for SPEC-007 live in:

```text
app/schemas/workflows_api.py     request/response models for future workflow routes
app/api/v1/workflow_errors.py    workflow exception to HTTP error mapping helpers
app/api/v1/workflows.py          workflow router foundation and RBAC scaffolding
```

These modules provide direct Pydantic request/response models for workflow REST
endpoints and map known workflow lifecycle exceptions to safe HTTP error
details. The workflow router is mounted under `/api/v1/workflows` and currently
implements:

```text
POST /api/v1/workflows                 Admin, Manager, Sales
GET  /api/v1/workflows                 Admin, Manager, Sales, Legal, Finance, Viewer
GET  /api/v1/workflows/{workflow_id}   Admin, Manager, Sales, Legal, Finance, Viewer
POST /api/v1/workflows/{workflow_id}/transition
                                      Admin, Manager
PATCH /api/v1/workflows/{workflow_id}/state
                                      Admin, Manager
GET  /api/v1/workflows/{workflow_id}/events
                                      Admin, Manager, Sales, Legal, Finance, Viewer
POST /api/v1/workflows/{workflow_id}/run
                                      Admin, Manager
POST /api/v1/workflows/{workflow_id}/approval
                                      Admin, Manager
GET  /api/v1/workflows/{workflow_id}/approval/history
                                      Admin, Manager, Sales, Legal, Finance, Viewer
POST /api/v1/workflows/{workflow_id}/resume
                                      Admin, Manager
GET  /api/v1/workflows/_meta           authenticated workflow readers
```

Workflow list supports minimal `limit`, `offset`, and optional `status` query
parameters. Workflow create uses `WorkflowService`, returns a direct
`WorkflowResponse`, and commits at the API route boundary after the service
flushes its caller-owned transaction. Workflow status transition uses
`WorkflowTransitionRequest`, existing SPEC-005 transition validation through
`WorkflowService`, maps missing workflows to `404`, maps invalid transitions to
`409`, and commits only after successful service execution. Workflow state
update uses `WorkflowStateUpdateRequest`, requires the supplied state id and
status to match the persisted workflow, maps missing workflows to `404`, maps
state mismatches to `400`, preserves existing service-level audit behavior, and
commits only after successful service execution. Workflow events read uses
`WorkflowEventService`, returns a direct `WorkflowEventListResponse`, supports
minimal `limit` and `offset` query parameters, maps missing workflows to `404`,
and does not commit because it is a read-only route. Approval decision writes
use `ApprovalService`, return direct approval response schemas, map approval
lifecycle conflicts to `409`, commit only after successful service execution,
and persist approval history, WorkflowEvent records, and AuditLog records
through existing service foundations. Approval history reads are read-only. The
resume route is authenticated, RBAC-protected, and calls the bounded
post-approval runtime continuation for approved workflows only.

The SPEC-007 workflow API slices use direct response models and keep workflow
business logic inside services. Runtime execution is exposed separately through
`POST /api/v1/workflows/{workflow_id}/run` and the explicit post-approval
`POST /api/v1/workflows/{workflow_id}/resume` continuation. Audit query APIs,
Agent calls, and unflagged real LLM-backed runtime behavior remain deferred.

## Runtime State Adapter

Runtime-facing contracts for SPEC-006 live in `app/runtime`.

```text
RuntimeStage                      deterministic runtime stage names
RuntimeWorkflowState              JSON-compatible state for graph execution
RuntimeWorkflowResult             lightweight future runtime result shape
workflow_state_to_runtime_state() converts persisted WorkflowState to runtime state
runtime_state_to_workflow_state() converts runtime output back to WorkflowState
runtime_stage_sequence()          runtime graph stage order
runtime_graph_topology()          START/stage/END edge topology
build_workflow_graph()            compiles injected handlers into a LangGraph graph
create_deterministic_node_handlers() complete no-LLM handler map for the graph
RuntimeService                   runs deterministic pre-approval graph execution
```

The adapter preserves the existing `WorkflowState` envelope while adding
runtime-oriented fields such as current stage, completed stages, failed stage,
stage outputs, runtime context, error, and retry count. Adapter functions are
pure and side-effect free. They do not import LangGraph, build graphs, execute
nodes, call Agents or LLM providers, create API routes, or modify database
models.

The runtime graph skeleton uses LangGraph `StateGraph` with injected handlers
for each `RuntimeStage`. The topology is deterministic and linear:

```text
START -> planner -> retrieval -> quotation -> compliance -> validation
  -> approval -> email_preparation -> END
```

The graph builder validates that every runtime stage has a handler before
compilation. Handler injection keeps TASK 006.2 free of production node logic,
workflow persistence, API route behavior, Agent calls, LLM calls, RAG,
document indexing, event streaming, frontend behavior, migrations, and model
changes.

Deterministic runtime nodes provide one side-effect-free placeholder handler for
each runtime stage. Each handler records the current stage, completed stage, and
a small JSON-compatible placeholder output in `stage_outputs` and
`outputs.stage_outputs`. The placeholders preserve existing workflow fields and
do not change workflow status, call services, emit persisted events, perform
retrieval or pricing, approve requests, generate customer-facing email, call
LLMs or Agents, create API routes, or modify database models.

`RuntimeService` orchestrates the deterministic pre-approval runtime path for a
persisted workflow. It loads workflow state through `WorkflowService`, streams a
LangGraph subgraph from planner through approval, transitions lifecycle status
through `WorkflowService`, appends runtime and node events through
`WorkflowEventService`, persists the updated `WorkflowState`, and stops at
`WAITING_APPROVAL`. The service keeps transactions caller-owned and does not
call `commit()`. Its separate resume method requires an approved workflow,
executes only the bounded `email_preparation` placeholder, and transitions
through `GENERATING_EMAIL` to `COMPLETED`. It does not execute
email_preparation before approval, send email, call Agents, stream events to
clients directly, create migrations, or modify database models.

The workflow runtime API endpoint `POST /api/v1/workflows/{workflow_id}/run`
uses `RuntimeService`, requires Admin or Manager access, passes the authenticated
user as runtime actor metadata, commits only at the API boundary after
successful service execution, and returns a direct `WorkflowRunResponse`. The
deterministic `/run` path stops at `WAITING_APPROVAL`; the `/resume` endpoint
uses `RuntimeService.resume_workflow_after_approval()` to continue only after a
final approve decision. Real email sending, arbitrary graph resume, Agent
execution, and unflagged real LLM calls remain deferred.

## Event Streaming Contracts

Event streaming contracts for SPEC-008 live in `app/streaming`.

```text
WorkflowEventStreamMessage        typed workflow event stream DTO
workflow_event_to_stream_message  converts WorkflowEventRead to stream DTO
WorkflowEventPublisher            async publisher protocol
WorkflowEventSubscriber           async subscriber protocol
workflow_events_channel()         deterministic workflow-scoped channel helper
RedisWorkflowEventPublisher       Redis pub/sub publisher implementation
RedisWorkflowEventSubscriber      Redis pub/sub subscriber implementation
```

`WorkflowEventStreamMessage` is a direct Pydantic v2 message schema for future
workflow stream delivery. It carries workflow id, event id, event type, status,
stage, timestamps, sequence, message text, and a sanitized payload. Payload
sanitization removes sensitive key names, bounds strings, lists, nesting depth,
and object counts, and coerces non-JSON values into bounded strings.

Redis-backed pub/sub support lives in `app/streaming/redis_pubsub.py`. The
publisher serializes `WorkflowEventStreamMessage` as JSON and publishes it to
`workflow-events:{workflow_id}`. The subscriber creates workflow-scoped Redis
pub/sub subscriptions, decodes valid JSON messages back into typed stream
messages, ignores malformed payloads, and cleans up subscriptions on close.
Factory helpers use `REDIS_URL` from settings, while tests inject fake Redis
clients so unit tests do not require a live Redis service.

`WorkflowEventService` accepts an optional `WorkflowEventPublisher`. When a
publisher is configured, appended workflow events are flushed, converted from
`WorkflowEventRead` into sanitized `WorkflowEventStreamMessage` DTOs, and
published best-effort. Publish failures are logged with bounded metadata and do
not remove or invalidate persisted workflow events. FastAPI dependency wiring
provides the Redis publisher lazily through settings without creating a global
Redis client.

The workflow event stream endpoint is mounted at:

```text
WS /api/v1/workflows/{workflow_id}/stream
```

The endpoint requires the same workflow read/event roles used by the REST event
read endpoint. On connection it sends a bounded backlog of persisted
`WorkflowEvent` records converted into safe `WorkflowEventStreamMessage` DTOs,
then forwards live workflow-scoped messages from the configured subscriber. The
stream endpoint does not append events, start or run workflows, mutate workflow
status, mutate runtime state, or expose ORM/database internals. WebSocket
clients may authenticate with an `Authorization: Bearer <token>` header or an
`access_token` query parameter when headers are not practical.

The streaming layer does not add SSE routes, start workflow execution, change
`/run` behavior, or modify database models. Approval/resume events arrive
through the existing persisted `WorkflowEventService` publisher path. Frontend
live UI changes, real LLM/Agent token streaming, RAG, and procurement-specific
runtime logic remain deferred.

## Docker

Build and run the backend plus Phase 1 infrastructure services from the
repository root:

```bash
docker-compose config
docker-compose up --build backend
```

The Compose stack includes:

```text
backend   FastAPI API on http://localhost:8000
postgres  PostgreSQL on localhost:5432
redis     Redis on localhost:6379
qdrant    Qdrant on http://localhost:6333
minio     MinIO API on http://localhost:9000 and console on http://localhost:9001
```

After the backend starts, verify:

```bash
curl http://localhost:8000/health
```

The Docker Compose file uses development defaults only. Do not reuse demo
passwords or API keys for production deployments.

## Logging And Middleware

`app/main.py` wires the core middleware foundation:

- `RequestIdMiddleware` attaches a request ID to every request.
- If `X-Request-ID` is provided, the same value is reused.
- If `X-Request-ID` is missing, a UUID request ID is generated.
- Every response includes `X-Request-ID`.
- `RequestLoggingMiddleware` emits JSON-compatible request logs with
  `request_id`, `method`, `path`, `status_code`, and `duration_ms`.
- CORS origins are loaded from `BACKEND_CORS_ORIGINS`.
- GZip response compression is enabled.
- The global exception handler returns the standard JSON error envelope.

## Test And Check

Run the reproducible Python 3.12 Docker quality gate from the repository root:

```bash
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
```

The `backend` image installs only runtime dependencies. The `backend-test`
service uses the Dockerfile `dev` target and installs development dependencies
for validation.

## Local Demo Seed

SPEC-010 local demo data is seeded explicitly; it never runs on backend startup
and is not exposed through an API endpoint. After applying migrations, run from
the repository root:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

The command seeds demo roles/users plus deterministic RFQ-001 workflow examples
and event backlog in one transaction. It commits once after all seed steps
succeed and rolls back on failure. The seed is idempotent and local-demo only.

To inspect behavior without persisting records:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --dry-run
```

Demo credentials are documented in `docs/demo/DATASET_INVENTORY.md` and are not
production defaults.

For the board-ready walkthrough and frontend smoke checklist, see:

- `docs/demo/DEMO_RUNBOOK.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
- `docs/llm/LOCAL_LLM_DEMO.md`
