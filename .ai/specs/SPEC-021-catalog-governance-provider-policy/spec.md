# SPEC-021 - Catalog Governance and Provider Policy

## Status

Planning / Draft

## Product Objective

Define the policy layer that governs future catalog expansion, provider
evidence usage, trust levels, manual review requirements, approval boundaries,
and outbound communication safety.

SPEC-021 is a planning specification only. It does not implement catalog
persistence, live provider calls, workflow integration, Telegram integration,
frontend behavior, API endpoints, database migrations, Docker/CI behavior, or
email sending.

The stable demo defaults remain unchanged:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
```

## Background

SPEC-018, SPEC-019, and SPEC-020 are approved and closed:

- SPEC-018 added a deterministic demo catalog, parser alias expansion, mixed
  supported/unsupported item protection, bounded catalog metadata, and safe
  frontend catalog display.
- SPEC-019 added manual-only Tavily live smoke verification with explicit
  confirmation, no-key CI, redaction, and no workflow/Telegram side effects.
- SPEC-020 added preview-only approved outbound communication foundations and
  a read-only preview endpoint/panel, with no send behavior.

SPEC-021 turns those foundations into a governed future roadmap. Its purpose is
to define what must be true before the system expands catalog support, consumes
provider evidence in product flows, or introduces approved outbound send
integrations.

## Governance Principles

1. Catalog support is explicit, versioned, tested, and reviewable.
2. Unsupported items are never silently dropped or priced.
3. Provider evidence is reference material, not a final quotation.
4. Evidence trust level determines whether automated use is allowed or manual
   review is required.
5. Manager/Admin approval and explicit resume remain the final decision
   boundary.
6. Outbound preview and outbound send remain separate operations.
7. Real provider keys, Telegram tokens, SMTP/Gmail credentials, raw provider
   payloads, raw prompts, embeddings, vector payloads, cookies, and secrets must
   never be committed or displayed.
8. Stable defense/demo behavior remains deterministic and no-key by default.

## Scope

SPEC-021 should define future policy and validation requirements for:

- catalog versioning policy;
- supported vs unsupported item governance;
- alias review policy;
- add-on compatibility policy;
- provider evidence trust levels;
- fake/manual/RAG/Tavily evidence policy;
- reference evidence vs final quotation boundary;
- approval/resume boundary;
- outbound preview/send boundary;
- audit requirements;
- future live provider integration policy;
- future real email/send policy;
- safety boundaries and non-goals;
- user stories and acceptance criteria;
- implementation task sequence.

## Non-Goals

- No backend behavior changes in this planning spec.
- No frontend behavior changes.
- No Telegram bridge behavior changes.
- No API endpoint changes.
- No database models or migrations.
- No Docker/Compose/CI changes.
- No provider calls or live web calls.
- No real email sending.
- No price lookup implementation.
- No automatic catalog expansion from provider data.
- No autonomous final quote.
- No auto-approval or auto-resume.
- No fake evidence, fake external prices, stock promises, delivery promises, or
  discount approvals.

## Target Policy Architecture

```text
Catalog governance policy
  -> versioned catalog contract
  -> supported item / alias / add-on review
  -> parser and workflow intake eligibility
  -> evidence policy
      -> fake/manual/RAG/Tavily trust levels
      -> reference-only labels and warnings
      -> manual review thresholds
  -> workflow approval policy
      -> WAITING_APPROVAL boundary
      -> Manager/Admin decision
      -> explicit /resume
  -> outbound communication policy
      -> approved preview
      -> future send gate
      -> audit requirements
