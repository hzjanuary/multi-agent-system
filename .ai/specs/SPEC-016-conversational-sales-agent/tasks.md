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

Status: Implemented.

Goal: Add one approved web/search provider adapter for external reference price
research behind `PRICE_RESEARCH_ENABLED`.

Implemented foundation (Telegram bridge scope):

- Added a controlled, disabled-by-default web search reference fallback to
  `scripts/demo/telegram_inbound_bridge.py` behind `TELEGRAM_WEB_SEARCH_ENABLED`
  with a stdlib-only Tavily adapter and bounded citation normalization.
- Web search is triggered only after the local catalog lookup misses, uses the
  customer's own item phrase as the query (no hard-coded product keywords), and
  treats results as untrusted reference data that is never echoed into customer
  replies.
- No fake provider is constructed; missing key/config or provider failure
  degrades to a safe follow-up reply without blocking the deterministic path.
- The backend `PRICE_RESEARCH_ENABLED` / `PriceResearchProvider` adapter for the
  async backend price research service remains future work and was not changed.

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

Validation:

```bash
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 016.9 - Telegram Sales Reply Uses Reference Evidence Safely

Status: Implemented.

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

Implemented foundation:

- Added an injectable evidence provider to the Telegram inbound bridge behind
  `PRICE_RESEARCH_ENABLED` (disabled by default).
- Added a provider-independent mapper (`reference_evidence_from_price_research_result`)
  that consumes the shared price research result/evidence contract (attribute or
  dict shaped) into bounded reply evidence.
- Reference amounts are kept only when the result exposes an explicit structured
  numeric amount; prose is never converted into a price.
- Source URLs are bounded and http(s)-only; raw snippets and provider payloads are
  never carried into replies.
- Evidence is wired into sales replies and dry-run output. A disabled flag, an
  absent provider, a provider exception, or a wrong return type degrade to no
  evidence without blocking the deterministic flow.
- Added tests covering mapper bounds/safety, dict-shaped contract, prose-amount
  rejection, disabled/failing/wrong-type provider degradation, env flag, dry-run
  evidence wiring, and http(s)-only URL enforcement.

Acceptance criteria:

- Customer replies never say final quote before approval.
- Customer replies never invent price, discount, stock, or delivery.
- Missing evidence produces a safe pending/review message.
- Sales and technical modes remain separately testable.

Validation:

```bash
python -m unittest scripts.demo.test_telegram_inbound_bridge
python -m py_compile scripts/demo/telegram_inbound_bridge.py
git diff --check
```

### TASK 016.10 - Observability / Agent Monitor Evidence Polish

Status: Implemented.

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

Validation:

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/ci/frontend-gate.sh
git diff --check
```

Implemented:

- The reference evidence panel (`workflow-reference-evidence-panel.tsx`) renders
  only explicit evidence-shaped fields from existing workflow state JSON (root,
  `runtime_context`, or `outputs`); it returns `null` when none exist, so empty
  states stay honest and no evidence is fabricated.
- Reference evidence is shown as review material with an internal-review notice;
  `is_final_quote=true` prices/sources are suppressed, so it is never presented
  as a final quote.
- Rendering is bounded to structured title/URL/price/warning fields; raw HTML is
  stripped, provider payloads/prompts/tokens/embeddings/vector payloads and
  chain-of-thought are never rendered, and arbitrary source snippets from
  workflow state are omitted.
- Source URLs are http(s)-only; file/javascript/data/ftp and other schemes are
  dropped.
- Existing approval/resume controls remain visible in Agent Monitor and workflow
  detail; no workflow actions or approval semantics changed.
- Frontend tests cover missing evidence, valid evidence, structured reference
  rows, non-http(s) URL rejection, snippet non-rendering, bounded rendering,
  review/final-quote wording, redaction of sensitive fields, honest empty
  states, and Agent Monitor approval/resume controls.

### TASK 016.11 - Final Validation And Docs

Status: Implemented.

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
docker compose config
docker compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
git diff --check
git status --short
```

(`docker compose` v2 and `python3` are the repository-equivalent commands on
this machine; the CI gate scripts detect both `docker-compose` and
`docker compose`.)

Implemented closeout:

- Confirmed stable defaults remain no-key and non-research by default:
  - `LLM_PROVIDER=fake`
  - `LLM_RUNTIME_ENABLED=false`
  - `PRICE_RESEARCH_ENABLED=false`
  - `RAG_ENABLED=false` unless explicitly enabled for a RAG demo.
- Confirmed the Telegram local bridge stays deterministic:
  - no live Tavily/web price research call
  - no backend price research provider call
  - no auto-approval
  - no auto-resume
  - no real email
- Confirmed reference evidence rendering is passive:
  - Telegram sales replies render supplied evidence only
  - frontend panels render explicit workflow evidence fields only
  - neither surface fabricates evidence or calls providers.
- Confirmed the optional Tavily adapter is disabled by default, requires
  explicit configuration/injection, and is tested with mocked/injected
  transport only.
- Confirmed reference evidence is always review material, never an approved
  customer quote.
- Ran the full SPEC-016 validation gate list and recorded actual results in
  the handoff.

## SPEC-016 Closeout Checklist

- [x] Final validation commands ran and actual results were recorded in the
  task handoff.
- [x] `PRICE_RESEARCH_ENABLED` defaults to `false`.
- [x] Tavily API key is not required in CI.
- [x] Tavily tests use mocked/injected transports and do not call the network.
- [x] Telegram bridge does not call Tavily or live price research providers.
- [x] Telegram reference evidence rendering is passive and requires explicitly
  supplied evidence.
- [x] Frontend reference evidence panels do not fabricate evidence when workflow
  state has no explicit evidence fields.
- [x] Raw prompts, raw provider payloads, tokens, cookies, passwords, secrets,
  embeddings, vector payloads, and chain-of-thought are not rendered.
- [x] Sales replies and frontend panels avoid stock, delivery, discount,
  approval, final quote, and email-sent claims.
- [x] Manager/Admin approval remains the final quotation boundary.
- [x] Stable no-key demo remains unchanged.

## Deferred After SPEC-016

- Live provider verification for Tavily with a real key in a private local
  environment (`docs/demo/PROVIDER_LIVE_VERIFICATION.md`).
- Catalog expansion beyond the laptop demo item.
- Safe integration of approved reference evidence into workflow state, if a
  future product spec authorizes it.
- Approved customer communication/email integration after workflow completion.
- Provider observability, caching, rate limits, and policy controls for live
  external research.
