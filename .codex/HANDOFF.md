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
- SPEC-012 Human Approval and Workflow Resume - Approved / Closed
- SPEC-013 RAG and Document Knowledge Base - Approved / Closed
- SPEC-014 Production Deployment and Observability - Approved / Closed

Current active spec:

- SPEC-015 Final Evaluation, Demo Validation, and Graduation Report Assets - TASK 015.2 implemented / pending review

## Current TASK 015.2 Implementation State

Implemented:

- Added `scripts/final/e2e-demo-validation.sh` for guarded final board-demo
  validation using existing health, auth, workflow, approval, resume,
  knowledge, and observability endpoints.
- Added `docs/final/E2E_DEMO_VALIDATION.md` with prerequisites, environment
  variables, no-key default mode, optional RAG mode, script usage, manual
  checklist, expected outcomes, troubleshooting, limitations, and safety notes.
- Added `docs/final/E2E_EVIDENCE_CAPTURE_TEMPLATE.md` as a placeholder-only
  final E2E evidence note template.
- Updated `docs/final/README.md`,
  `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md`, and `scripts/README.md` with the
  final E2E validation script and evidence-capture links.

Scope boundaries preserved:

- No backend behavior, frontend behavior, runtime behavior, Docker/Compose
  behavior, CI workflow behavior, API contract, tests, migrations, database
  models, real secrets, provider keys, cloud resources, deployment automation,
  startup seed, startup ingestion, final report chapters, diagrams,
  screenshots, slides, or global response envelope were added.

Validation:

- `git status --short` reviewed.
- `docker-compose config` passed.
- `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config` passed.
- `bash scripts/final/e2e-demo-validation.sh --help` passed when Git Bash was
  first on `PATH`; the default Windows `bash` command resolves to a broken WSL
  shim on this host.
- `bash scripts/ci/compose-gate.sh` passed when Git Bash was first on `PATH`.
- `git diff --check` passed with LF/CRLF warnings only.
- Harness intake recorded as #114.
- Harness story `TASK-015.2` marked implemented.
- Harness trace recorded as #130.

## Current SPEC-015 Planning State

Planning files:

- `.ai/specs/SPEC-015-final-evaluation-demo-report-assets/spec.md`
- `.ai/specs/SPEC-015-final-evaluation-demo-report-assets/tasks.md`

## Current TASK 015.1 Implementation State

Implemented:

- Added `docs/final/README.md` as the final evaluation planning entry point.
- Added `docs/final/EVALUATION_MATRIX.md` mapping final evaluation dimensions
  to SPEC-001 through SPEC-014 capabilities, acceptance criteria, automated
  evidence, manual demo evidence, expected artifacts, risks, and placeholder
  final statuses.
- Added `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md` defining command-based
  evidence, manual demo evidence, no-key and optional RAG-enabled evaluation
  modes, safety/no-secret evidence, and later artifact placeholders.
- Added `docs/final/EVALUATION_REPORT_TEMPLATE.md` as a placeholder-only
  evaluation report skeleton for later evidence capture.
- Linked final evaluation planning from the root `README.md`.

Scope boundaries preserved:

- No E2E automation scripts, final report chapters, diagrams, screenshots,
  slides, tests, backend behavior, frontend behavior, runtime behavior, Docker
  behavior, CI behavior, migrations, database models, real secrets, provider
  keys, cloud resources, or deployment automation were added.

Validation:

- `git status --short` reviewed.
- `docker-compose config` passed.
- `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config` passed.
- Git Bash `scripts/ci/compose-gate.sh` passed.
- `git diff --check` passed with LF/CRLF warnings only.
- Harness intake recorded as #113.
- Harness story `TASK-015.1` marked implemented.
- Harness trace recorded as #129.

Scope:

- Plan final graduation evaluation evidence for the completed SPEC-001 through
  SPEC-014 product path.
- Define a repeatable end-to-end demo validation strategy covering startup,
  migrations, demo seed, knowledge ingestion, workflow run to
  `WAITING_APPROVAL`, RAG evidence, approval, resume, `COMPLETED`, RBAC,
  readiness, and metrics.
- Plan safe evidence capture under `docs/final/` or equivalent.
- Plan graduation report structure, architecture diagram inventory, screenshot
  checklist, final demo script, defense Q&A bank, and repository release
  checklist.
- Preserve no-key deterministic defaults: fake LLM provider, disabled LLM
  runtime, fake embeddings, and `RAG_ENABLED=false`.

Deferrals:

- New backend or frontend features.
- Admin operations or policy builder.
- Enterprise SSO.
- Production email sending.
- Production secret vault.
- Cloud deployment automation.
- Terraform or Kubernetes.
- Upload UI or admin document-management UI.
- Token streaming or agent-thought streaming.
- Global response envelope rollout.
- Real secrets, provider keys, or paid/live LLM provider requirements.

Planning validation:

- `git status --short` completed.
- `docker-compose config` passed.
- `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config` passed.
- `git diff --check` passed.
- Harness intake recorded as #112.

## Current TASK 014.6 Implementation State

Implemented:

- Added `docs/deployment/RUNBOOK.md` as the production-demo operator runbook.
- Added `docs/deployment/DEMO_PACKAGE.md` for board-demo packaging and
  walkthrough evidence.
- Added `docs/deployment/SMOKE_CHECKS.md` for automated and manual smoke
  checks.
- Added `docs/deployment/BACKUP_RESTORE.md` for honest backup, restore, and
  rollback basics.
