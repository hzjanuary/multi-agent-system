# SPEC-018 - Catalog Expansion

## Status

Planned / ready for review before implementation

## Product Objective

Expand the procurement demo catalog beyond laptop and Office 365 requests using
explicit deterministic product data, safe alias normalization, add-on
compatibility rules, and strict unsupported-item protection.

SPEC-018 turns the current laptop-only Telegram/workflow intake boundary into a
small governed catalog foundation. It must preserve the SPEC-016 safety model:
catalog support allows workflow creation and review, not autonomous final
quotation.

## Current Dependencies

- SPEC-003 authentication and RBAC.
- SPEC-005 workflow state.
- SPEC-007 workflow create/run APIs.
- SPEC-010 deterministic demo seed conventions.
- SPEC-012 Manager/Admin approval and explicit resume.
- SPEC-013 RAG/document knowledge base.
- SPEC-016 conversational sales, deterministic parser, mixed unsupported item
  guard, and reference evidence foundations.
- SPEC-017 Violet Operations Console surfaces, including Demo Command, Agent
  Monitor, workflow detail, and reference evidence panels.

## Target Catalog Scope

Initial supported item families:

- Standard business laptop
- Business desktop PC
- Office monitor
- Office printer
- Wireless keyboard and mouse combo
- Microsoft 365 / Office 365 add-on

This scope is intentionally small. Each supported item must be represented by
explicit deterministic catalog data, aliases, metadata, and tests before
Telegram or workflow creation treats it as supported.

## Target Architecture

```text
Customer request
  -> channel/parser alias detection
  -> deterministic catalog normalizer
  -> item family / SKU candidate
  -> add-on compatibility check
  -> mixed supported/unsupported guard
  -> workflow create payload with catalog metadata
  -> deterministic runtime / reference evidence review
  -> Manager/Admin approval boundary
```

### Catalog Data Contract

The catalog should start as deterministic versioned data, not live external
lookup. A catalog item should define:

- canonical item family name
- stable SKU or demo catalog code
- supported aliases by language
- item category/domain
- default unit
- optional display description
- compatibility with add-ons
- safety notes and unsupported-adjacent terms
- version metadata such as `CATALOG_VERSION`

The catalog must not contain real customer data, real supplier credentials, or
unverified external prices.

### Item Family And SKU Model

The first implementation should separate family-level matching from SKU-level
metadata:

- Family: `Office printer`
- SKU/code: deterministic demo identifier such as `office_printer_standard`
- Display name: evaluator-facing name
- Domain: procurement domain such as `it_equipment` or `office_equipment`

The model can remain in code fixtures or configuration at first. Database
models are not required unless a future task explicitly scopes persistence.

### Alias / Normalization Rules

Alias normalization must be deterministic and testable. It should support
English and Vietnamese aliases where planned:

- laptop, laptops, notebook, `may tinh xach tay`, `máy tính xách tay`
- desktop, desktop PC, `may tinh de ban`, `máy tính để bàn`
- monitor, display, `man hinh`, `màn hình`
- printer, `may in`, `máy in`
- keyboard mouse combo, `bo phim chuot`, `bộ phím chuột`

The original customer text remains the source of truth for unsupported item
scanning. LLM extraction may propose items, but deterministic normalization
must accept or reject them.

### Add-On Compatibility Rules

Microsoft 365 / Office 365 must be modeled as an add-on, not silently folded
into item names. The catalog must define which item families can accept the
add-on.

If an add-on is incompatible or ambiguous, workflow creation should ask for
clarification rather than creating a misleading request.

### Unsupported Item Handling

Unsupported items must produce a follow-up or clear rejection. The system must
not create a workflow that pretends unsupported items are supported.

### Mixed Supported / Unsupported Item Handling

Mixed requests must not silently drop unsupported lines. For example, a request
for laptops plus an unsupported service must not become a laptop-only workflow
unless the customer explicitly sends a laptop-only follow-up.

### Telegram Parser Integration Boundary

SPEC-018 may expand deterministic Telegram parser aliases and payload
construction. It must not make Telegram call RAG, Tavily, live price research,
or outbound communication providers.

### Workflow Payload / Catalog Metadata Boundary

Workflow payloads may include bounded catalog metadata such as:

- catalog version
- normalized item family
- catalog SKU/code
- supported add-ons
- unsupported item warnings when no workflow is created

Workflow state must not include raw LLM prompts, raw provider payloads, secrets,
or fabricated prices.

