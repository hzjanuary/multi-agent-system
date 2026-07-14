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
- SPEC-011 LLM Provider Abstraction - Approved / Closed

Current active spec:

- SPEC-012 Human Approval and Workflow Resume - Active

## Current SPEC-012 Planning State

Planning files:

- `.ai/specs/SPEC-012-human-approval-and-resume/spec.md`
- `.ai/specs/SPEC-012-human-approval-and-resume/tasks.md`

Planned tasks:

- `TASK 012.1 - Approval Contracts, Lifecycle Rules, and Planning Fixtures` -
  Implemented
- `TASK 012.2 - Backend Approval Service and Audit/Event Persistence`
- `TASK 012.3 - Approval and Resume API Endpoints with RBAC`
- `TASK 012.4 - Runtime Resume Implementation`
- `TASK 012.5 - Frontend Approval Panel and API Client`
- `TASK 012.6 - Approval Timeline, Demo Runbook, and Seed Updates`
- `TASK 012.7 - Human Approval Hardening and SPEC-012 Final Review`

## TASK 012.1 Implementation State

Deliverables:

- `backend/app/approvals/__init__.py`
- `backend/app/approvals/schemas.py`
- `backend/app/approvals/lifecycle.py`
- `backend/app/approvals/exceptions.py`
- `backend/app/approvals/policies.py`
- `backend/app/approvals/events.py`
- `backend/app/tests/test_approval_contracts.py`
- `backend/app/tests/test_approval_lifecycle.py`
- `backend/app/tests/test_approval_policies.py`

Behavior:

- Adds provider-independent/domain approval contracts for
  `approve`, `reject`, and `request_changes`.
- Treats `approve` and `reject` as final approval decisions.
- Treats `request_changes` as non-final, leaving the workflow in
  `WAITING_APPROVAL` for a later final decision.
- Adds bounded Pydantic v2 request, response, history, approval record, and
  resume DTOs without modeling new database tables.
- Adds pure lifecycle helpers that require approval decisions to occur only
  from `WAITING_APPROVAL`, block terminal workflow approval mutation, reject
  duplicate final decisions, and allow resume only after `APPROVED` with an
  approving record.
- Adds pure RBAC policy helpers using the existing `RoleName` enum: Admin and
  Manager can approve/reject/request changes/resume; Sales, Legal, Finance,
  and Viewer remain read-only for this slice.
- Adds approval/resume event name constants for future WorkflowEvent
  persistence and streaming.
- Does not add an approval persistence service, API endpoints, runtime resume,
  frontend behavior, migrations, model changes, auth/RBAC behavior changes, or
  event publishing.

Scope:

- Complete the `WAITING_APPROVAL` lifecycle with approve/reject decisions,
  persisted approval history, workflow events, audit evidence, and bounded
  runtime resume after approval.
- Prefer existing `Workflow.state_payload`, `WorkflowEvent`, and `AuditLog`
  foundations before adding migrations or new models.
- Preserve existing `/run` behavior and deterministic runtime defaults.
- Keep LLM runtime behavior behind `LLM_RUNTIME_ENABLED`.
- Use existing SPEC-008 WebSocket event streaming for approval/resume events.
- Add frontend approval/resume UI only through later implementation tasks.
- Defer full BPMN, configurable approval chains, email sending, digital
  signatures, document upload, RAG/document grounding, admin approval-policy UI,
  production notifications, provider-management UI, billing, and deployment.

## SPEC-011 Final Review State

Status:

- SPEC-011 approved and ready to close.

Evidence:

- `TASK 011.1 - LLM Provider Contracts and Settings` - Approved
- `TASK 011.2 - Provider Client Implementations with Mocked HTTP Tests` - Approved
- `TASK 011.3 - LLM Service Router, Fallbacks, and Error Handling` - Approved
- `TASK 011.4 - Prompt Templates and Structured Output Schemas` - Approved
- `TASK 011.5 - Runtime Integration Behind Feature Flag` - Approved
- `TASK 011.6 - Provider Documentation and Local Demo Guide` - Approved
- `TASK 011.7 - LLM Provider Hardening and SPEC-011 Final Review` - Approved