- Added `docs/deployment/TROUBLESHOOTING.md` for common production-demo and
  board-demo failures.
- Updated deployment, demo, root, backend, frontend, and scripts docs with
  concise cross-links.

Scope boundaries preserved:

- No backend behavior, frontend behavior, runtime behavior, API contract,
  Docker/Compose behavior, CI workflow behavior, migration, database model,
  deployment automation, backup automation, rollback automation, cloud
  resource, Kubernetes/Terraform resource, real secret, provider key,
  production email behavior, startup seed, startup knowledge ingestion, or
  global response envelope was added.

Validation:

- `git status --short` reviewed.
- `docker-compose config` passed.
- `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config` passed.
- Git Bash `scripts/ci/compose-gate.sh` passed.
- Git Bash `scripts/deployment/smoke-prod-demo.sh --help` passed.
- `git diff --check` passed with line-ending warnings only.

## Current TASK 014.5 Implementation State

Implemented:

- Added `.github/workflows/ci.yml` for repository CI quality gates.
- Added local CI scripts for Compose validation, backend validation, frontend
  validation, and full gate execution.
- Added `scripts/deployment/smoke-prod-demo.sh` for safe production-demo smoke
  checks against existing `/health`, `/live`, optional `/ready`, and frontend
  root endpoints.
- Updated deployment, backend, frontend, root, and scripts documentation with
  local gate commands, no-key behavior, cleanup behavior, serial frontend
  build/typecheck guidance, and smoke-script usage.

Scope boundaries preserved:

- No real deployment, image push, cloud resource, Kubernetes/Terraform,
  secret-vault integration, real secret, real provider key, backend behavior,
  frontend behavior, runtime behavior, API contract change, migration, database
  model, production email, global response envelope, startup seed, or startup
  knowledge ingestion was added.

Validation:

- `git status --short` reviewed.
- `docker-compose config` passed.
- `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config` passed.
- Git Bash `scripts/ci/compose-gate.sh` passed.
- Git Bash `scripts/ci/backend-gate.sh` passed with backend-test build,
  migrations, pytest `685 passed, 1 skipped`, Ruff, Black, MyPy, demo seed
  dry-run JSON, and knowledge ingestion dry-run JSON.
- Git Bash `scripts/ci/frontend-gate.sh` passed with npm install/ci, lint,
  build, typecheck, and `55` frontend tests.
- Git Bash `scripts/ci/all-gates.sh` passed, including production-demo
  backend/frontend image build and `git diff --check`.
- Explicit production-demo backend/frontend image build passed.
- `git diff --check` and `git diff --cached --check` passed with line-ending
  warnings only.
- Git Bash `scripts/deployment/smoke-prod-demo.sh --help` passed.

## Current TASK 014.4 Implementation State

Implemented:

- Added vendor-neutral observability helpers for recursive redaction and
  bounded log/metrics payload values.
- Hardened structlog configuration with `LOG_FORMAT`,
  `LOG_REDACTION_ENABLED`, and JSON redaction defaults.
- Wired request logging to preserve request IDs, avoid headers/bodies, and
  record bounded HTTP request metrics.
- Added in-process metrics collection with low-cardinality labels and safe
  request duration summaries.
- Added authenticated `GET /api/v1/observability/metrics` for Admin and
  Manager users.
- Added observability/metrics settings and production-demo env/Compose wiring.
- Added tests for recursive redaction, JSON logging, request log safety,
  metrics aggregation, metrics endpoint auth/RBAC, and settings bounds.

Scope boundaries preserved:

- No telemetry vendor SDK, OpenTelemetry exporter, Prometheus dependency,
  frontend behavior, workflow API contract change, knowledge API contract
  change, health/live/ready contract change, migrations, database models,
  provider SDK, CI workflow, deployment smoke script, production email,
  Kubernetes/Terraform, cloud resource, real secret, token streaming, or
  agent-thought streaming was added.

## Current TASK 014.3 Implementation State

Status:

- Approved.

Implemented:

- Added bounded backend readiness dependency checks for Postgres, Redis,
  Qdrant, and MinIO/object storage.
- Kept `/health` and `/live` lightweight process checks.
- Updated `/ready` to return safe typed per-dependency summaries and `503`
  when required dependencies fail.
- Added `READINESS_TIMEOUT_SECONDS` with safe defaults in settings and env
  templates.
- Added deterministic readiness route/service/settings tests, including
  timeout and sanitized failure coverage.

Scope boundaries preserved:

- No CI workflow, startup seeding, knowledge ingestion, migration startup
  behavior, runtime workflow behavior, workflow API behavior, knowledge API
  behavior, frontend behavior, migrations, database models, cloud resources, or
  real secrets were added.

## Current TASK 014.2 Implementation State

Implemented:

- Added additive `docker-compose.prod.yml` for the production-demo stack.
- Added frontend production `Dockerfile` and `.dockerignore`.
- Hardened the backend runtime image to run as a non-root app user.
- Documented production-demo Compose validation/build commands under
  `docs/deployment/`.
- Kept local `docker-compose.yml` and `backend-test` behavior intact.

Scope boundaries preserved:

- No backend readiness dependency code, observability/metrics code, CI
  workflows, cloud resources, runtime behavior, API behavior, frontend feature
  behavior, migrations, database models, auto-seeding, or auto-ingestion were
  added.

## Current TASK 014.1 Implementation State

