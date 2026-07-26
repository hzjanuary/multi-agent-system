# SPEC-022 - Evaluation and Benchmarking

## Status

Sprint 2 implemented / ready for review

## Product Objective

Define a product-grade evaluation and benchmarking plan for the completed
Multi-Agent System demo path and post-demo safety foundations.

SPEC-022 plans how the project should measure deterministic demo quality,
Telegram RFQ parsing, catalog support, unsupported-item safety, workflow
lifecycle correctness, approval/resume gates, reference evidence handling,
catalog metadata display, outbound preview policy, frontend usability, and
regression readiness before live demos.

Sprint 1 added deterministic Telegram parser evaluation assets:

- `scripts/evaluation/telegram_parser_cases.json`
- `scripts/evaluation/evaluate_telegram_parser.py`
- `scripts/evaluation/test_evaluate_telegram_parser.py`

Sprint 2 adds deterministic demo-safety evaluation assets:

- `scripts/evaluation/demo_safety_cases.json`
- `scripts/evaluation/evaluate_demo_safety.py`
- `scripts/evaluation/test_evaluate_demo_safety.py`
- `docs/evaluation/SPEC_022_EVALUATION_GUIDE.md`
- `docs/evaluation/DEMO_REGRESSION_CHECKLIST.md`

The Sprint 2 benchmark covers a 39-case deterministic safety matrix for
workflow lifecycle transitions, invalid transition blocking,
approval/resume/outbound preview gates, reference evidence schema safety,
fake/manual/RAG/Tavily reference evidence fixtures, catalog metadata safety,
frontend evidence/catalog bounding assumptions, and stable no-key/default-
disabled settings.

SPEC-022 does not add CI jobs, backend behavior, frontend behavior, Telegram
runtime behavior, API endpoints, database models, provider calls, live web
calls, LLM calls, Tavily calls, workflow mutation, or email sending.

Stable defaults remain unchanged:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
```

## Background

SPEC-001 through SPEC-021 are completed or ready for closeout review. The
project now has:

- deterministic workflow runtime and demo seed data;
- Telegram RFQ intake with deterministic English/Vietnamese parsing,
  optional local Ollama extraction, catalog normalization, sales-style replies,
  and mixed unsupported-item protection;
- deterministic demo catalog support for laptops, desktop PCs, monitors,
  printers, keyboard/mouse combos, and Office 365 add-ons;
- reference price/evidence schemas and fake/manual/RAG/Tavily provider
  foundations, disabled by default;
- frontend Agent Monitor, workflow detail, catalog metadata, reference
  evidence, approval/resume, and outbound preview surfaces;
- preview-only approved outbound communication after completed workflows;
- governance docs for catalog, provider evidence, approval, and outbound
  policy.

SPEC-015 covers final graduation evaluation assets. SPEC-022 is narrower and
more product-operational: it defines repeatable benchmark protocols, metrics,
datasets, and regression checklists for future implementation tasks.

## Scope

SPEC-022 should define future planning for:

- deterministic demo evaluation;
- Telegram parser benchmark dataset;
- English/Vietnamese RFQ test matrix;
- supported item accuracy;
- unsupported item rejection accuracy;
- mixed supported/unsupported safety;
- workflow lifecycle validation;
- approval/resume gate validation;
- reference evidence safety validation;
- catalog metadata display validation;
- outbound preview gate validation;
- frontend smoke checklist;
- regression checklist before demos;
- benchmark metrics format;
- future CI integration boundary;
- user stories;
- acceptance criteria;
- risks and mitigations;
- implementation task sequence.

## Non-Goals

- No new backend behavior.
- No new frontend behavior.
- No Telegram bridge behavior changes.
- No API endpoint changes.
- No database models or migrations.
- No Docker/Compose/CI changes.
- No new tests in this planning task.
- No benchmark automation scripts in this planning task.
- No provider calls, live web calls, or real price lookup.
- No real email sending.
- No final quote behavior.
- No auto-approval or auto-resume.
- No fake evidence, fake live provider proof, stock promise, delivery promise,
  discount approval, or customer-facing final quotation.

## Evaluation Architecture

```text
Benchmark plan
  -> benchmark dataset definitions
      -> Telegram parser RFQs
      -> workflow lifecycle scenarios
      -> evidence safety fixtures
      -> frontend smoke scenarios
  -> expected outcomes
      -> parse result
      -> workflow status transition
      -> approval/resume boundary
      -> evidence rendering boundary
      -> outbound preview boundary
  -> score format
      -> pass/fail counts
      -> precision/recall-style parser metrics
      -> safety violation counts
      -> regression summary
  -> future automation
      -> local command first
      -> optional CI integration later
      -> no real provider keys by default
