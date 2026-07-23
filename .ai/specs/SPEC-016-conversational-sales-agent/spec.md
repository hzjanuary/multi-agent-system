# SPEC-016 - Conversational Sales Agent and External Price Research

## Status

Draft / post-demo roadmap

## Product Objective

Turn the local Telegram inbound demo into a product-grade Conversational Sales
Agent roadmap for procurement RFQs. The target system should accept natural
customer messages, extract intent safely, normalize requests against an
internal catalog, use internal RAG evidence where available, optionally collect
external reference price evidence with citations, create existing procurement
workflows, and preserve human approval before any final quote.

SPEC-016 is a post-demo development specification. It does not change the
current stable defense path:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

The completed demo proves the channel and safety boundary. Future SPEC-016
tasks should harden that boundary into provider-independent services and
evidence contracts without issuing autonomous quotes.

## Current Completed Capabilities

The following SPEC-016-related capabilities already exist as local-demo work:

- Ollama local provider smoke guide and utility:
  - `docs/llm/OLLAMA_LOCAL_SMOKE.md`
  - `scripts/demo/llm_provider_smoke.py`
- Local Telegram inbound bridge:
  - `scripts/demo/telegram_inbound_bridge.py`
  - `docs/demo/TELEGRAM_INBOUND_DEMO.md`
- Optional Telegram LLM extraction through local Ollama.
- Deterministic English and Vietnamese RFQ parser.
- Deterministic fallback when Ollama is disabled, unavailable, slow, or returns
  invalid output.
- Strict normalization:
  - laptop aliases normalize to `Standard business laptop`
  - Office 365 aliases normalize to `office_365`
  - quantity must be a positive integer
  - unsupported items produce follow-up instead of low-quality workflow data
- Sales-style Telegram replies behind `TELEGRAM_SALES_REPLY_ENABLED`.
- Mixed unsupported item safety guard:
  - supported laptop plus unsupported printer requests do not create partial
    workflows silently
- Workflow creation through existing backend APIs.
- Optional auto-run to `WAITING_APPROVAL`.
- No auto-approval.
- No auto-resume.
- Final live demo runbook:
  - `docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md`

The Violet Operations Console frontend redesign is intentionally tracked
separately under SPEC-017.

## Target Architecture

SPEC-016 should keep channel, extraction, normalization, evidence, workflow,
approval, and response responsibilities separate.

```text
Telegram Sales Agent / inbound channel
  -> LLM extraction layer, optional
  -> deterministic normalization and safety guard
  -> internal catalog / RAG lookup
  -> optional external price research tool
  -> workflow creation and runtime
  -> human approval and explicit resume
  -> sales-style response layer
```

### A. Telegram Sales Agent / Inbound Channel Layer

Responsibilities:

- Poll or receive customer messages from Telegram.
- Handle `/start` and `/help`.
- Reject non-text or empty messages with helpful examples.
- Enforce optional chat allowlist.
- Keep Telegram token local and out of logs.
- Never store Telegram bot tokens, backend access tokens, or passwords.
- Delegate extraction and workflow creation through bounded interfaces.

Initial implementation may remain a local script. A production channel adapter
is a later design decision and must include webhook hosting, authentication,
retry, rate-limit, and audit planning before implementation.

### B. LLM Extraction Layer

Responsibilities:

- Optionally extract RFQ intent from natural English or Vietnamese text.
- Use a strict JSON schema for:
  - language
  - intent
  - items
  - requested add-ons
  - follow-up need
  - follow-up question
- Return structured data only.
- Reject invalid JSON or invalid shape safely.
- Avoid raw prompt, raw provider payload, raw model output, chain-of-thought,
  token, or secret persistence.

Ollama extraction remains opt-in. Provider-independent extraction may be
formalized later, but deterministic fallback must remain available.

### C. Deterministic Normalization And Safety Guard

Responsibilities:

- Canonicalize item aliases.
- Canonicalize add-ons.
- Validate quantity.
- Detect unsupported items from original customer text.
- Block mixed supported and unsupported item requests by default.
- Prevent silent partial workflow creation.
- Attach bounded extraction metadata only.

The original message remains the source of truth for unsupported item scanning,
even when an LLM returns only supported items.

### D. Internal Catalog / RAG Lookup

Responsibilities:

- Check supported catalog items and add-ons.
- Use internal RAG evidence when `RAG_ENABLED=true` and knowledge ingestion has
  run.
- Return bounded citations or an honest empty evidence state.
- Avoid raw documents, embeddings, vector payloads, provider payloads, prompts,
  and secrets.
- Keep catalog/RAG evidence separate from final quote approval.

The current catalog is demo-scale and laptop-focused. Expanding catalog coverage
requires explicit product data, tests, and safety copy.

### E. Optional External Price Research Tool

Responsibilities:

- Collect reference prices only when explicitly enabled.
- Use provider-independent contracts.
- Attach source citations and warnings.
- Label outputs as reference prices, not final quotes.
- Never fabricate price, stock, discount, or delivery information.
- Respect provider terms and robots/policy constraints.
- Fail closed with warnings when evidence is missing or low confidence.