### RAG / Price Research Compatibility

Catalog metadata should be compatible with SPEC-016 price research requests and
RAG evidence lookups. Reference evidence remains review material only.

The catalog may provide query inputs such as normalized item family, region,
currency, and requested add-ons. It must not trigger live web calls by default.

### Frontend Display Considerations

Frontend surfaces may need small display updates for:

- normalized item family
- catalog SKU/code
- add-on compatibility
- unsupported item guidance
- read-only catalog hints in Demo Command or workflow detail

Frontend changes must not fabricate catalog records or prices.

## User Stories

### Customer Requests A Supported Desktop PC

As a customer actor, I want to request desktop PCs in English or Vietnamese so
the system can create a normalized procurement workflow when the item is in the
demo catalog.

### Customer Requests A Printer

As a customer actor, I want an office printer request to be recognized as a
supported catalog item once printer data and aliases are explicitly added.

### Customer Mixes Supported And Unsupported Items

As a governance owner, I want mixed requests to be blocked unless all requested
items are supported, so the system never silently drops part of a customer RFQ.

### Operator Reviews Catalog Metadata

As a sales operator, I want workflow detail and Agent Monitor evidence to show
the normalized catalog item and add-ons so I can explain why the workflow was
created.

### Manager Approves Only After Review

As a Manager, I want catalog expansion to preserve the existing approval
boundary so expanded item support does not create autonomous final quotes.

## Acceptance Criteria

- Catalog data is explicit, deterministic, versioned, and covered by tests.
- The supported item families listed in this spec have canonical names and
  alias rules before they are accepted by parser/workflow intake.
- Office 365 / Microsoft 365 remains an add-on with compatibility rules.
- Unsupported items produce follow-up/rejection and do not create low-quality
  workflows.
- Mixed supported/unsupported requests are blocked by default.
- Workflow payloads include bounded catalog metadata only when it is explicit.
- No unsupported item auto-pricing is introduced.
- No final quote, stock, delivery, discount, approval, or email-sent claim is
  introduced.
- No live web lookup, provider key, or external provider call is required.
- Existing laptop-only behavior remains stable.

## Safety Boundaries

- No unsupported item auto-pricing.
- No silent item dropping.
- No final quote.
- No stock or delivery claims.
- No fake external prices.
- No web lookup required.
- No provider keys.
- No real customer data.
- No raw prompts, provider payloads, embeddings, vector payloads, secrets,
  tokens, or chain-of-thought.
- Manager/Admin approval remains the final quotation boundary.

## Feature Flags And Configuration

Prefer explicit deterministic catalog versioning over runtime feature flags.

Candidate configuration:

- `CATALOG_VERSION`, for example `demo-catalog-v1`
- `CATALOG_EXPANSION_ENABLED`, only if implementation needs a safe rollout
  switch. Default must preserve the existing stable demo unless a task
  explicitly migrates the demo to the expanded catalog.

## Non-Goals

- Real supplier catalog integration.
- ERP integration.
- Live price lookup.
- Web scraping.
- Tavily or other provider calls.
- Autonomous final quotation.
- Stock or delivery promise.
- Catalog admin UI.
- Database persistence unless a later task explicitly scopes it.
- Replacing Manager/Admin approval.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Alias expansion accepts the wrong item | Use deterministic alias tables, language-specific tests, and unsupported-adjacent term tests. |
| Mixed-item requests create partial workflows | Keep original-text unsupported scanning as a required guard. |
| Catalog support is mistaken for pricing support | Separate item support from price evidence and keep no-final-quote copy. |
| Add-ons are applied to incompatible items | Add explicit compatibility matrix and tests. |
| Frontend overstates catalog confidence | Render catalog metadata as normalized intake evidence, not pricing approval. |

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
```

Implementation tasks should add focused parser/catalog tests, then run:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/ci/all-gates.sh
git diff --check
```

## Suggested Task Order

1. TASK 018.1 - Catalog Data Model / Contract Planning
2. TASK 018.2 - Deterministic Catalog Fixture And Tests
3. TASK 018.3 - Parser Alias Expansion For Supported Catalog Items
4. TASK 018.4 - Mixed-Item Safety Hardening
5. TASK 018.5 - Workflow Payload Catalog Metadata
6. TASK 018.6 - Frontend Catalog Display Polish If Needed
7. TASK 018.7 - Final Validation And Docs