- Verified provider-independent contracts, settings, fake/Groq/OpenRouter/
  Ollama/Gemini clients, mocked HTTP tests, service routing, retry/fallback
  boundaries, prompt builders, structured output schemas, output parser,
  feature-flagged runtime integration, and provider/local demo docs.
- Confirmed safe defaults: `LLM_PROVIDER=fake`, `LLM_RUNTIME_ENABLED=false`,
  no API keys required at settings load time, fallback disabled by default, and
  deterministic runtime remains the default.
- Confirmed runtime integration uses `LLMService`/interface boundaries only,
  not provider clients, and still stops at `WAITING_APPROVAL`.
- Confirmed no frontend behavior changes, workflow API contract changes,
  migrations, database model changes, public provider-management endpoints,
  admin key-management UI, RAG/document indexing, `/resume`, human approval
  continuation, LLM token streaming, real API keys, provider SDKs, or
  LangChain/LiteLLM additions were introduced by SPEC-011.
- Hardened root README endpoint docs so deferred `/resume`, cancellation,
  approvals, token streaming, and provider-management endpoints are not listed
  as implemented routes.

Validation:

- `git status --short` completed.
- `docker-compose config` passed.
- `docker-compose build backend-test` passed.
- `docker-compose run --rm backend-test pytest` passed: 489 passed, 1 skipped.
- `docker-compose run --rm backend-test ruff check .` passed.
- `docker-compose run --rm backend-test black --check .` passed.
- `docker-compose run --rm backend-test mypy app` passed.
- `docker-compose run --rm backend-test python -m app.demo.seed --help` passed.
- `docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json` passed.
- `git diff --check` passed with LF/CRLF warnings only.
- Focused LLM/runtime tests passed: 93 passed.

Non-blocking notes:

- Existing LangGraph pending deprecation warning remains non-blocking.
- Existing Starlette TestClient deprecation warning remains non-blocking.
- LF/CRLF warnings from `git diff --check` remain non-blocking when no
  whitespace errors are reported.

## SPEC-011 Scope

- Provider-independent LLM contracts for Groq, OpenRouter, Ollama,
  Gemini, and a deterministic fake provider.
- Preserve no-key local demo behavior and deterministic tests.
- Keep runtime integration feature-flagged and behind an LLM service
  interface.
- Do not implement provider clients, runtime integration, prompts, API
  behavior, frontend behavior, migrations, or model changes during planning.

## TASK 011.1 Implementation State

Deliverables:

- `backend/app/llm/__init__.py`
- `backend/app/llm/contracts.py`
- `backend/app/llm/errors.py`
- `backend/app/llm/settings.py`
- `backend/app/tests/test_llm_contracts.py`
- `backend/app/tests/test_llm_settings.py`
- `backend/app/tests/test_settings.py` updated for LLM settings defaults
- `backend/.env.example` updated with safe LLM variables
- `backend/README.md` updated with LLM settings notes
- `docker-compose.yml` updated to use fake/offline LLM defaults

Behavior:

- Adds provider-independent Pydantic v2 LLM contracts for provider names,
  message roles, chat messages, chat requests, chat responses, structured
  response metadata, model capabilities, usage metadata, finish reasons, and
  safe provider error categories.
- Adds safe exception classes for provider/configuration errors without
  provider SDKs or network behavior.
- Adds `LLMSettings` helper and integrates LLM fields into existing application
  settings.
- Supports `fake`, `groq`, `openrouter`, `ollama`, and `gemini` provider
  values.
- Defaults to `LLM_PROVIDER=fake`, `LLM_RUNTIME_ENABLED=false`,
  `LLM_TIMEOUT_SECONDS=30`, and `LLM_MAX_RETRIES=2`.
- Keeps API keys optional at settings load time; real provider readiness is an
  explicit check for later provider-client tasks.
- Does not add provider clients, HTTP calls, LLM service routing, prompt
  templates, runtime integration, API behavior, frontend behavior, migrations,
  or database model changes.

## TASK 011.2 Implementation State

Deliverables:

- `backend/app/llm/clients/__init__.py`
- `backend/app/llm/clients/base.py`
- `backend/app/llm/clients/http.py`
- `backend/app/llm/clients/fake.py`
- `backend/app/llm/clients/groq.py`
- `backend/app/llm/clients/openrouter.py`
- `backend/app/llm/clients/ollama.py`
- `backend/app/llm/clients/gemini.py`
- `backend/app/llm/clients/openai_compatible.py`
- `backend/app/tests/test_llm_fake_client.py`
- `backend/app/tests/test_llm_provider_clients.py`
- `backend/app/tests/test_llm_provider_error_mapping.py`
- `backend/README.md` updated with provider-client scope

Behavior:

- Adds a provider-independent async `LLMClient` protocol.
- Adds deterministic `FakeLLMClient` for tests and no-key local development.
- Adds Groq and OpenRouter clients using non-streaming OpenAI-compatible chat
  completion request/response shapes.
- Adds Ollama client using the local non-streaming `/api/chat` endpoint with
  `stream: false` and no API key requirement.
- Adds Gemini client using the non-streaming `generateContent` REST shape with
  `x-goog-api-key` authentication.
- Adds an injectable JSON HTTP transport contract plus a stdlib urllib
  implementation for runtime use; tests inject fake transports and do not make
  live provider calls.
- Normalizes provider responses into `LLMChatResponse`, including usage,
  finish reason, request id/provider response id, and structured JSON parsing
  when requested.
- Maps configuration, authentication, rate limit, timeout, unavailable,
  invalid response, and unknown provider failures into safe LLM error
  categories without exposing API keys.
- Does not add provider SDKs, LLM service routing/fallbacks, prompt templates,
  runtime integration, API behavior, frontend behavior, migrations, or database
  model changes.

## TASK 011.3 Implementation State

Deliverables:

- `backend/app/llm/factory.py`
- `backend/app/llm/retry.py`
- `backend/app/llm/service.py`
- `backend/app/llm/__init__.py` updated
- `backend/app/llm/settings.py` updated with fallback controls
- `backend/app/config/settings.py` updated with fallback env vars
- `backend/app/tests/test_llm_client_factory.py`
- `backend/app/tests/test_llm_service.py`
- `backend/app/tests/test_llm_settings.py` updated
- `backend/.env.example` updated
- `backend/README.md` updated with service/router notes
- `docker-compose.yml` updated with safe fallback defaults

Behavior:

- Adds `LLMService` as the provider-independent async completion API for
  future runtime nodes and Agents.
- Adds `create_llm_client()` and `SettingsLLMClientFactory` to construct fake,
  Groq, OpenRouter, Ollama, and Gemini clients from `LLMSettings` without
  network calls or global clients.
- Keeps default behavior fake/offline-safe.
- Adds bounded retry handling based on `LLM_MAX_RETRIES`.
- Retries only transient categories: timeout, unavailable, and rate limit.
- Does not retry configuration, authentication, invalid response, safety,
  invalid request, or cancellation failures.
- Adds opt-in fallback controls:
  `LLM_FALLBACK_ENABLED=false` and `LLM_FALLBACK_PROVIDER=fake`.
- Fallback is disabled by default and does not hide configuration or
  authentication failures.
- Fallback responses include safe metadata showing fallback use, original
  provider, and error category.
- Does not add prompt templates, runtime integration, API behavior, frontend
  behavior, provider SDKs, live network validation, migrations, or database
  model changes.

## TASK 011.4 Implementation State

Deliverables:

- `backend/app/llm/prompts/__init__.py`
- `backend/app/llm/prompts/base.py`
- `backend/app/llm/prompts/procurement.py`
- `backend/app/llm/structured_outputs.py`
- `backend/app/llm/output_parser.py`
- `backend/app/llm/__init__.py` updated
- `backend/app/tests/test_llm_prompts.py`
- `backend/app/tests/test_llm_structured_outputs.py`
- `backend/app/tests/test_llm_output_parser.py`
- `backend/README.md` updated with prompt/schema/parser scope

Behavior:

- Adds provider-independent prompt builders for requirement extraction,
  supplier/pricing analysis, legal/compliance analysis, finance/risk analysis,
  and approval package preparation.