External price research must not become unsupervised web scraping. Provider
choice, rate limiting, caching, citation quality, and audit behavior must be
planned before live external access is enabled.

### F. Workflow Creation / Runtime

Responsibilities:

- Use existing workflow create and run APIs.
- Preserve current workflow contracts.
- Create procurement workflows only after normalization passes.
- `/run` must stop at `WAITING_APPROVAL`.
- Backend deterministic runtime remains stable when
  `LLM_RUNTIME_ENABLED=false`.
- Workflow state may include bounded request metadata and evidence references,
  not raw provider payloads.

### G. Human Approval / Resume

Responsibilities:

- Keep Manager/Admin approval as the final decision boundary.
- Prevent autonomous final quote issuance.
- Preserve explicit `/resume` after approval.
- Never auto-approve or auto-resume from the sales channel.
- Keep rejected workflows terminal.

### H. Sales-Style Response Layer

Responsibilities:

- Reply in customer-friendly wording when enabled.
- Confirm parsed need and supported add-ons.
- Explain that the request entered internal quotation processing.
- Include workflow and Agent Monitor links for the operator/demo path.
- State that manager approval is required before final quotation.
- Avoid final price, stock, delivery date, discount amount, email-sent, or
  approval claims before the workflow has been approved.

## External Price Research Tool Contract

Future implementation should start with a provider-independent contract.

### Input

```json
{
  "item_name": "customer supplied item label",
  "normalized_item_name": "Standard business laptop",
  "quantity": 20,
  "region": "VN",
  "currency": "VND",
  "customer_context": {
    "customer_name": "bounded optional name",
    "contract_hint": "bounded optional context"
  },
  "requested_addons": ["office_365"]
}
```

Rules:

- `quantity` must be a positive integer.
- `normalized_item_name` must come from the supported catalog or a future
  explicitly configured item mapping.
- `customer_context` must be bounded and must not include secrets, tokens, raw
  documents, or unbounded chat history.

### Output

```json
{
  "reference_prices": [],
  "sources": [],
  "confidence": "low | medium | high",
  "retrieved_at": "ISO-8601 timestamp",
  "warnings": [],
  "provider": "fake | manual | web_provider_name"
}
```

Each source must include:

```json
{
  "title": "source title",
  "url": "https://example.com/source",
  "snippet": "bounded snippet or summary",
  "observed_price": "bounded price text or numeric structure when available",
  "currency": "VND",
  "retrieved_at": "ISO-8601 timestamp"
}
```

Rules:

- Output must be labeled `reference price`, never `final quote`.
- Sources must be cited.
- Missing price should produce a warning, not invented data.
- Provider payloads must be normalized and bounded before storage.
- Raw HTML, raw provider responses, full page text, prompts, chain-of-thought,
  embeddings, and vector payloads must not enter workflow state or Telegram
  replies.

## Data Flow

1. Customer sends Telegram RFQ.
2. Channel layer receives text and ignores unsupported commands/non-text.
3. Greeting detection returns help with no workflow creation.
4. Optional LLM extraction attempts strict JSON extraction.
5. Deterministic parser/fallback handles known supported messages.
6. Normalizer canonicalizes item, quantity, add-ons, and language.
7. Unsupported item scanner checks original customer text.
8. If quantity/item missing or unsupported, response layer asks follow-up.
9. If request is supported, internal catalog/RAG lookup may attach evidence.
10. Optional price research may collect reference prices when enabled.
11. Backend workflow is created through existing API.
12. Optional auto-run calls existing `/run`.
13. Workflow stops at `WAITING_APPROVAL`.
14. Operator observes workflow in Agent Monitor.
15. Manager/Admin approves through existing UI.
16. Operator resumes explicitly.
17. Sales response may reference workflow status and evidence safely, but must
    not claim final quote before approval.

## Feature Flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `TELEGRAM_LLM_EXTRACTION_ENABLED` | `false` | Enables optional local LLM extraction in the Telegram bridge. |
| `TELEGRAM_SALES_REPLY_ENABLED` | `false` | Enables customer-friendly sales reply templates. |
| `PRICE_RESEARCH_ENABLED` | `false` | Enables future reference price research. Must remain off until provider contracts and tests exist. |
| `PRICE_RESEARCH_PROVIDER` | `fake` or empty | Future provider selector: `fake`, `manual`, or explicit web provider name. |
| `PRICE_RESEARCH_TIMEOUT_SECONDS` | bounded short timeout | Future timeout for reference price provider calls. |
| `RAG_ENABLED` | `false` | Enables existing runtime RAG grounding after explicit knowledge ingestion. |
| `LLM_RUNTIME_ENABLED` | `false` | Existing backend runtime flag. It stays separate from Telegram extraction and should remain false for stable workflow demos. |

## User Stories

### Customer Sends Vietnamese RFQ Through Telegram

As a customer actor, I want to send a natural Vietnamese procurement request so
the local sales agent can create an internal workflow without requiring an
English prepared sentence.

### Sales Agent Asks Follow-Up When Quantity Or Item Is Missing

As a customer, I want a helpful prompt when my message lacks quantity or item so
I can resend a valid RFQ.

