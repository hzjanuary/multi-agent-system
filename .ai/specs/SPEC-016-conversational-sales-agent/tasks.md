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

Goal: Integrate internal catalog/RAG evidence with reference price research
results while preserving bounded citation contracts.

Scope:

- Add integration path from internal knowledge retrieval to price research
  evidence when `RAG_ENABLED=true`.
- Attach bounded citation DTOs to workflow state/events where appropriate.
- Keep empty evidence states honest when RAG is disabled or ingestion has not
  run.
- Add tests for RAG-enabled and RAG-disabled behavior.
- Do not expose raw documents, chunks beyond bounds, embeddings, vector
  payloads, raw prompts, or provider payloads.

Acceptance criteria:

- Internal catalog/RAG evidence can support reference price review when
  explicitly enabled.
- Evidence includes source/citation metadata.
- Workflow state remains bounded.
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

Validation:

```bash
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 016.9 - Telegram Sales Reply Uses Reference Evidence Safely

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

Validation:

```bash
python -m unittest scripts.demo.test_telegram_inbound_bridge
python -m py_compile scripts/demo/telegram_inbound_bridge.py
git diff --check
```

### TASK 016.10 - Observability / Agent Monitor Evidence Polish

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
