# SPEC-013 - RAG and Document Knowledge Base

## Status

Draft

## Context

Enterprise Multi-Agent OS now has the foundations needed for a bounded
procurement knowledge base:

- SPEC-004 provides interface-first storage providers for Redis, Qdrant, and
  MinIO.
- SPEC-006 provides deterministic LangGraph runtime stages, including a
  retrieval stage placeholder.
- SPEC-007 exposes authenticated workflow REST APIs using direct Pydantic
  response models.
- SPEC-008 streams persisted workflow events over WebSocket.
- SPEC-010 provides deterministic demo datasets, documents, workflows, and a
  runbook.
- SPEC-011 provides a feature-flagged LLM service and structured prompt/output
  contracts while preserving no-key deterministic defaults.
- SPEC-012 completes human approval and explicit resume.

SPEC-013 plans the retrieval and grounding layer. It should ingest local/demo
documents, chunk and index them into Qdrant, store source objects in MinIO where
appropriate, retrieve bounded evidence, and expose citations to runtime and
frontend views. It must keep the board demo deterministic and no-key safe by
default.

## Product Goal

- Let procurement workflows use a local/demo knowledge base for policy,
  contract, pricing, supplier, and compliance evidence.
- Support board-ready evidence grounding:
  - compliance analysis cites policy clauses
  - finance/risk analysis cites pricing or contract evidence
  - approval package shows evidence summaries
- Keep no-key deterministic demo behavior possible.
- Keep chat LLM provider usage behind existing SPEC-011 feature flags.
- Use existing Qdrant and MinIO provider foundations from SPEC-004.
- Preserve existing workflow, approval, resume, and streaming behavior unless a
  later SPEC-013 task explicitly scopes integration.

## Non-goals

- Enterprise document permissions.
- Production-grade OCR.
- Arbitrary frontend file upload unless explicitly scoped later.
- Large-scale ingestion pipelines.
- Multi-tenant knowledge isolation beyond safe demo/domain metadata.
- Admin document-management UI.
- External SaaS document connectors.
- Live web search.
- Provider cost dashboard.
- Production secret vault integration.
- LLM token streaming or agent thought streaming.
- Global response envelope rollout.
- Provider SDK additions.
- Backend/frontend/runtime behavior changes during planning.

## Knowledge Base Domain Model

SPEC-013 should add provider-independent knowledge base contracts before any
infrastructure writes.

### Document Source Types

Planned source types:

- `policy`
- `contract`
- `pricing`
- `supplier_profile`
- `rfq`
- `guideline`

These values should be represented by a typed enum and reused in ingestion,
retrieval, API, runtime, and frontend DTOs.

### Document Metadata

Document metadata should be JSON-compatible and bounded:

- `document_id`
- `title`
- `source_type`
- `domain`
- `version`
- `effective_date`
- `owner`
- `team`
- `object_storage_key`
- `checksum`
- `content_type`
- `dataset_path` for demo/reference documents

Metadata must not contain secrets, raw provider payloads, or unbounded document
content.

### Chunk Metadata

Chunk metadata should describe bounded text segments:

- `chunk_id`
- `document_id`
- `chunk_index`
- `text`
- `citation_label`
- `page`
- `section`
- `start_offset`
- `end_offset`
- `checksum`
- `token_count` or `character_count`

Chunk text must have explicit size limits. Chunk metadata should be sufficient
to reconstruct citations without storing source documents inside workflow state.

### Retrieval Result

Retrieval results should normalize Qdrant payloads into typed DTOs:

- `chunk_id`
- `document_id`
- `chunk_text`
- `score`
- `source_type`
- `document_title`
- `domain`
- `citation`
- bounded `metadata`

The service must avoid exposing raw vector payload internals directly.

### Grounding And Citation Contract

Runtime and frontend citation views should use a stable citation DTO:

- `citation_id`
- `document_id`
- `document_title`
- `source_type`
- `section`
- `page`
- `excerpt`
- `relevance_score`
- `citation_label`

Excerpts must be bounded and should be sanitized before entering workflow state,
workflow events, or frontend responses.

## Persistence Strategy

Default persistence should use existing provider foundations:

- MinIO stores original demo/source objects when object storage adds value.
- Qdrant stores chunk vectors and chunk/source metadata for retrieval.
- Postgres is avoided initially unless a document catalog or ingestion history
  cannot be represented safely by deterministic contracts and provider payloads.

If a future task requires a Postgres document catalog, that task must explicitly
plan and implement:

- model shape
- migration
- repository/service tests
- rollback-safe behavior
- RBAC implications