```

The evaluation layer should sit outside product behavior. It may inspect public
APIs, local deterministic parser functions, frontend rendered states, scripts,
and documentation, but it must not change workflow semantics.

## Evaluation Dimensions

### Deterministic Demo Evaluation

Goal: prove the stable local demo path remains reproducible without real
provider keys.

Planned checks:

- environment defaults are no-key;
- demo seed data is explicit and idempotent enough for local demonstration;
- Telegram bridge can operate with deterministic parser only;
- workflow `/run` reaches `WAITING_APPROVAL`;
- `/resume` is the only post-approval continuation path;
- no final quote, real email, auto-approval, or auto-resume occurs.

Primary evidence sources:

- `docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md`;
- `docs/demo/TELEGRAM_INBOUND_DEMO.md`;
- `docs/final/E2E_DEMO_VALIDATION.md`;
- future SPEC-022 benchmark report artifact.

### Telegram Parser Benchmark Dataset

Goal: define a repeatable dataset of customer messages and expected parser
outcomes.

Dataset categories should include:

- English supported RFQs;
- Vietnamese supported RFQs with accents;
- Vietnamese supported RFQs without accents;
- greeting/help messages;
- missing quantity;
- missing item;
- unknown item;
- mixed supported/unsupported request;
- supported item with compatible add-on;
- supported item with incompatible or ambiguous add-on if introduced later;
- malformed or noisy customer text.

Each row should define:

- id;
- language;
- input text;
- expected intent;
- expected normalized item family;
- expected quantity;
- expected add-ons;
- expected catalog metadata presence;
- expected follow-up/rejection reason;
- expected workflow creation: yes/no;
- safety notes;
- related test or manual validation command once implemented.

The dataset must avoid real customer data and must not include secrets.

### English/Vietnamese RFQ Test Matrix

Goal: cover both exact board-demo wording and natural RFQ variants.

Example future matrix dimensions:

| Axis | Values |
| --- | --- |
| Language | English, Vietnamese accented, Vietnamese unaccented |
| Intent | procurement RFQ, greeting, unsupported, other |
| Item status | supported, unsupported, mixed |
| Quantity | valid positive integer, missing, invalid |
| Add-on | none, Office 365, unsupported add-on |
| Expected action | create workflow, ask follow-up, reject unsupported |
| Reply style | technical, sales-style |

### Supported Item Accuracy

Goal: measure whether supported catalog requests are correctly accepted and
normalized.

Planned metrics:

- supported acceptance rate;
- normalized item accuracy;
- quantity extraction accuracy;
- add-on extraction accuracy;
- catalog metadata presence rate for created workflows;
- false rejection count.

### Unsupported Item Rejection Accuracy

Goal: measure whether unsupported requests fail closed instead of creating bad
workflows.

Planned metrics:

- unsupported rejection rate;
- false acceptance count;
- follow-up clarity score placeholder;
- unsupported item mention coverage.

Unsupported rejection must include cases where the unsupported item appears
beside a supported item.

### Mixed Supported/Unsupported Safety

Goal: prove mixed requests are not silently converted into partial workflows.

Required scenario examples:

- laptop plus unsupported service;
- laptop plus unsupported product family;
- supported catalog item plus unsupported add-on;
- LLM extraction returns only supported item while original text includes
  unsupported item.

Acceptance boundary:

- no workflow is created by default;
- technical and sales replies mention both the supported and unsupported
  portions;
- the user is asked for a supported-only RFQ or catalog expansion.

### Workflow Lifecycle Validation

Goal: verify the core state path remains stable:

```text
CREATED -> /run -> WAITING_APPROVAL -> approve -> APPROVED -> /resume -> COMPLETED
```

Validation should include:

- status transition checks;
- `waiting_for_approval=true` at the pause;
- `completed=false` before resume;
- persisted stage/runtime events;
- no email preview before approval/resume;
- terminal states block invalid actions.

### Approval/Resume Gate Validation

Goal: prove human approval remains the decision boundary.

Checks should include:

- Manager/Admin approval allowed;
- Viewer/non-authorized mutation forbidden;
- duplicate final decisions blocked;
- rejected workflows remain terminal;
- request-changes behavior remains non-final where supported;
- `/run` does not auto-resume;
- `/resume` requires prior approval.

### Reference Evidence Safety Validation

Goal: verify reference evidence remains bounded review material only.

Checks should include:

- no final quote rendering;
- no inferred price from prose;
- no stock, delivery, discount, approval, or email-sent claims;
- `is_final_quote=true` evidence is downgraded or rejected;
- raw provider payloads, prompts, embeddings, vector payloads, tokens,
  cookies, secrets, raw HTML, and chain-of-thought are not rendered;
- low-confidence or empty evidence produces manual-review wording.

### Catalog Metadata Display Validation

Goal: verify frontend surfaces show explicit catalog metadata only when
workflow state contains it.

Checks should include:

- normalized item family;
- catalog version;
- SKU/code when present;
- add-ons and compatibility notes;
- unsupported-warning absence for created supported workflows;
- no fabricated catalog metadata from prose, events, or agent summaries.

### Outbound Preview Gate Validation

Goal: verify approved outbound preview remains read-only and post-completion
only.

Checks should include:

- preview endpoint/panel requires completed workflow;
- preview requires approval and resume completion evidence;
- non-completed workflows show pending/unavailable state;
- no send button;
- no SMTP/Gmail/provider call;
- no event mutation from preview reads unless a future spec changes that
  explicitly;
- warnings remain visible.

### Frontend Smoke Checklist

Goal: define a repeatable UI smoke path before demos.

Surfaces:

- `/login`;
- `/demo`;
- `/agent-monitor`;
- `/agent-monitor?workflowId=<id>`;
- `/workflows`;
- `/workflows/<id>`;
- `/dashboard`;
- workflow detail approval/resume;
- Agent Activity Panel;
- catalog metadata panel;
- reference evidence panel;
- outbound preview panel when available.

Checks:

- no default white/unstyled surfaces on core pages;
- mobile viewport has no horizontal overflow;
- current status and next action are visible;
- safety copy remains visible;
- no fake metrics/evidence;
- no secrets or raw provider payloads rendered.

### Regression Checklist Before Demos

Goal: define a fast pre-demo regression checklist.

Future checklist should include:

- `git status --short`;
- compose config validation;
- backend gate or targeted backend tests;
- frontend gate or targeted frontend tests;
- Telegram parser unit tests;
- Tavily live smoke dry-run only;
- final E2E script help;
- manual runbook review;
- no-secret scan review;
- optional full local demo rehearsal.

## Metrics Format

Future benchmark output should be machine-readable and human-reviewable.

Recommended JSON shape:

```json
{
  "benchmark_name": "telegram_parser_rfq_matrix",
  "version": "SPEC-022-draft",
  "run_id": "local timestamp or uuid",
  "run_at": "ISO-8601 timestamp",
  "environment": "local-demo",
  "mode": "deterministic",
  "summary": {
    "total_cases": 0,
    "passed": 0,
    "failed": 0,
    "safety_violations": 0
  },
  "metrics": {
    "supported_acceptance_rate": null,
    "unsupported_rejection_rate": null,
    "mixed_request_block_rate": null,
    "quantity_accuracy": null,
    "item_normalization_accuracy": null,
    "addon_accuracy": null
  },
  "cases": [],
  "warnings": []
}
```

Planning notes:

- Do not invent metrics before benchmark implementation runs.
- Percentages should include numerator and denominator in any future report.
- Safety violations should be counted separately from normal parse mistakes.
- Outputs must not include tokens, API keys, raw prompts, provider payloads,
  chain-of-thought, real customer data, or local `.env` contents.

## Future CI Integration Boundary

SPEC-022 may later add CI integration only after explicit implementation
tasks. The planned boundary is:

- deterministic parser benchmark can be CI-safe;
- frontend smoke tests can be CI-safe when using existing mocked APIs;
- provider live smoke must remain manual-only and never require keys in CI;
- full local demo rehearsal should remain optional and explicitly confirmed;
- no benchmark may send real email, create cloud resources, or call live web
  providers by default.

## User Stories

### Evaluator Reviews Demo Quality

As an evaluator, I want a clear benchmark summary so I can understand whether
the demo path is stable, safe, and repeatable.

### Developer Checks Telegram Parser Changes

As a developer, I want an English/Vietnamese RFQ benchmark dataset so parser
changes can be validated against supported, unsupported, and mixed-item cases.

### Governance Owner Reviews Catalog Expansion

As a governance owner, I want catalog benchmark results to show supported-item
accuracy and unsupported-item rejection so new aliases do not create unsafe
workflows.

### Manager Reviews Approval Gate Safety

As a Manager, I want approval/resume benchmark checks so I can trust that
workflows do not continue or produce customer-ready communication before human
approval.

### Operator Runs Pre-Demo Regression

As a demo operator, I want a concise pre-demo checklist so I can verify the
system without running unsafe provider calls or mutating production-like data.

## Acceptance Criteria

- SPEC-022 defines deterministic demo evaluation scope.
- SPEC-022 defines a Telegram parser benchmark dataset plan.
- SPEC-022 defines an English/Vietnamese RFQ matrix.
- SPEC-022 defines supported item accuracy metrics.
- SPEC-022 defines unsupported item rejection metrics.
- SPEC-022 defines mixed supported/unsupported safety checks.
- SPEC-022 defines workflow lifecycle validation.
- SPEC-022 defines approval/resume gate validation.
- SPEC-022 defines reference evidence safety validation.
- SPEC-022 defines catalog metadata display validation.
- SPEC-022 defines outbound preview gate validation.
- SPEC-022 defines frontend smoke checklist scope.
- SPEC-022 defines a regression checklist before demos.
- SPEC-022 defines metrics format guidance.
- SPEC-022 defines future CI integration boundaries.
- SPEC-022 includes user stories, risks, mitigations, and task sequence.
- Planning does not add tests, scripts, provider calls, product behavior, API
  endpoints, database changes, Docker/CI changes, real email, or final quote
  behavior.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Benchmark dataset becomes stale after catalog changes | Require catalog version and expected outcome fields per case. |
| Parser benchmark rewards unsafe partial acceptance | Track mixed-request block rate and count silent-drop behavior as safety violation. |
| Metrics are misread as business performance claims | Label metrics as benchmark correctness/safety only, not latency, ROI, or market accuracy. |
| Provider evidence checks accidentally require live keys | Keep live provider verification manual-only and separate from CI. |
| Frontend smoke checklist turns into fake UI assertions | Require evidence only from existing workflow state/API fixtures. |
| Outbound preview benchmark implies real email send | Keep send behavior out of scope and check that no send button/provider call exists. |
| Benchmark reports expose secrets or raw provider data | Redact and bound outputs; forbid raw prompts, payloads, tokens, cookies, and secrets. |

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
```

Future implementation validation may include:

```bash
python -m unittest scripts.demo.test_telegram_inbound_bridge
docker compose run --rm backend-test pytest -q
cd frontend && npm test
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
```

These future commands are not required by this planning task.

## Suggested Task Order

1. TASK 022.1 - Evaluation Scope And Metrics Contract
2. TASK 022.2 - Telegram Parser Benchmark Dataset Plan
3. TASK 022.3 - Workflow Lifecycle And Approval Gate Benchmark Plan
4. TASK 022.4 - Evidence, Catalog Metadata, And Outbound Preview Safety Plan
5. TASK 022.5 - Frontend Smoke And Pre-Demo Regression Checklist
6. TASK 022.6 - Future Automation And CI Boundary Plan
7. TASK 022.7 - Documentation, Validation, And Closeout