Implemented:

- Added deployment environment documentation under `docs/deployment/`.
- Added placeholder-only production-demo and CI/test environment templates.
- Annotated backend and frontend local-demo `.env.example` files without
  changing their default values.
- Linked deployment environment guidance from the root, backend, and frontend
  READMEs.

Scope boundaries preserved:

- No Dockerfile, Docker Compose, CI workflow, readiness, observability, runtime,
  backend behavior, frontend behavior, migrations, database models, cloud
  resources, or real secrets were added.

## Current SPEC-014 Planning State

Planning files:

- `.ai/specs/SPEC-014-production-deployment-observability/spec.md`
- `.ai/specs/SPEC-014-production-deployment-observability/tasks.md`

Scope:

- Plan a bounded Docker Compose production-demo deployment target for backend,
  frontend, Postgres, Redis, Qdrant, and MinIO.
- Separate local demo, production demo, and CI/test environment strategies.
- Keep secrets injected through environment variables only; do not commit real
  provider keys, JWT secrets, database passwords, or object storage credentials.
- Keep local deterministic demo behavior intact: fake LLM provider,
  `LLM_RUNTIME_ENABLED=false`, fake embeddings, and `RAG_ENABLED=false` remain
  safe defaults.
- Plan backend readiness checks for critical dependencies while keeping
  optional LLM providers out of default readiness failure criteria.
- Plan frontend production build/container strategy and runtime API/WS URL
  configuration.
- Plan structured observability, redaction, metrics foundations, CI quality
  gates, deployment smoke scripts, and runbook documentation.

Deferrals:

- Kubernetes.
- Cloud-provider-specific Terraform.
- Production secret vault integration.
- Autoscaling.
- Billing/cost dashboards.
- Provider-management UI.
- Token streaming or agent thought streaming.
- Enterprise SSO.
- Production email sending.
- Multi-tenant isolation.
- Real secrets or real customer data.
- Global response envelope rollout.

Planning validation:

- `git status --short` completed and shows only SPEC-014 planning docs, SPEC
  index, and handoff changes.
- `docker-compose config` passed.
- `git diff --check` passed with LF/CRLF warnings only.
- Harness intake recorded as #104.

## SPEC-013 Closure State

Status:

- SPEC-013 approved and ready to close after TASK 013.7 final review.

## Current SPEC-013 Planning State

Planning files:

- `.ai/specs/SPEC-013-rag-document-knowledge-base/spec.md`
- `.ai/specs/SPEC-013-rag-document-knowledge-base/tasks.md`

Planned tasks:

- `TASK 013.1 - Knowledge Base Contracts and Chunking Rules`
- `TASK 013.2 - Embedding Abstraction and Fake Embedding Provider`
- `TASK 013.3 - Demo Document Ingestion CLI with MinIO/Qdrant Upsert`
- `TASK 013.4 - Retrieval Service and Search API`
- `TASK 013.5 - Runtime RAG Grounding Behind Feature Flag`
- `TASK 013.6 - Frontend Evidence/Citations Panel and Demo Docs`
- `TASK 013.7 - RAG Hardening and SPEC-013 Final Review`

Scope:

- Add a procurement knowledge base plan that uses existing SPEC-004 MinIO and
  Qdrant provider foundations.
- Define document/source metadata, chunk metadata, retrieval result DTOs, and
  citation contracts before any implementation.
- Keep embedding concerns separate from chat LLM concerns and use deterministic
  fake embeddings for tests and no-key demos.
- Plan explicit local/demo ingestion only; no backend startup auto-ingestion.
- Keep runtime grounding behind `RAG_ENABLED=false` by default and preserve
  current deterministic `/run`, approval, and `/resume` behavior.
- Add frontend evidence/citation display as a bounded task, without upload UI
  or full document-management UI.

Deferrals:

- Enterprise document permissions.
- Production OCR.
- Arbitrary frontend upload.
- Large-scale ingestion pipelines.
- Multi-tenant knowledge isolation beyond demo/domain metadata.
- Admin document-management UI.
- External SaaS document connectors.
- Live web search.
- Provider SDK additions.
- Provider cost dashboard.
- Production secret vault integration.
- Token streaming or agent thought streaming.
- Global response envelope rollout.
- Migrations/models unless a later implementation task proves a document
  catalog is necessary.

Planning validation:

- `git status --short` completed.
- `docker-compose config` passed.
- `git diff --check` passed with LF/CRLF warnings only.
- Harness intake recorded as #96.

## TASK 013.1 Implementation State

Deliverables:

- `backend/app/knowledge/__init__.py`
- `backend/app/knowledge/schemas.py`
- `backend/app/knowledge/chunking.py`
- `backend/app/knowledge/exceptions.py`
- `backend/app/tests/test_knowledge_contracts.py`
- `backend/app/tests/test_knowledge_chunking.py`
- `backend/README.md` updated with knowledge contract scope

Behavior:

- Adds provider-independent Pydantic v2 contracts for knowledge document
  source types, document metadata, source documents, chunk metadata, chunks,
  citations, retrieval results, search requests/responses, chunking config, and
  chunking results.
- Covers document source types `policy`, `contract`, `pricing`,
  `supplier_profile`, `rfq`, `guideline`, and `compliance_checklist`.
- Enforces bounded text, titles, IDs, tags, citation excerpts, search `top_k`,
  and JSON-compatible metadata. Metadata validators reject sensitive key names
  such as secrets, tokens, API keys, raw prompts, raw provider payloads, and
  chain-of-thought markers.