Planning default: no new database models or migrations until proven necessary.

Workflow state must not store raw documents or unbounded chunks. Runtime may
store bounded evidence summaries and citation DTOs only.

## Embedding Strategy

Embedding concerns should remain separate from chat LLM concerns.

Planned contracts:

- `EmbeddingProvider`
- `EmbeddingRequest`
- `EmbeddingResponse`
- `EmbeddingModelCapabilities`
- `EmbeddingError`

Default behavior:

- deterministic fake/local embeddings for tests and no-key demos
- no external embedding calls in tests
- no real provider key required at settings load time
- embedding dimensions must be explicit and Qdrant-compatible

Optional real embeddings may be planned later only when needed. Ollama local
embeddings may be considered if it fits the no-key local story, but it should
remain behind configuration and mocked tests. Provider SDKs should not be added
unless a later implementation task justifies them.

## Ingestion Strategy

Initial ingestion should target deterministic demo documents from `datasets/`:

- `datasets/contracts/*.md`
- `datasets/policies/*.md`
- `datasets/pricing_rules.json`
- `datasets/products.json`
- `datasets/customers.json` where useful for supplier/customer context
- `datasets/rfqs/rfq_samples.json`
- `datasets/index/document_index.json`

Implementation tasks should add an explicit local/demo ingestion command, for
example:

```text
python -m app.knowledge.ingest_demo --confirm-local-demo
```

Ingestion requirements:

- explicit command only
- no backend startup auto-ingestion
- idempotent reruns
- deterministic document and chunk IDs
- stable content checksums
- bounded chunk size and overlap
- Qdrant collection creation/upsert
- optional MinIO source-object upload
- dry-run/report mode if practical
- safe summary output

The ingestion command should not modify workflow records directly.

## Retrieval Strategy

The retrieval service should be provider-independent:

```text
RetrievalService
  -> EmbeddingProvider
  -> VectorStore
```

Capabilities:

- embed query text with fake/local embeddings by default
- query Qdrant with a bounded top-k value
- apply exact-match filters where supported:
  - `source_type`
  - `domain`
  - `document_id`
  - `version`
  - `effective_date`
- normalize provider payloads into retrieval result DTOs
- return bounded evidence and citations
- avoid leaking raw vector payloads or unbounded chunks

Tests should use fake embeddings and mocked or local-provider Qdrant patterns
consistent with SPEC-004.

## Runtime Integration Strategy

Runtime grounding should be behind an explicit feature flag such as:

```text
RAG_ENABLED=false
```

Default behavior remains deterministic and compatible with the existing board
demo.

When enabled, retrieval evidence can be used in:

- retrieval stage
- compliance stage
- validation/finance stage
- approval package stage

Integration modes:

- If `LLM_RUNTIME_ENABLED=false`, deterministic runtime may attach seeded or
  retrieved evidence summaries and citation DTOs without calling chat providers.
- If `LLM_RUNTIME_ENABLED=true`, prompt builders may receive bounded retrieved
  context through existing SPEC-011 prompt inputs.

Structured outputs should include citations where practical. Runtime must not
store raw documents, raw prompts, raw provider payloads, large chunks, or hidden
reasoning in workflow state/events.

## API Strategy

Knowledge endpoints should be added only when implementation tasks require
them. Planned route namespace:

```text
/api/v1/knowledge
```

Possible endpoints:

- `POST /api/v1/knowledge/ingest-demo`
- `GET /api/v1/knowledge/documents`
- `GET /api/v1/knowledge/documents/{document_id}`
- `POST /api/v1/knowledge/search`

API rules:

- authenticated only
- Admin/Manager for ingestion
- workflow read roles for list/search if safe
- direct Pydantic response models, no global response envelope rollout
- no frontend upload endpoints unless explicitly scoped later
- safe error mapping for missing documents, invalid filters, unavailable
  vector store, and ingestion conflicts

The explicit CLI remains the preferred first ingestion surface. API-triggered
ingestion should be a later task only if needed for demo UX.

## Event And Audit Strategy

- CLI ingestion should print safe summaries.
- API-triggered ingestion, if implemented, should create audit logs.
- Runtime retrieval may append safe WorkflowEvent summaries when useful.
- The existing SPEC-008 workflow stream remains the only streaming mechanism.
- Do not stream raw document chunks over WebSocket by default.
- Event payloads should include document IDs, citation IDs, result counts, and
  bounded summaries only.

## Frontend Strategy

Frontend scope should stay lightweight:

- Add an evidence/citations panel to workflow detail.
- Show citations already present in workflow state or events.
- Show source title, source type, section/page, excerpt, and relevance score.
- Use honest copy such as "retrieved evidence"; do not present it as legal
  advice.
- Add knowledge search UI only if bounded and useful.
- Do not add full document management UI.
- Do not add upload UI unless a later task explicitly scopes it.

Frontend should rely on backend DTOs and existing auth/session/API client
patterns.

## Demo Strategy

SPEC-013 should extend the deterministic demo with local knowledge evidence:

- procurement policy
- contract terms
- supplier/customer evaluation notes
- pricing guideline
- compliance checklist

Demo flow:

1. Start services.
2. Apply migrations.
3. Seed demo users/workflows.
4. Ingest demo knowledge base.
5. Start frontend.
6. Run workflow to `WAITING_APPROVAL`.
7. Show compliance/finance/approval citations.
8. Approve and resume through SPEC-012 flow.

The demo must remain runnable without real LLM keys. Real-provider behavior is
optional experimentation only.

## Testing Strategy

Automated tests must not require live LLM keys, live external embedding
providers, or external network.

Planned tests:

- contract/schema validation
- source-type enum coverage
- chunking size/overlap/hash/idempotency
- deterministic fake embeddings
- Qdrant vector upsert/search with mocked or local provider patterns
- MinIO source-object storage with mocked or local provider patterns
- demo ingestion CLI idempotency and dry-run behavior
- retrieval service top-k/filter normalization
- API tests if endpoints are implemented
- runtime integration with fake retrieval
- frontend evidence panel tests if UI is implemented

Implementation tasks should use the backend/frontend quality gates appropriate
to the files changed.

## Risks And Decisions

- A Postgres document catalog may become necessary for document list/search and
  ingestion history. Default to Qdrant payloads and deterministic contracts
  first; require explicit migration planning before adding tables.
- Embedding providers could drift into chat LLM concerns. Keep embedding
  contracts separate from `LLMService`.
- Qdrant vector dimensions are collection-specific. Store dimensions in
  settings/contracts and validate before upsert/search.
- Runtime state can bloat if chunks are stored directly. Store citations and
  bounded excerpts only.
- Demo documents are small markdown/JSON files. Do not design a large-scale
  ingestion pipeline in this spec.
- Knowledge search can become document management. Keep UI and APIs bounded.

## User Stories

### US-006 - Retrieve Contract And Policy Evidence

As a workflow reviewer, I want the retrieval stage to find relevant contract
and policy evidence so that quotation decisions have citations.

### US-010 - Compliance Evidence Grounding

As a Legal user, I want compliance output to cite policy and contract clauses
so that risks are explainable.

### US-012 - Validate Citation Coverage

As a Manager, I want validation and approval packages to show whether critical
claims have supporting citations.

### Demo Operator - Ingest Knowledge Base

As a demo operator, I want one explicit local command to ingest demo knowledge
documents so that the board demo can show grounded evidence.

## Acceptance Criteria

```gherkin
Given demo knowledge documents exist
When the demo ingestion command runs
Then documents are chunked deterministically
And chunks are upserted into Qdrant with stable metadata
And rerunning ingestion does not create duplicate chunks
```

```gherkin
Given a workflow query references Acme IT equipment
When retrieval runs with RAG enabled
Then bounded policy or contract evidence is returned
And each result includes citation metadata
```

```gherkin
Given RAG is disabled
When the existing deterministic runtime runs
Then current demo behavior remains unchanged
And no external embedding or LLM network call is required
```

```gherkin
Given retrieved evidence is written to workflow state
When the workflow detail page renders
Then citations show source title, source type, section/page, excerpt, and score
And raw documents are not exposed as workflow state
```

## Validation Strategy

Planning-only validation for SPEC-013:

```bash
git status --short
docker-compose config
git diff --check
```

Implementation tasks should use focused gates appropriate to their slice:

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

No validation may require real provider keys or live external network calls.

## Out-of-scope List

- Enterprise document permissions.
- Production OCR.
- Arbitrary frontend upload.
- Large-scale ingestion pipelines.
- Multi-tenant knowledge isolation beyond safe demo/domain metadata.
- Admin document-management UI.
- External SaaS document connectors.
- Live web search.
- Provider SDK additions.
- Provider cost dashboard.
- Production secret vault integration.
- LLM token streaming.
- Agent thought streaming or hidden reasoning exposure.
- Global response envelope rollout.
- Backend/frontend/runtime behavior changes during planning.
- Migrations or database model changes during planning.