```

The policy layer should remain provider-independent. Future implementation may
be represented as documentation, typed schemas, fixtures, service guards,
admin-only configuration, or a persisted policy model, but persistence is not
required until a later implementation task scopes it.

## Catalog Versioning Policy

Every supported catalog revision must have a stable version identifier such as
`CATALOG_VERSION`. A version change is required when:

- a new item family is added;
- an alias changes matching behavior;
- an add-on compatibility rule changes;
- a product family is removed or deprecated;
- metadata semantics change.

Catalog version records should document:

- version id;
- effective date;
- changed item families;
- changed aliases;
- changed add-on compatibility;
- reviewer/approver role;
- migration or compatibility notes;
- validation commands.

Versioning must not imply pricing, stock, delivery, discount, or final quote
approval.

## Supported vs Unsupported Item Governance

An item is supported only when all of the following are true:

- canonical item family is defined;
- stable item id or SKU-like demo code exists;
- at least one tested alias exists;
- quantity unit is defined;
- domain is defined;
- add-on compatibility is defined;
- safety copy and unsupported-adjacent terms are reviewed;
- tests cover successful parsing and unsupported/mixed behavior.

Unsupported item handling must fail closed:

- no partial workflow creation by default;
- no low-quality generic workflow for unknown items;
- no fabricated catalog metadata;
- no price lookup for unsupported items;
- clear technical and sales-friendly follow-up wording.

Mixed supported/unsupported requests must ask for clarification unless all
items are supported by the active catalog version.

## Alias Review Policy

Aliases are externally observable because they decide whether a customer
message creates a workflow. New aliases require review for:

- language and spelling variants;
- false-positive risk;
- overlap with unsupported items;
- plural/singular forms;
- Vietnamese accents and unaccented forms;
- brand terms that could imply unsupported SKU specificity;
- add-on terms that must not be folded into item names.

LLM extraction output must still pass deterministic alias normalization.
Original customer text remains the source of truth for unsupported item safety
scanning.

## Add-On Compatibility Policy

Add-ons must be represented separately from item names. A supported add-on must
define:

- canonical add-on id;
- display name;
- aliases;
- compatible item families;
- incompatible item families;
- behavior when compatibility is ambiguous;
- tests for compatible, incompatible, and missing-item cases.

Office 365 / Microsoft 365 remains an add-on, not a price, final quote,
delivery promise, or discount approval.

## Provider Evidence Trust Levels

Provider evidence must be assigned a trust level before product flows use it.

| Trust level | Evidence source | Allowed use | Required warning |
| --- | --- | --- | --- |
| `demo_fake` | deterministic fake provider | tests/demo only | fake deterministic reference evidence, not final quote |
| `manual_reviewed` | human-entered/manual source | internal review evidence | manually supplied reference evidence, not final quote |
| `internal_rag` | internal knowledge/RAG citations | internal review evidence with citations | internal evidence, verify before approval |
| `external_unverified` | Tavily or future external provider result | manual review only | external web evidence requires manual pricing review |
| `approved_policy` | future explicitly approved internal pricing policy | may inform draft after policy approval | still requires Manager/Admin approval |

The default for any new provider is `external_unverified` until an explicit
policy review promotes it.

## Evidence Source Policies

### Fake Provider

- Allowed only for deterministic tests and demo reference evidence.
- Must label output as fake/demo reference data.
- Must never be shown as market truth, stock status, delivery status, discount,
  or final quotation.

### Manual Provider

- Represents explicit human-supplied reference evidence.
- Must preserve source, retrieved date, currency, warning, and reviewer notes.
- Does not bypass approval/resume.

### RAG Provider

- Uses internal knowledge results as citations.
- Creates reference prices only from explicit structured metadata.
- Must not infer prices from prose.
- Must not expose raw documents, embeddings, vector payloads, raw prompts, or
  provider payloads.

### Tavily / External Web Provider

- Manual-only or feature-flagged until a later spec integrates it.
- Must use provider APIs, not arbitrary scraping.
- Requires local provider key, explicit confirmation for live smoke, timeout,
  result limits, redaction, and citation quality checks.
- Search snippets are external reference evidence only.
- Must not infer price from prose unless a later structured extraction policy
  explicitly authorizes and tests it.

## Reference Evidence vs Final Quotation Boundary

Reference evidence may support internal review, but it is not a final quote.

Final quotation requires:

- supported catalog item;
- deterministic workflow completion path;
- Manager/Admin approval;
- explicit resume;
- approved communication preview or future approved send flow;
- no unresolved unsupported item or low-confidence evidence blocker.

Before that boundary, user-facing messages must not claim:

- final quote;
- approved quotation;
- stock availability;
- delivery date;
- discount approval;
- real email sent;
- autonomous approval or resume.

## Approval / Resume Boundary

The existing workflow rule remains authoritative:

```text
/run -> WAITING_APPROVAL
Manager/Admin approval -> APPROVED
/resume -> COMPLETED
```

Catalog and provider policy must not alter this lifecycle. A future policy
implementation may add warnings or blockers before approval, but it must not
auto-approve, auto-resume, or send customer-facing final communication.

## Outbound Preview / Send Boundary

SPEC-020 preview-only behavior remains the baseline:

- `OUTBOUND_COMMUNICATION_ENABLED=false`
- `OUTBOUND_SEND_ENABLED=false`
- preview requires completed workflow evidence and explicit preview content;
- no send endpoint exists in the current implementation;
- no Gmail/SMTP/provider send integration exists.

Future send behavior must require a separate spec covering:

- RBAC;
- send confirmation UX/API;
- persisted audit events;
- outbox or provider strategy;
- retry/failure handling;
- credential storage and redaction;
- customer communication policy;
- test and smoke strategy.

## Audit Requirements

Future policy implementation should define bounded audit/event records for:

- catalog version created/changed/deprecated;
- alias added/removed;
- add-on compatibility changed;
- unsupported item blocked;
- provider evidence collected;
- provider evidence rejected or downgraded;
- manual review completed;
- outbound preview exported/viewed if implemented as a mutation;
- future send requested/succeeded/failed.

Audit payloads must not contain secrets, raw provider payloads, raw prompts,
raw documents, embeddings, vector payloads, cookies, tokens, or passwords.

## Feature Flags And Defaults

Planning should preserve these stable defaults:

| Flag | Default | Policy |
| --- | --- | --- |
| `LLM_PROVIDER` | `fake` | Stable backend runtime stays deterministic by default. |
| `LLM_RUNTIME_ENABLED` | `false` | Real backend LLM runtime requires explicit enablement. |
| `RAG_ENABLED` | `false` | RAG evidence requires explicit ingestion and enablement. |
| `PRICE_RESEARCH_ENABLED` | `false` | Reference price research is opt-in only. |
| `PRICE_RESEARCH_PROVIDER` | `fake` | Provider output is reference evidence only. |
| `TELEGRAM_LLM_EXTRACTION_ENABLED` | `false` | Telegram LLM extraction is optional and local-demo scoped. |
| `TELEGRAM_SALES_REPLY_ENABLED` | `false` | Sales reply tone is opt-in. |
| `OUTBOUND_COMMUNICATION_ENABLED` | `false` | Approved preview endpoint remains disabled by default. |
| `OUTBOUND_SEND_ENABLED` | `false` | Real sending is unavailable by default. |

## User Stories

### Governance Owner Reviews Catalog Change

As a governance owner, I want every new catalog item, alias, and add-on rule to
be reviewed and versioned so customer requests do not create unsupported or
misleading workflows.

### Sales Operator Handles Unsupported Item

As a sales operator, I want unsupported or mixed supported/unsupported requests
to produce a clear follow-up so the system never silently drops customer
requirements.

### Manager Reviews Provider Evidence Trust

As a Manager, I want evidence trust levels and warnings visible before approval
so external or low-confidence evidence cannot be mistaken for approved pricing.

### Developer Adds New Provider Safely

As a developer, I want a provider policy checklist before live integration so
new providers do not add CI key requirements, raw payload leakage, or automatic
workflow effects.

### Admin Plans Future Send Integration

As an Admin, I want real email/send behavior to require a separate approved
policy and audit design so preview-only behavior cannot accidentally become
production sending.

## Acceptance Criteria

- SPEC-021 defines catalog versioning policy.
- SPEC-021 defines supported vs unsupported item governance.
- SPEC-021 defines alias review policy.
- SPEC-021 defines add-on compatibility policy.
- SPEC-021 defines provider evidence trust levels.
- SPEC-021 defines fake/manual/RAG/Tavily evidence policies.
- SPEC-021 preserves reference evidence vs final quotation boundary.
- SPEC-021 preserves Manager/Admin approval and explicit resume boundaries.
- SPEC-021 preserves outbound preview vs send separation.
- SPEC-021 defines future audit requirements.
- SPEC-021 defines future live provider integration policy.
- SPEC-021 defines future real email/send policy.
- SPEC-021 includes safety boundaries, non-goals, user stories, and task
  sequence.
- Planning does not implement backend, frontend, Telegram, API, database,
  Docker/CI, provider, or send behavior.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Catalog expansion creates false positives | Require reviewed aliases, unsupported-adjacent tests, and versioned changes. |
| Unsupported items are silently dropped | Keep original-text unsupported scanning and mixed-item blocking. |
| Provider snippets are mistaken for prices | Use trust levels, reference-only labels, and manual-review warnings. |
| Tavily/live providers leak secrets or raw payloads | Keep live calls manual/flagged, redact output, and forbid raw payload storage. |
| RAG prose is treated as structured price | Create reference prices only from explicit metadata. |
| Outbound preview is mistaken for sent email | Keep preview/send separation, disabled send default, and explicit labels. |
| Future send bypasses governance | Require a separate send spec with RBAC, audit, confirmation, and credential handling. |

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
```

Future implementation validation should include focused tests for any changed
policy surface, plus the relevant backend/frontend/script gates. No future
implementation task may require real provider keys or live network calls in CI.

## Suggested Task Order

1. TASK 021.1 - Catalog Governance Policy And Version Contract
2. TASK 021.2 - Alias And Add-On Review Checklist
3. TASK 021.3 - Provider Evidence Trust-Level Policy
4. TASK 021.4 - Manual Review And Approval Boundary Policy
5. TASK 021.5 - Outbound Preview/Send Governance Policy
6. TASK 021.6 - Audit Event Requirements Planning
7. TASK 021.7 - Documentation, Validation, And Closeout