- Adds deterministic text normalization, SHA-256 content checksums, stable
  chunk IDs, and character-based chunking with overlap and paragraph-boundary
  preference.
- Adds focused unit tests for source types, DTO validation, metadata safety,
  citation/search bounds, config validation, deterministic hashing/chunk IDs,
  ordering, overlap, no empty chunks, and chunk size bounds.
- Does not implement embeddings, Qdrant calls, MinIO calls, ingestion CLI,
  retrieval/search API, runtime RAG grounding, frontend behavior, migrations,
  database models, provider SDKs, tokenizer/OCR/PDF dependencies, or live
  external calls.

## TASK 013.2 Implementation State

Deliverables:

- `backend/app/knowledge/embeddings.py`
- `backend/app/knowledge/__init__.py` updated
- `backend/app/knowledge/exceptions.py` updated
- `backend/app/config/settings.py` updated with safe embedding env wiring
- `backend/.env.example` updated with embedding env defaults
- `backend/app/tests/test_knowledge_embeddings.py`
- `backend/app/tests/test_knowledge_embedding_settings.py`
- `backend/README.md` updated with embedding scope

Behavior:

- Adds provider-independent embedding contracts separate from chat LLM
  contracts: provider enum, error categories, settings, input/request/result,
  batch result, vector metadata, model capabilities, async client protocol,
  service, and factory.
- Adds deterministic `FakeEmbeddingClient` only. It normalizes text, expands
  SHA-256 digests into bounded float vectors, preserves batch order, and makes
  no network calls.
- Adds safe defaults: `EMBEDDING_PROVIDER=fake`,
  `EMBEDDING_MODEL=fake-hash-embedding`, `EMBEDDING_DIMENSIONS=64`, and
  `EMBEDDING_BATCH_SIZE=32`.
- Embedding settings load without API keys and are exposed through
  `Settings.embedding_settings`.
- Reuses TASK 013.1 metadata safety validation so embedding metadata remains
  JSON-compatible and rejects sensitive keys such as secrets, tokens, API keys,
  raw prompts, raw provider payloads, and chain-of-thought markers.
- Adds tests for settings defaults/overrides, bounds, contracts, deterministic
  vectors, configured dimensions, batch order, repeated batch calls, blank and
  oversized input rejection, vector value bounds, and default factory/service
  behavior.
- Does not implement real embedding providers, call `LLMService`, call chat
  provider clients, call Qdrant or MinIO, add ingestion CLI, add retrieval/API,
  change runtime/frontend behavior, add migrations/models, add provider SDKs,
  or make external calls.

## TASK 013.3 Implementation State

Deliverables:

- `backend/app/demo/knowledge_documents.py`
- `backend/app/knowledge/ingestion.py`
- `backend/app/knowledge/ingest_demo.py`
- `backend/app/knowledge/__init__.py` updated
- `backend/app/knowledge/exceptions.py` updated
- `backend/app/tests/test_knowledge_demo_documents.py`
- `backend/app/tests/test_knowledge_ingestion.py`
- `backend/app/tests/test_knowledge_ingestion_cli.py`
- `docs/demo/DATASET_INVENTORY.md` updated
- `docs/demo/DEMO_RUNBOOK.md` updated
- `docs/demo/FRONTEND_SMOKE_FLOW.md` updated
- `backend/README.md` updated

Behavior:

- Adds deterministic local-demo knowledge documents for procurement policy,
  Acme contract terms, supplier evaluation notes, pricing guidance, and
  compliance checklist evidence.
- Adds explicit `python -m app.knowledge.ingest_demo --confirm-local-demo`
  CLI for local-demo knowledge ingestion only.
- CLI supports `--dry-run`, `--json`, and `--collection-name`.
- Mutating ingestion requires `--confirm-local-demo`; dry-run is non-writing.
- Ingestion uses TASK 013.1 chunking/contracts and TASK 013.2 fake embeddings
  by default.
- Ingestion stores original source text in MinIO through
  `ObjectStorageProvider` and upserts deterministic chunk vectors into Qdrant
  through `VectorStore`.
- Vector payloads include bounded safe metadata: document id/title/source type,
  domain, checksum, chunk id/index, citation label, bounded text, embedding
  provider/model/dimensions, and demo markers.
- Idempotency uses deterministic object keys and deterministic UUIDv5 vector
  point ids derived from chunk ids.
- Does not implement retrieval/search APIs, runtime RAG grounding, frontend
  citation panels, upload UI, migrations, database models, real embedding
  providers, provider SDKs, or backend startup auto-ingestion.

## TASK 013.4 Implementation State

Deliverables:

- `backend/app/knowledge/retrieval.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/__init__.py` updated
- `backend/app/main.py` updated
- `backend/app/core/dependencies.py` updated
- `backend/app/knowledge/schemas.py` updated with catalog response DTOs
- `backend/app/knowledge/exceptions.py` updated
- `backend/app/tests/test_knowledge_retrieval.py`
- `backend/app/tests/test_knowledge_api.py`
- `backend/app/tests/test_knowledge_contracts.py` updated
- `backend/README.md` updated
- `docs/demo/DATASET_INVENTORY.md` updated
- `docs/demo/DEMO_RUNBOOK.md` updated

Behavior:

- Adds provider-independent `KnowledgeRetrievalService` that embeds search
  queries through `EmbeddingService`, searches Qdrant through the existing
  `VectorStore` abstraction, and normalizes vector payloads into bounded
  `KnowledgeRetrievalResult` and `KnowledgeCitation` DTOs.
- Adds authenticated read-only API routes:
  `POST /api/v1/knowledge/search`,
  `GET /api/v1/knowledge/documents`, and
  `GET /api/v1/knowledge/documents/{document_id}`.
- Uses the same baseline read roles as workflow reads: Admin, Manager, Sales,
  Legal, Finance, and Viewer.
- Returns empty search results when the configured knowledge collection is not
  present yet, so local API reads remain safe before ingestion.
- Applies native exact-match vector filters for single source type/document id
  and domain; multi-value filters and minimum-score checks are applied safely
  in the retrieval service.
- Catalog endpoints return deterministic demo document metadata and bounded
  previews only; full source documents remain in object storage/demo contracts.
- Maps missing documents to 404 and retrieval provider failures to safe 503
  responses.
- Does not implement runtime RAG grounding, frontend citation panels, upload
  UI, migrations, database models, real embedding providers, chat LLM calls,
  workflow event publishing, or backend startup auto-ingestion.

## TASK 013.5 Implementation State

Deliverables:

- `backend/app/runtime/rag_adapter.py`
- `backend/app/runtime/service.py` updated
- `backend/app/runtime/__init__.py` updated
- `backend/app/config/settings.py` updated with safe RAG env wiring
- `backend/.env.example` updated with RAG env defaults
- `backend/app/core/dependencies.py` updated with conditional retrieval wiring
- `backend/app/tests/test_runtime_rag_grounding.py`
- `backend/README.md` updated
- `docs/demo/DEMO_RUNBOOK.md` updated
- `docs/demo/DATASET_INVENTORY.md` updated

Behavior:

- Adds `RAG_ENABLED=false` plus bounded `RAG_TOP_K`,
  `RAG_MINIMUM_SCORE`, `RAG_MAX_CONTEXT_CHARS`, and
  `RAG_EVENT_PAYLOAD_MAX_CHARS` settings.
- Adds provider-independent runtime grounding through
  `RuntimeRAGGroundingAdapter`, depending only on the
  `KnowledgeRetrievalService` search protocol.
- Keeps the disabled path silent: no retrieval calls, no grounding events, and
  existing deterministic `/run` and `/resume` behavior remain unchanged.
- When enabled, retrieves evidence only for compliance, validation/finance, and
  approval stages, attaches bounded citation summaries into `runtime_context.rag`,
  `outputs.evidence`, and the current stage output, and appends safe
  `knowledge.grounding.started`, `knowledge.grounding.completed`, and
  `knowledge.grounding.failed` events.
- Retrieval failures degrade safely with a bounded failure marker/event and do
  not fail the workflow runtime.
- Resume/email-preparation continuation does not perform RAG retrieval.
- Does not add frontend behavior, API contract changes, migrations, database
  models, provider SDKs, upload UI, token streaming, raw embeddings, raw vector
  payload persistence, or chat LLM calls from grounding code.

## TASK 013.6 Implementation State

Deliverables:

- `frontend/lib/api/types.ts` updated with knowledge/citation DTOs
- `frontend/lib/api/knowledge.ts`
- `frontend/components/workflows/workflow-evidence-panel.tsx`
- `frontend/components/knowledge/knowledge-search-panel.tsx`
- `frontend/components/knowledge/knowledge-document-list.tsx`
- `frontend/components/workflows/workflow-detail-view.tsx` updated
- `frontend/tests/knowledge-api.test.ts`
- `frontend/tests/workflow-evidence.test.tsx`
- `frontend/tests/workflow-pages.test.tsx` updated
- `frontend/README.md` updated
- `docs/demo/DEMO_RUNBOOK.md` updated
- `docs/demo/FRONTEND_SMOKE_FLOW.md` updated
- `docs/demo/DATASET_INVENTORY.md` updated

Behavior:

- Adds typed frontend knowledge API helpers for:
  `POST /api/v1/knowledge/search`,
  `GET /api/v1/knowledge/documents`, and
  `GET /api/v1/knowledge/documents/{document_id}`.
- Adds workflow evidence/citation display on workflow detail pages. The panel
  extracts bounded citation objects from `runtime_context.rag`,
  `outputs.evidence`, `stage_outputs`, and loaded grounding events when those
  events include citation objects.
- Shows an honest empty state when no RAG evidence is attached and never
  fabricates evidence or streamed events.
- Adds lightweight knowledge search and demo document catalog components using
  existing authenticated backend knowledge endpoints.
- Handles loading, empty, 401/403/404/422/503, and generic error states where
  applicable.
- Suppresses raw embeddings, raw vector payloads, raw prompts, provider
  payloads, secrets, and chain-of-thought fields from evidence rendering.
- Updates demo docs for knowledge ingestion, `RAG_ENABLED=true`, evidence
  panel checks, knowledge search/catalog checks, and no-key fake-embedding
  behavior.
- Does not modify backend code, runtime behavior, knowledge API backend
  behavior, workflow API behavior, demo ingestion behavior, migrations, database
  models, upload UI, admin document-management UI, provider-management UI,
  token streaming, agent-thought display, or frontend dependencies.

## TASK 013.7 Final Review State

Status:

- SPEC-013 approved and ready to close.

Evidence:

- Verified knowledge contracts/chunking, fake embedding abstraction, demo
  ingestion, retrieval/search API, feature-flagged runtime grounding, frontend
  evidence/search/catalog UI, demo docs, and out-of-scope boundaries.
- Hardened stale docs that still claimed frontend citation display was not
  wired after TASK 013.6.
- Confirmed `.env.example` keeps API-key placeholders empty and RAG/embedding
  defaults offline-safe.
- Confirmed no dirty migration/model files and no new upload/admin document UI,
  provider SDK, tokenizer/OCR/PDF dependency, fake streamed events, global
  response envelope, real secrets, live external provider calls, or backend
  startup auto-ingestion.

Validation:

- `docker-compose config` passed.
- `docker-compose up -d postgres redis qdrant minio` completed.
- `docker-compose run --rm backend-test alembic upgrade head` passed.
- `docker-compose build backend-test` passed.
- `docker-compose run --rm backend-test pytest` passed: 660 passed, 1 skipped.
- `docker-compose run --rm backend-test ruff check .` passed.
- `docker-compose run --rm backend-test black --check .` passed.
- `docker-compose run --rm backend-test mypy app` passed.
- `python -m app.knowledge.ingest_demo --help` passed.
- Knowledge ingestion dry-run JSON reported `committed:false`, 5 documents, and
  5 chunks.
- Two confirmed knowledge ingestion JSON runs reported `committed:true`, 5
  documents, 5 chunks, 5 reused objects, and 5 vector upserts.
- `python -m app.demo.seed --confirm-local-demo --dry-run --json` passed with
  `committed:false`.
- Frontend `npm install`, `npm run lint`, `npm run build`, serial
  `npm run typecheck`, and `npm test` passed: 55 frontend tests.
- `git diff --check` passed with LF/CRLF warnings only.

Non-blocking notes:

- Existing LangGraph pending deprecation warning remains non-blocking.
- Existing Starlette TestClient deprecation warning remains non-blocking.
- Existing Vitest/Vite CJS deprecation warning remains non-blocking.
- Existing frontend npm audit advisories remain a future dependency
  maintenance item.
- Running frontend `build` and `typecheck` in parallel can race over generated
  `.next/types`; the serial requested gate passes.

## Current SPEC-012 Planning State

Planning files:

- `.ai/specs/SPEC-012-human-approval-and-resume/spec.md`
- `.ai/specs/SPEC-012-human-approval-and-resume/tasks.md`

Planned tasks:

- `TASK 012.1 - Approval Contracts, Lifecycle Rules, and Planning Fixtures` -
  Implemented
- `TASK 012.2 - Backend Approval Service and Audit/Event Persistence` -
  Implemented
- `TASK 012.3 - Approval and Resume API Endpoints with RBAC` - Implemented
- `TASK 012.4 - Runtime Resume Implementation` - Implemented
- `TASK 012.5 - Frontend Approval Panel and API Client` - Implemented
- `TASK 012.6 - Approval Timeline, Demo Runbook, and Seed Updates` -
  Implemented
- `TASK 012.7 - Human Approval Hardening and SPEC-012 Final Review` -
  Implemented

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

## TASK 012.2 Implementation State

Deliverables:

- `backend/app/approvals/service.py`
- `backend/app/approvals/__init__.py` updated
- `backend/app/approvals/exceptions.py` updated
- `backend/app/tests/test_approval_service.py`

Behavior:

- Adds explicit `ApprovalService` for backend-domain approval decisions.
- Records `approve`, `reject`, and `request_changes` decisions using existing
  `Workflow.state_payload`, `WorkflowEvent`, and `AuditLog` persistence.
- Stores bounded approval history under `WorkflowState.approval` keys:
  `approval_history` and `approval_state`.
- Uses TASK 012.1 lifecycle helpers so approval decisions are accepted only
  from `WAITING_APPROVAL`, terminal workflows reject approval mutation, and
  final decisions prevent later final decisions.
- Uses TASK 012.1 policy helpers as service-level defense in depth: Admin and
  Manager can submit decisions; Viewer and other non-approval roles are
  rejected in this slice.
- Transitions `approve` to existing `APPROVED` and `reject` to existing
  `REJECTED`; `request_changes` leaves status as `WAITING_APPROVAL` and remains
  non-final.
- Persists approval decision events using the existing `WorkflowEventService`
  and TASK 012.1 approval event constants.
- Persists a bounded `workflow.approval_decision_submitted` audit record for
  the decision itself.
- Flushes through existing services/session but does not commit; callers own
  transaction boundaries.
- Redacts sensitive approval metadata keys before storing state history and
  avoids raw provider payloads, state payloads, request payloads, API keys, or
  secrets in event/audit payloads.
- Does not add approval/resume API endpoints, runtime resume execution,
  frontend behavior, migrations, model changes, new workflow statuses, or
  auth/RBAC policy changes.

## TASK 012.3 Implementation State

Deliverables:

- `backend/app/api/v1/workflows.py` updated
- `backend/app/core/dependencies.py` updated
- `backend/app/tests/test_workflow_api_approval.py`
- `backend/app/tests/test_workflow_api_router.py` updated
- `backend/app/tests/test_workflow_api_runtime_run.py` updated
- `backend/README.md` updated

Behavior:

- Adds `POST /api/v1/workflows/{workflow_id}/approval` for authenticated
  Admin/Manager approval decisions through `ApprovalService`.
- Adds `GET /api/v1/workflows/{workflow_id}/approval/history` for authenticated
  workflow read roles.
