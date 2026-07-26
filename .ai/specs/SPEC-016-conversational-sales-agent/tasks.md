# SPEC-016 Tasks - Conversational Sales Agent and External Price Research

## Task List

### TASK 016.4 - Formalize SPEC-016 And Architecture

Goal: Capture the completed local Telegram/Ollama demo work as a product-grade
roadmap for conversational sales, catalog safety, RAG evidence, and future
external reference price research.

Scope:

- Create `.ai/specs/SPEC-016-conversational-sales-agent/spec.md`.
- Create `.ai/specs/SPEC-016-conversational-sales-agent/tasks.md`.
- Document current completed capabilities.
- Define target architecture, feature flags, user stories, acceptance criteria,
  safety boundaries, data flow, dependencies, risks, and non-goals.
- Add short cross-links from demo docs and README if useful.
- Do not implement price research, web search, backend behavior, frontend
  behavior, Telegram behavior, migrations, Docker, or CI changes.

Acceptance criteria:

- SPEC-016 spec exists and separates channel, LLM extraction, deterministic
  normalization, catalog/RAG, price research, workflow, approval/resume, and
  sales reply responsibilities.
- External price research tool contract is defined as future work.
- Safety boundaries forbid autonomous final quotes, fake prices, stock/delivery
  promises, auto-approval, auto-resume, and raw provider/prompt exposure.
- Docs do not claim implemented price lookup or real web search.

Validation:

```bash
git diff --check
git status --short
```

### TASK 016.5 - External Price Research Tool Interface And Schemas

Status: Implemented.

Goal: Add provider-independent backend contracts for reference price research
without calling real web providers.

Scope:

- Add typed request/response schemas for price research.
- Include item name, normalized item name, quantity, region, currency, customer
  context, and requested add-ons.
- Include reference prices, sources, confidence, retrieved timestamp, warnings,
  and provider in the output.
- Add source DTOs with title, URL, bounded summary/snippet, observed price,
  currency, and retrieved timestamp.
- Add validation tests for bounds, required fields, and no-secret/no-raw-payload
  behavior.
- Do not connect to external web search or pricing providers yet.

Implemented foundation:

- Added backend `app.price_research` package with safe request/result/source
  schemas, async provider protocol, typed exceptions, and disabled-by-default
  service shell.
- Added safe price research settings with disabled default and no required API
  keys.
- Added focused backend tests for schema validation, source index validation,
  final quote rejection, provider protocol behavior, disabled service behavior,
  and settings defaults.
- No web provider, workflow runtime integration, Telegram integration, API
  endpoint, database model, or migration was added.

Acceptance criteria:

- Schemas validate positive quantity, bounded strings, allowed confidence
  values, and safe source metadata.
- Output uses `reference price` wording, not final quote.
- Tests prove raw provider payloads, prompts, tokens, and secrets are not part
  of the public schema.

Validation:

```bash
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 016.6 - Fake/Manual Price Research Provider And Tests

Status: Implemented.

Goal: Add a deterministic fake/manual provider for reference price evidence so
the workflow can be tested without web access.

Scope:

- Add provider interface and fake/manual implementation.
- Return bounded reference price examples only from explicit fixtures or manual
  configuration.
- Add feature flag plumbing with `PRICE_RESEARCH_ENABLED=false` by default.
- Add tests for disabled mode, fake/manual provider output, warnings, timeouts,
  and no fabricated prices when data is missing.
- Do not call external network.

Implemented foundation:

- Added `FakePriceResearchProvider` with deterministic demo reference evidence
  for `Standard business laptop` and safe no-match warnings for unknown items.
- Added `ManualPriceResearchProvider` that returns no prices unless explicit
  constructor data is supplied.
- Added `get_price_research_provider()` for `fake` and `manual` provider
  selection only.
- Updated `PriceResearchService` to remain disabled by default and delegate to
  either an explicit provider object or the supported no-network provider
  factory when enabled.
- Added tests proving no network calls, no final quote flag, no stock/delivery
  claims, safe warnings, factory behavior, and service delegation.
- No real web provider, workflow runtime integration, Telegram integration,
  API endpoint, database model, or migration was added.

Acceptance criteria:

- Automated tests require no external provider.
- Disabled mode returns no research and no error for stable demos.
- Fake/manual output is clearly labeled reference evidence.
- Missing fixture/manual data produces warnings instead of invented price.

Validation:

```bash
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 016.7 - RAG Evidence Integration For Price References

Status: Implemented as backend provider foundation.