- Prompt builders return bounded JSON-mode `LLMChatRequest` objects using the
  existing LLM contracts and deterministic string rendering.
- Prompt rendering redacts sensitive input keys, bounds request/context text,
  uses low-temperature structured JSON mode, and does not read provider
  environment secrets.
- Adds Pydantic v2 structured output schemas for the five procurement prompt
  areas plus bounded shared nested models for extracted items, findings, risks,
  recommendations, and draft approval direction.
- Adds deterministic structured output parser helpers that parse JSON or simple
  fenced JSON from `LLMChatResponse.content`, validate through Pydantic, and
  raise safe `invalid_response` `LLMProviderError` failures for malformed or
  schema-invalid output.
- Does not call `LLMService`, provider clients, runtime nodes, workflow APIs,
  frontend code, RAG/document indexing, migrations, or database models.

## TASK 011.5 Implementation State

Deliverables:

- `backend/app/runtime/llm_adapter.py`
- `backend/app/runtime/service.py` updated for feature-flagged LLM path
- `backend/app/runtime/__init__.py` updated with adapter exports
- `backend/app/core/dependencies.py` updated to pass `LLMSettings` and create
  `LLMService` only when `LLM_RUNTIME_ENABLED=true`
- `backend/app/tests/test_runtime_llm_integration.py`
- `backend/README.md` updated with runtime feature-flag behavior

Behavior:

- Keeps `LLM_RUNTIME_ENABLED=false` as the default deterministic runtime path.
- When disabled, `RuntimeService` uses the existing deterministic LangGraph
  graph and does not call `LLMService`.
- When enabled, `RuntimeService` uses a provider-independent
  `LLMRuntimeAdapter` through a narrow `LLMCompletionService` protocol.
- LLM-enabled stage mapping:
  - `planner` -> `RequirementExtractionOutput`
  - `retrieval` -> `SupplierPricingAnalysisOutput`
  - `quotation` -> deterministic no-LLM arithmetic skip marker
  - `compliance` -> `LegalComplianceAnalysisOutput`
  - `validation` -> `FinanceRiskAnalysisOutput`
  - `approval` -> `ApprovalPackageOutput`
- LLM-enabled stages build bounded procurement prompt requests, call
  `LLMService.complete_json`, parse structured output with Pydantic, and write
  only validated bounded output and safe provider metadata into runtime state.
- Runtime events include safe LLM stage mode metadata and bounded stage output
  summaries; raw prompts, raw provider payloads, API keys, hidden reasoning, and
  raw LLM response content are not persisted.
- Invalid structured output and provider errors are persisted through existing
  runtime failure semantics with safe LLM error category metadata.
- Existing `/run` endpoint shape and transaction boundary remain unchanged.
- Runtime still stops at `WAITING_APPROVAL`; `/resume` remains deferred.
- Does not add provider SDKs, live network tests, frontend behavior, API
  contract changes, migrations, database model changes, RAG, or token
  streaming.

## TASK 011.6 Implementation State

Deliverables:

- `docs/llm/PROVIDER_SETUP.md`
- `docs/llm/LOCAL_LLM_DEMO.md`
- `backend/README.md` updated with provider documentation links and current
  SPEC-011 scope.
- `README.md` updated with current LLM safe defaults and documentation links.
- `docs/demo/DEMO_RUNBOOK.md` updated with LLM demo-mode guidance.

Behavior:

- Documents safe defaults: `LLM_PROVIDER=fake` and
  `LLM_RUNTIME_ENABLED=false`.
- Documents all LLM provider environment variables, retry/fallback controls,
  and provider-specific setup for Fake, Groq, OpenRouter, Ollama, and Gemini.
- Documents that the board demo remains deterministic with no keys configured.
- Documents optional real-provider local experimentation without requiring live
  provider validation.
- Documents runtime feature-flag behavior, structured-output validation,
  provider error troubleshooting, security notes, and known limitations.
- Does not add provider code, runtime behavior changes, workflow API changes,
  frontend behavior changes, migrations, database model changes, provider SDKs,
  LangChain/LiteLLM, or live external network calls.

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