### Sales Agent Refuses Partial Workflow For Mixed Unsupported Items

As an operator, I want the sales agent to block requests that mix supported and
unsupported items so the system never silently drops part of a customer request.

### Sales Agent Creates Workflow For Supported Catalog Item

As a sales operator, I want supported laptop RFQs to create procurement
workflows with safe metadata so the internal process starts from normalized
data.

### Operator Observes Workflow In Agent Monitor

As a demo operator, I want to open Agent Monitor for the created workflow so I
can see deterministic stages, events, and approval boundary evidence.

### Manager Approves And Resumes Workflow

As a Manager, I want to approve and then explicitly resume the workflow so
human governance remains the final quote boundary.

### System Uses Internal Catalog/RAG Evidence When Available

As a reviewer, I want internal policy, contract, catalog, and pricing evidence
to appear as bounded citations when RAG is enabled and knowledge has been
ingested.

### System Optionally Collects External Reference Prices With Citations

As a sales analyst, I want the system to collect external reference price
evidence when internal catalog data is missing so the manager can review cited
market context before approval.

### System Never Issues Final Quote Before Approval

As a governance owner, I want all customer-facing replies before approval to
state that no final quote has been issued.

## Acceptance Criteria

- Deterministic fallback works without Ollama.
- Ollama extraction is opt-in.
- Telegram extraction failure does not surface internal LLM errors to the
  customer.
- No raw LLM prompt is stored.
- No raw provider payload is stored.
- No raw model response is stored.
- No chain-of-thought is exposed.
- No unsupported item is silently dropped.
- Mixed supported/unsupported requests do not create partial workflows by
  default.
- No fake price is generated.
- No stock availability is claimed without cited evidence and approval.
- No delivery promise is made.
- No final quote is issued before Manager/Admin approval.
- No auto-approval occurs.
- No auto-resume occurs.
- No real email is sent unless explicitly configured in a future spec.
- Price research output, when implemented, is labeled as `reference price`.
- Price research sources include title, URL, bounded snippet/summary,
  observed price when available, currency, and retrieval timestamp.
- External provider failure produces safe warnings and does not block the
  deterministic no-key workflow path unless a later task explicitly requires
  it.

## Safety Boundaries

- Telegram tokens, provider keys, backend tokens, passwords, cookies, and local
  override files must not be committed.
- Sales replies must not include stack traces, raw backend errors, provider
  payloads, prompts, raw model output, raw documents, embeddings, vector
  payloads, or chain-of-thought.
- Customer replies must not invent price, discount, stock, delivery, approval,
  or email-sent claims.
- External research must respect provider terms and must not scrape arbitrary
  sites without an approved provider/policy.
- Unsupported catalog items must not be auto-priced.
- Internal RAG and external price evidence support review; they do not replace
  human approval.
- `LLM_RUNTIME_ENABLED` remains separate from Telegram extraction and stays
  false for the stable demo.

## Dependencies

- SPEC-003 authentication and RBAC.
- SPEC-005 workflow state.
- SPEC-006 deterministic LangGraph runtime.
- SPEC-007 workflow APIs.
- SPEC-008 persisted events and WebSocket timeline.
- SPEC-011 LLM provider abstraction and safe runtime flag.
- SPEC-012 human approval and resume.
- SPEC-013 RAG/document knowledge base.
- SPEC-017 Agent Monitor and Violet Operations Console frontend surfaces.
- Local Telegram bridge and tests.
- Optional local Ollama for Telegram extraction experiments.

## Non-goals

- Autonomous final quote issuance.
- Web scraping without provider policy.
- Unsupported catalog auto-pricing.
- Replacing human approval.
- Real email sending.
- Backend LLM runtime enabled by default.
- Cloud deployment automation.
- New Telegram backend routes during planning.
- Database migrations during planning.
- Product catalog expansion during this formalization task.
- RAG/web search or price lookup implementation during this formalization task.
- Provider-management UI.
- Token streaming or agent-thought streaming.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| LLM extraction drops unsupported items | Always scan original customer text with deterministic unsupported-item guard. |
| Price research is mistaken for final quote | Label outputs as reference prices and require Manager/Admin approval before final quote. |
| External provider returns stale or low-quality data | Store `retrieved_at`, confidence, warnings, and cited source metadata. |
| Scraping violates provider/site policy | Use explicit provider adapters only after policy review; no arbitrary scraping by default. |
| Raw provider payload leaks into state or replies | Normalize into bounded schemas and test for prompt/payload/secret markers. |
| Catalog coverage is too narrow | Ask follow-up or reject unsupported items until catalog expansion is explicitly implemented. |
| Real LLM runtime destabilizes demo | Keep `LLM_RUNTIME_ENABLED=false` for stable demos; separate Telegram extraction flag. |
| Customer-facing sales copy overpromises | Template replies with forbidden-claim tests and explicit no-final-quote disclaimer. |

## Validation Strategy

Planning-only validation for this formalization task:

```bash
git diff --check
git status --short
```

Implementation tasks should run focused backend/script/frontend gates according
to files changed, while keeping automated tests independent of real Telegram,
Ollama, web search, paid providers, and external network.