Goal: Integrate internal catalog/RAG evidence with reference price research
results while preserving bounded citation contracts.

Scope:

- Add an injected internal knowledge retrieval provider for price research
  evidence.
- Map bounded knowledge citations/results into `PriceResearchSource` entries
  with `source_type="rag"`.
- Create `ReferencePrice` values only from explicit structured price metadata,
  not from prose extraction.
- Keep empty evidence states honest when internal knowledge has no matching
  evidence or no structured price metadata.
- Add tests for RAG evidence, unstructured-only evidence, empty evidence, and
  service/provider dependency boundaries.
- Do not expose raw documents, chunks beyond bounds, embeddings, vector
  payloads, raw prompts, or provider payloads.
- Do not integrate with workflow runtime, Telegram, frontend, API endpoints, web
  search, or database persistence in this task.

Implemented foundation:

- Added `backend/app/price_research/rag_provider.py`.
- Added `RAGPriceResearchProvider` with an injected `KnowledgeSearchRequest ->
  KnowledgeSearchResponse` callable.
- Added safe warnings:
  - `RAG evidence is reference material, not a final quote.`
  - `No structured price metadata found; manual pricing review is required.`
  - `No internal knowledge evidence found for this item.`
- Updated provider exports and the provider factory so `rag` cannot be
  constructed without an injected knowledge dependency.
- Added `backend/app/tests/test_price_research_rag_provider.py`.

Acceptance criteria:

- Internal catalog/RAG evidence can support reference price review when a caller
  explicitly injects the knowledge search dependency and enables the service.
- Evidence includes bounded source/citation metadata.
- Prose-only evidence never fabricates a price.
- `rag` provider selection fails safely without an injected knowledge
  dependency.
- Stable no-key default remains unchanged.

Validation:

```bash
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 016.8 - Optional Web Search Provider Adapter Behind Feature Flag

Status: Implemented as optional Tavily adapter foundation.

Goal: Add one approved web/search provider adapter for external reference price
research behind `PRICE_RESEARCH_ENABLED`.

Scope:

- Select a provider only after policy review.
- Add adapter with timeout, bounded response parsing, source citation mapping,
  warnings, and error categories.
- Mock all provider behavior in tests.
- Do not require real provider keys in CI.
- Do not scrape arbitrary websites without provider policy.

Acceptance criteria:

- Provider is disabled by default.
- Missing key/config fails safely only when the provider is selected and used.
- Adapter output maps to the provider-independent source contract.
- Tests cover timeout, unavailable, malformed response, no price found, and
  safe citation output.

Implemented foundation:

- Added `backend/app/price_research/tavily_provider.py`.
- Added `TavilyPriceResearchProvider` for the official Tavily Search API
  (`POST /search` with bearer authentication), using an injectable transport
  so tests do not perform network calls.
- Added Tavily settings:
  - `TAVILY_API_KEY`
  - `TAVILY_SEARCH_URL`
  - `TAVILY_MAX_RESULTS`
  - `TAVILY_INCLUDE_RAW_CONTENT`
  - `TAVILY_SEARCH_DEPTH`
- Tavily remains disabled by default and cannot be constructed by the generic
  provider factory without explicit provider injection and key configuration.
- External web results are mapped to bounded
  `PriceResearchSource(source_type="external_web")` citation evidence.
- The adapter does not infer prices from snippets/prose and returns no
  `ReferencePrice` unless a future response contains explicit structured price
  metadata.
- Safe warnings label external web evidence as reference material, not a final
  quote, and require manual pricing review when no structured price metadata is
  available.
- Tests cover missing key, sanitized query construction, mocked successful
  responses, source mapping, score normalization, timeout/non-2xx/invalid JSON
  errors, malformed results, max result bounds, no default network call with
  injected transport, and factory/service safe failure without injection.
- No workflow runtime integration, Telegram integration, frontend changes, API
  endpoint, database model, migration, real web search in tests, final quote,
  stock/delivery/discount/approval claim, or provider key was added.

Validation:

```bash
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 016.9 - Telegram Sales Reply Uses Reference Evidence Safely

Status: Implemented as reply-rendering foundation.

Goal: Let Telegram sales replies mention available reference evidence without
issuing a final quote or overclaiming.

Scope:

- Add reply templates for reference evidence summaries.
- Mention reference price ranges only when evidence exists and is explicitly
  labeled as reference.
- Include warnings when evidence is incomplete or low confidence.
- Keep workflow URL, Agent Monitor URL, status, and human approval note.
- Preserve technical reply mode.
- Add tests for forbidden claims and no raw payload leakage.

