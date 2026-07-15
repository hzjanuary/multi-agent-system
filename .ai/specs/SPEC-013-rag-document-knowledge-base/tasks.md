# SPEC-013 Tasks - RAG and Document Knowledge Base

## Task List

### TASK 013.1 - Knowledge Base Contracts and Chunking Rules

Goal: Define provider-independent knowledge base contracts, source types,
citation DTOs, chunking rules, deterministic IDs, and validation helpers
without writing to Qdrant, MinIO, Postgres, runtime, API routes, or frontend.

Scope:

- Add a backend knowledge package/module structure.
- Define typed contracts for document metadata, source types, chunk metadata,
  retrieval results, and citations.
- Define chunking configuration and pure chunking helpers.
- Define stable content hash and deterministic document/chunk ID helpers.
- Define bounded excerpt and metadata sanitization helpers.
- Inventory which existing dataset files are planned for SPEC-013 ingestion.
- Add tests for contracts, bounds, deterministic IDs, chunking, hashing, and
  dataset path references.

Acceptance criteria:

- Knowledge contracts exist and import cleanly.
- Source types cover policy, contract, pricing, supplier_profile, rfq, and
  guideline.
- Chunking is deterministic for the same source text/config.
- Chunk text, excerpts, and metadata are bounded.
- Stable IDs and checksums are deterministic.
- No Qdrant/MinIO/Postgres writes are implemented.
- No API, runtime, frontend, migrations, model changes, provider SDKs, or live
  external calls are added.

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

### TASK 013.2 - Embedding Abstraction and Fake Embedding Provider

Goal: Add provider-independent embedding contracts and a deterministic fake
embedding provider for tests and no-key local/demo use, without real embedding
provider calls or retrieval integration.

Scope:

- Add embedding provider protocol/interface.
- Add embedding request/response schemas and model capability metadata.
- Add embedding settings with safe defaults such as `EMBEDDING_PROVIDER=fake`,
  `EMBEDDING_DIMENSIONS`, and bounded timeout/retry values if needed.
- Add deterministic fake embedding provider.
- Add error categories for embedding configuration, invalid input, timeout,
  unavailable provider, invalid response, and unknown failures.
- Add tests for settings defaults, deterministic vectors, dimensions, bounds,
  and no-key behavior.
- Update `.env.example` and backend README only if settings are added.

Acceptance criteria:

- Embedding contracts exist and are separate from chat LLM contracts.
- Fake embedding provider is deterministic and offline.
- No real provider keys are required at settings load time.
- Embedding dimensions are explicit and Qdrant-compatible.
- Tests do not use external network or live providers.
- No Qdrant/MinIO ingestion, runtime, API, frontend, migrations, model changes,
  provider SDKs, or chat LLM behavior changes are added.

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

### TASK 013.3 - Demo Document Ingestion CLI with MinIO/Qdrant Upsert

Goal: Add an explicit local/demo-safe ingestion command that reads deterministic
demo documents, chunks them, stores source objects in MinIO where useful, and
upserts chunk vectors into Qdrant using fake embeddings by default.

Scope:

- Add ingestion service/orchestration module.
- Use TASK 013.1 contracts and chunking helpers.
- Use TASK 013.2 fake embedding provider by default.
- Use existing `ObjectStorageProvider` and `VectorStore` abstractions.
- Create/upsert a deterministic Qdrant collection.
- Store source documents in MinIO under deterministic object keys where
  appropriate.
- Add explicit CLI such as
  `python -m app.knowledge.ingest_demo --confirm-local-demo`.
- Add `--dry-run` and `--json` if practical.
- Keep ingestion idempotent and safe to rerun.
- Add tests for ingestion summary, idempotency, dry-run, Qdrant upsert payloads,
  MinIO object keys, and no auto-run behavior.

Acceptance criteria:

- Demo ingestion CLI exists and imports cleanly.
- Mutating ingestion requires an explicit local-demo confirmation flag.
- CLI does not run on import or backend startup.
- Demo documents are chunked deterministically.
- Qdrant upsert payloads use stable chunk IDs and bounded metadata.
- MinIO object keys are deterministic when source storage is used.
- Rerunning ingestion does not create duplicate chunks.
- No public API endpoint, runtime integration, frontend UI, migrations, model
  changes, provider SDKs, or live external calls are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d qdrant minio
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --help
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
git diff --check
```

### TASK 013.4 - Retrieval Service and Search API

Goal: Add a provider-independent retrieval service and bounded authenticated
search/read APIs for indexed knowledge, using existing Qdrant and embedding
abstractions.

Scope:

- Add retrieval service that embeds query text and searches Qdrant.
- Normalize Qdrant results into typed retrieval/citation DTOs.
- Support bounded `top_k` and filters for source type, domain, document ID, and
  version/effective date when available.
- Add API route namespace under `/api/v1/knowledge` if scoped:
  - `POST /api/v1/knowledge/search`
  - `GET /api/v1/knowledge/documents`
  - `GET /api/v1/knowledge/documents/{document_id}`
- Use existing auth/RBAC patterns.
- Prefer Admin/Manager for any ingestion-like action; allow workflow read roles
  for safe read/search endpoints.
- Add tests for service search, filter normalization, error mapping, auth/RBAC,
  missing document behavior, and bounded payloads.

Acceptance criteria:

- Retrieval service exists and returns typed retrieval results.
- Search uses fake embeddings in tests and does not require external network.
- API responses are direct Pydantic models.
- API routes are authenticated and RBAC-protected.
- Raw vector payloads and unbounded chunk text are not exposed.
- No runtime integration, frontend UI, upload UI, migrations, model changes,
  provider SDKs, or live external calls are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d postgres qdrant
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 013.5 - Runtime RAG Grounding Behind Feature Flag

Goal: Integrate retrieval evidence into the existing runtime behind a disabled
default feature flag, preserving deterministic runtime behavior when RAG is
off.

Scope:

- Add RAG settings such as `RAG_ENABLED=false`, collection name, top-k, and
  context bounds.
- Inject retrieval service into runtime only when enabled.
- Use retrieval evidence in retrieval, compliance, validation/finance, and
  approval package stages where compatible.
- When `LLM_RUNTIME_ENABLED=false`, attach deterministic retrieved evidence
  summaries/citations without chat provider calls.
- When `LLM_RUNTIME_ENABLED=true`, pass bounded retrieved context into existing
  prompt builders.
- Store only bounded citation DTOs and evidence summaries in workflow state.
- Append safe WorkflowEvent evidence summaries if useful.
- Add tests for disabled default path, enabled fake-retrieval path, citation
  state writes, prompt context bounds, and no raw document/prompt persistence.

Acceptance criteria:

- `RAG_ENABLED=false` preserves current deterministic runtime behavior.
- No retrieval service call happens when RAG is disabled.
- Enabled path uses retrieval service/interface, not Qdrant directly.
- Runtime state stores bounded citations, not raw documents.
- Existing `/run`, approval, and `/resume` contracts remain stable.
- Tests use fake retrieval/embeddings and no live external network.
- No frontend behavior, migrations, model changes, provider SDKs, token
  streaming, or upload/admin UI are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 013.6 - Frontend Evidence/Citations Panel and Demo Docs

Goal: Add a lightweight workflow detail evidence/citations panel and update
demo documentation for the knowledge base ingestion and grounded evidence flow,
without adding upload UI or full document management UI.

Scope:

- Add frontend DTOs for citations/evidence if backend responses or workflow
  state expose them.
- Add evidence/citations panel to workflow detail.
- Render citations from workflow state/events or retrieval/search responses as
  scoped by prior tasks.
- Show source title, source type, section/page, excerpt, and relevance score.
- Add loading/empty/error states where API calls are involved.
- Keep copy honest: "retrieved evidence", not final legal advice.
- Update demo runbook and smoke flow with ingestion command, run workflow, show
  citations, approve, and resume.
- Add frontend component/API tests if UI is changed.

Acceptance criteria:

- Workflow detail can display bounded evidence/citations.
- UI does not show fake citations as if loaded.
- No upload UI, admin document-management UI, provider-management UI, token
  streaming, or raw document display is added.
- Demo docs include knowledge ingestion and citation checkpoints.
- Frontend quality gate passes.

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

### TASK 013.7 - RAG Hardening and SPEC-013 Final Review

Goal: Verify SPEC-013 is complete, deterministic by default, safe, documented,
and ready to close.

Scope:

- Review contracts, chunking, embedding abstraction, ingestion CLI, retrieval
  service/API, runtime integration, frontend evidence panel, demo docs, and
  out-of-scope boundaries.
- Confirm no real provider keys or live external network calls are required.
- Confirm `RAG_ENABLED=false` preserves current deterministic runtime.
- Confirm Qdrant/MinIO usage stays behind provider interfaces.
- Confirm no unplanned migrations/model changes, upload UI, admin document UI,
  provider SDKs, or global response envelope were introduced.
- Harden only tiny docs/test blockers within SPEC-013 scope.
- Record final Harness review evidence.

Acceptance criteria:

- Knowledge base contracts are complete and bounded.
- Demo ingestion is explicit, local-demo-safe, and idempotent.
- Retrieval returns typed evidence and citations.
- Runtime RAG grounding is feature-flagged and deterministic by default.
- Frontend citations are readable and bounded if implemented.
- Demo docs are updated.
- Full quality gates pass.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis qdrant minio
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