- Adds `POST /api/v1/workflows/{workflow_id}/resume` as a typed, authenticated,
  Admin/Manager-only `501` boundary. It does not call `RuntimeService`, mutate
  workflow state, or execute resume.
- Keeps approval endpoint transaction ownership at the API route boundary:
  commit only after successful `ApprovalService` execution.
- Maps missing workflows to `404`, approval invalid-state/terminal/duplicate
  lifecycle errors to `409`, and approval permission failures to `403`.
- Adds route tests for approve, reject, request_changes, approval history,
  duplicate final decisions, invalid state, terminal state, missing workflow,
  unauthenticated requests, RBAC denial, resume boundary behavior, and
  `/run` route stability.
- Uses dependency injection for `ApprovalService` and reuses the configured
  `WorkflowEventService` so persisted approval events can use the existing
  event publisher path in production.
- Does not implement runtime resume execution, change `/run`, change frontend
  behavior, add migrations/models, add new workflow statuses, send email, or
  introduce a global response envelope.

## TASK 012.4 Implementation State

Deliverables:

- `backend/app/runtime/service.py` updated
- `backend/app/runtime/__init__.py` updated
- `backend/app/api/v1/workflows.py` updated
- `backend/app/tests/test_runtime_resume.py`
- `backend/app/tests/test_workflow_api_approval.py` updated
- `backend/README.md` updated

Behavior:

- Adds `RuntimeService.resume_workflow_after_approval()` for the explicit
  post-approval continuation.
- Requires workflow status `APPROVED` and an approving approval-history record
  through the existing approval lifecycle helper.
- Rejects missing, non-approved, rejected, request-changes-only, terminal, and
  already-completed workflows with safe errors.
- Executes only the existing deterministic `email_preparation` node; it does
  not send real email and does not implement arbitrary graph jump/resume.
- Transitions through existing lifecycle rules:
  `APPROVED -> GENERATING_EMAIL -> COMPLETED`.
- Persists bounded resume metadata in workflow runtime context and keeps
  state/event/audit payloads free of secrets, raw provider payloads, raw
  prompts, and unbounded input.
- Persists resume request, node start/completion, and resume completed events
  through `WorkflowEventService`; resume failures persist safe failure events.
  Existing event append audit behavior records audit evidence for these events.
- Updates `POST /api/v1/workflows/{workflow_id}/resume` to call
  `RuntimeService` and commit at the route boundary on success.
- Preserves `/run` behavior and contract: `/run` still stops at
  `WAITING_APPROVAL` and never auto-resumes.
- Keeps LLM runtime feature-flag behavior intact; email preparation remains
  deterministic because SPEC-011 does not define an LLM email prompt yet.
- Does not add frontend behavior, migrations, model changes, new statuses,
  email sending, RAG/document upload, provider-management UI, token streaming,
  or a global response envelope.

## TASK 012.5 Implementation State

Deliverables:

- `frontend/lib/api/types.ts` updated
- `frontend/lib/api/workflows.ts` updated
- `frontend/components/workflows/workflow-approval-panel.tsx`
- `frontend/components/workflows/workflow-approval-history.tsx`
- `frontend/components/workflows/workflow-detail-view.tsx` updated
- `frontend/tests/workflow-api.test.ts` updated
- `frontend/tests/workflow-pages.test.tsx` updated
- `frontend/tests/workflow-approval.test.tsx`
- `frontend/README.md` updated

Behavior:

- Adds typed frontend DTOs for approval decisions, approval records, approval
  history, resume request, and resume response.
- Adds typed workflow API client helpers for:
  `POST /api/v1/workflows/{workflow_id}/approval`,
  `GET /api/v1/workflows/{workflow_id}/approval/history`, and
  `POST /api/v1/workflows/{workflow_id}/resume`.
- Encodes workflow ids in workflow API paths and continues attaching bearer
  tokens through the existing API client.
- Extends workflow detail loading to fetch workflow detail, persisted events,
  and approval history together.
- Adds a workflow approval panel that shows approve, reject, and
  request-changes actions while a workflow is `WAITING_APPROVAL`.
- Enforces only local comment validation in the frontend; backend 403/409
  responses remain the authorization and lifecycle source of truth.
- Adds explicit resume UI for approved/resume-ready workflows. Resume calls
  `/resume` with `{}` and never calls `/run`.
- Adds approval history rendering with decision, actor email/id, comment,
  decided timestamp, previous status, and next status.
- Refreshes workflow detail, events, and approval history after approval or
  resume actions.
- Does not modify backend/runtime behavior, auth/RBAC policy, demo seeds,
  runbook docs, WebSocket protocol, frontend framework dependencies, or
  existing `/run` behavior.

## TASK 012.6 Implementation State

Deliverables:

- `backend/app/demo/contracts.py` updated
- `backend/app/demo/workflow_seed.py` updated
- `backend/app/tests/test_demo_seed_contracts.py` updated
- `backend/app/tests/test_demo_workflow_seed.py` updated
- `docs/demo/DATASET_INVENTORY.md` updated
- `docs/demo/DEMO_RUNBOOK.md` updated
- `docs/demo/FRONTEND_SMOKE_FLOW.md` updated
- `README.md` updated
- `docs/llm/LOCAL_LLM_DEMO.md` updated for stale limitation copy
- `docs/llm/PROVIDER_SETUP.md` updated for stale limitation copy

Behavior:

- Preserves `rfq-001-waiting-approval-history` as the primary
  `WAITING_APPROVAL` workflow with no final seeded approval decision so
  Manager/Admin can approve it live.
- Adds deterministic approval/resume seed examples:
  `rfq-001-approved-ready-to-resume`,
  `rfq-001-completed-resumed-history`, and `rfq-001-rejected-history`.
- Stores seeded approval history through the same `approval_history` and
  `approval_state` payload keys used by `ApprovalService`.
- Builds seeded approval history records with `ApprovalRecord`, bounded demo
  metadata, the seeded Manager as actor, and deterministic UUIDv5 decision ids.
- Adds persisted approval/resume timeline events using existing event
  constants: `workflow.approval.approved`,
  `workflow.approval.rejected`, `workflow.approval.changes_requested`,
  `workflow.resume_requested`, and `workflow.resumed`.
- Adds completed resume metadata under `runtime_context.resume_state` and an
  email-preparation preview that explicitly does not send email.
- Updates demo runbook and frontend smoke flow to cover request changes,
  approval, explicit `/resume`, approval history, approval/resume timeline
  events, and approval RBAC checks.
- Keeps seed CLI behavior explicit, local-demo-only, and idempotent.
- Does not modify backend approval service behavior, runtime resume behavior,
  workflow API behavior, frontend behavior, migrations, database models, new
  statuses, email sending, RAG/document upload, provider-management UI, token
  streaming, fake live events, or production seed behavior.

## TASK 012.7 Final Review State

Status:

- SPEC-012 approved and ready to close.

Evidence:

- Verified approval contracts for `approve`, `reject`, `request_changes`,
  bounded approval records/history, typed resume request/response, rejection
  comment validation, and JSON-safe metadata.
- Verified lifecycle helpers allow approval decisions only from
  `WAITING_APPROVAL`, block terminal and duplicate final decisions, keep
  `request_changes` non-final, and require `APPROVED` plus a final approve
  record for resume.
- Verified RBAC policy helpers use existing roles: Admin/Manager can approve,
  reject, request changes, and resume; Sales/Legal/Finance/Viewer cannot submit
  approval or resume mutations in this slice.
- Verified `ApprovalService` stores `approval_history` and `approval_state`
  through existing workflow state payload, persists WorkflowEvent records and
  audit evidence, flushes without service-level commit, and adds no migrations,
  tables, model fields, or workflow statuses.
- Verified workflow API endpoints:
  `POST /api/v1/workflows/{workflow_id}/approval`,
  `GET /api/v1/workflows/{workflow_id}/approval/history`, and
  `POST /api/v1/workflows/{workflow_id}/resume`; existing `/run` remains
  stable.
- Verified `RuntimeService.resume_workflow_after_approval()` is bounded to the
  post-approval email-preparation continuation, requires approval, transitions
  through `APPROVED -> GENERATING_EMAIL -> COMPLETED`, persists resume events,
  does not send real email, and does not add arbitrary graph jump/resume.
- Verified frontend approval/resume client functions, detail page approval
  panel, approval history, explicit `/resume` action, error handling, and that
  resume does not call `/run`.
- Verified demo seed data preserves the primary live `WAITING_APPROVAL`
  workflow and includes deterministic approved, completed-resumed, and rejected
  approval examples with deterministic event history.
- Hardened stale documentation copy in `backend/README.md` and
  `docs/llm/LOCAL_LLM_DEMO.md` so `/resume` is no longer described as deferred
  after SPEC-012.

Validation:

- `git status --short` completed.
- `docker-compose config` passed.
- `docker-compose up -d postgres redis qdrant minio` passed.
- `docker-compose run --rm backend-test alembic upgrade head` passed.
- `docker-compose build backend-test` passed.
- `docker-compose run --rm backend-test pytest` passed: 579 passed, 1 skipped.
- `docker-compose run --rm backend-test ruff check .` passed.
- `docker-compose run --rm backend-test black --check .` passed.
- `docker-compose run --rm backend-test mypy app` passed.
- `docker-compose run --rm backend-test python -m app.demo.seed --help`
  passed.
- Two confirmed seed runs passed and reused existing data:
  6 workflows reused, 14 events reused, 0 created.
- `docker-compose run --rm backend-test python -m app.demo.seed
  --confirm-local-demo --dry-run --json` passed with `committed:false`.
- `cd frontend && npm install` passed.
- `cd frontend && npm run lint` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm test` passed: 43 passed.
- `git diff --check` passed with LF/CRLF warnings only.
- Focused approval/runtime/demo backend tests passed: 111 passed, 1 skipped.
- Focused frontend approval test passed: 9 passed.

Non-blocking notes:

- Existing LangGraph pending deprecation warning remains non-blocking.
- Existing Starlette TestClient deprecation warning remains non-blocking.
- Existing frontend npm audit advisories remain a future dependency
  maintenance item.
- Existing Vite CJS deprecation warning remains non-blocking.
- LF/CRLF warnings from `git diff --check` remain non-blocking when no
  whitespace errors are reported.

Out-of-scope confirmation:

- No new migrations, database models/tables, workflow statuses, email sending,
  RAG/document upload, admin approval-policy UI, provider-management UI,
  production secret vault, token streaming, agent thought streaming, fake
  streamed events, global response envelope, deployment automation,
  billing/cost dashboard, production seed behavior, live provider smoke tests,
  or real API keys/secrets were added.

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