Acceptance criteria:

- Customer replies never say final quote before approval.
- Customer replies never invent price, discount, stock, or delivery.
- Missing evidence produces a safe pending/review message.
- Sales and technical modes remain separately testable.

Implemented foundation:

- Added local Telegram bridge summary dataclasses for explicitly supplied
  reference evidence:
  - `ReferenceEvidenceSummary`
  - `ReferenceEvidenceSourceSummary`
  - `ReferenceEvidencePriceSummary`
- Sales-style replies can render bounded provider/source/confidence/reference
  amount summaries only when an evidence object is passed to the renderer.
- Evidence rendering is passive: the Telegram bridge does not call Tavily,
  backend price research services, RAG providers, or any external network path
  for evidence.
- Empty, absent, low-confidence, warning-only, or `is_final_quote=true`
  evidence is downgraded to manual/internal-review wording.
- Technical reply mode remains compatible and ignores evidence summaries.
- Added unit tests covering absent evidence, explicit reference prices, bounded
  citations, low confidence, final-quote downgrade, redaction, forbidden claims,
  technical mode compatibility, and no network calls.
- No workflow runtime integration, backend API change, frontend change,
  database model/migration, provider call, final quote, stock/delivery/discount
  claim, auto-approval, auto-resume, or real email behavior was added.

Validation:

```bash
python -m unittest scripts.demo.test_telegram_inbound_bridge
python -m py_compile scripts/demo/telegram_inbound_bridge.py
git diff --check
```

### TASK 016.10 - Observability / Agent Monitor Evidence Polish

Status: Implemented as frontend display foundation.

Goal: Surface reference price and RAG evidence in Agent Monitor/workflow UI only
when real backend evidence exists.

Scope:

- Add frontend evidence display polish for price reference citations if the
  backend exposes them.
- Keep empty states honest.
- Add tests that sensitive fields are not rendered.
- Do not fabricate evidence or metrics.
- Do not change workflow actions or approval semantics.

Acceptance criteria:

- Reference evidence is displayed as review evidence, not final quote.
- UI hides raw provider payloads, prompts, tokens, embeddings, vector payloads,
  and chain-of-thought.
- Existing approval/resume controls remain visible.

Implemented foundation:

- Added `frontend/components/workflows/workflow-reference-evidence-panel.tsx`.
- Added `extractReferenceEvidence()` to scan only explicit evidence-shaped
  workflow fields such as `reference_price_research`, `price_research`,
  `reference_evidence`, nested `evidence.price_research`, and `rag_evidence`
  under the workflow root, `runtime_context`, or `outputs`.
- Mounted the panel in selected Agent Monitor workflow view and workflow detail.
- The panel returns `null` when no explicit evidence field exists, so no fake
  evidence cards are rendered.
- Evidence output is bounded to structured source/reference price/warning
  fields, caps source/price/warning counts, strips raw HTML, redacts sensitive
  markers, and suppresses upstream `is_final_quote=true` prices/sources behind
  internal-review wording.
- Existing RAG citation panel remains intact for workflow citations and
  grounding events.
- Added frontend tests for missing evidence, valid evidence, structured
  reference amounts, source/warning bounds, sensitive redaction, final-quote
  downgrade, forbidden positive claims, Agent Monitor selected workflow, and
  workflow detail rendering.
- No provider calls, API changes, workflow runtime changes, Telegram changes,
  database models/migrations, Docker/Compose/CI behavior, fake evidence, final
  quote behavior, stock/delivery/discount/approval claim, or real email
  behavior was added.

Validation:

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/ci/frontend-gate.sh
git diff --check
```

### TASK 016.11 - Final Validation And Docs

Goal: Validate SPEC-016 implementation, update runbooks, and document the safe
post-demo conversational sales workflow.

Scope:

- Update Telegram inbound docs, frontend operator guide, and README links.
- Add final SPEC-016 validation checklist.
- Run backend/script/frontend gates appropriate to implemented files.
- Confirm no real provider keys, Telegram tokens, raw provider payloads, fake
  evidence, fake prices, auto-approval, auto-resume, or real email behavior.

Acceptance criteria:

- SPEC-016 is ready for review or closure.
- Default deterministic demo remains stable without Ollama or web access.
- Optional Ollama extraction and optional price research remain feature-flagged.
- Docs honestly distinguish reference price evidence from final approved quote.

Validation:

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
python -m unittest scripts.demo.test_telegram_inbound_bridge
git diff --check
```
