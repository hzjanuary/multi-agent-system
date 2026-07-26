# SPEC-022 Tasks - Evaluation and Benchmarking

## Task List

### TASK 022.1 - Evaluation Scope And Metrics Contract

Status: Planned.

Goal: Define the evaluation dimensions, metric names, benchmark result format,
and safety violation categories before adding benchmark data or automation.

Scope:

- Define deterministic demo evaluation scope.
- Define benchmark result JSON shape and human-readable summary fields.
- Define correctness metrics for parsing, workflow lifecycle, evidence, and
  frontend smoke.
- Define safety violation categories.
- Preserve no-key defaults.

Acceptance criteria:

- Metrics contract is documented.
- Metrics are correctness/safety metrics, not business ROI or market-price
  performance claims.
- Result format excludes secrets, raw prompts, provider payloads, embeddings,
  vector payloads, cookies, tokens, real customer data, and chain-of-thought.
- No benchmark runner or CI job is implemented in this task.

Planned validation:

```bash
git diff --check
git status --short
```

### TASK 022.2 - Telegram Parser Benchmark Dataset Plan

Status: Planned.

Goal: Plan the English/Vietnamese RFQ dataset used to measure parser and
normalization behavior.

Scope:

- Define dataset row fields.
- Define supported RFQ examples.
- Define unsupported item examples.
- Define mixed supported/unsupported examples.
- Define greeting, missing quantity, missing item, noisy text, and add-on
  examples.
- Define expected technical and sales-style reply categories.

Acceptance criteria:

- Dataset plan covers English, Vietnamese accented, and Vietnamese unaccented
  inputs.
- Supported item accuracy and unsupported rejection accuracy are measurable.
- Mixed supported/unsupported requests are treated as safety-critical.
- No new parser behavior or tests are implemented in this task.

Planned validation:

```bash
git diff --check
git status --short
```

### TASK 022.3 - Workflow Lifecycle And Approval Gate Benchmark Plan

Status: Planned.

Goal: Plan validation for the deterministic workflow path and human approval
boundary.

Scope:

- Define lifecycle cases for `CREATED`, `WAITING_APPROVAL`, `APPROVED`,
  `COMPLETED`, `REJECTED`, `FAILED`, and `CANCELLED`.
- Define `/run` expectations.
- Define approval/history expectations.
- Define `/resume` expectations.
- Define RBAC and duplicate-decision safety checks.
- Define event/timeline evidence expectations.

Acceptance criteria:

- `/run -> WAITING_APPROVAL` is benchmarked as the normal pre-approval stop.
- `/resume` is benchmarked as the only post-approval continuation path.
- Approval/resume checks include authorized and unauthorized roles.
- No workflow runtime, API, database, or frontend behavior is changed.

Planned validation:

```bash
git diff --check
git status --short
```

### TASK 022.4 - Evidence, Catalog Metadata, And Outbound Preview Safety Plan

Status: Planned.

Goal: Plan benchmark checks for reference evidence, catalog metadata, and
approved outbound preview surfaces.

Scope:

- Define reference evidence safety cases.
- Define catalog metadata display cases.
- Define outbound preview gate cases.
- Define forbidden positive claims.
- Define redaction and bounding requirements.

Acceptance criteria:

- Reference evidence remains review material only.
- `is_final_quote=true` inputs are downgraded/rejected in expected behavior.
- Catalog metadata is displayed only when explicit workflow state contains it.
- Outbound preview remains read-only, post-completion, and no-send.
- No provider calls, live web calls, real email, or fake evidence are added.

Planned validation:

```bash
git diff --check
git status --short
```

### TASK 022.5 - Frontend Smoke And Pre-Demo Regression Checklist

Status: Planned.

Goal: Plan a repeatable UI smoke checklist and demo-regression routine.

Scope:

- Define key frontend routes and panels to inspect.
- Define desktop/mobile viewport expectations.
- Define status/action visibility expectations.
- Define safety copy and forbidden rendering checks.
- Define pre-demo command checklist.

Acceptance criteria:

- Smoke checklist covers login, demo command center, Agent Monitor, workflows,
  workflow detail, dashboard, evidence, catalog metadata, and outbound preview.
- Checklist avoids fake metrics and fake evidence.
- Regression checklist distinguishes safe deterministic checks from optional
  live/manual checks.
- No frontend implementation or new tests are added in this planning task.

Planned validation:

```bash
git diff --check
git status --short
```

### TASK 022.6 - Future Automation And CI Boundary Plan

Status: Planned.

Goal: Define which benchmark checks can later become automated local/CI gates
and which must remain manual-only.

Scope:

- Classify deterministic parser benchmark as future CI-safe.
- Classify frontend mocked smoke tests as future CI-safe.
- Keep Tavily/live provider verification manual-only.
- Keep full local demo rehearsal optional and explicitly confirmed.
- Define no-key and no-network CI boundary.

Acceptance criteria:

- CI boundary is documented.
- Real provider keys are not required in CI.
- No live web/provider calls are introduced into automated tests.
- No Docker/Compose/GitHub Actions changes are implemented in this planning
  task.

Planned validation:

```bash
git diff --check
git status --short
```

### TASK 022.7 - Documentation, Validation, And Closeout

Status: Planned.

Goal: Close SPEC-022 planning with updated index, handoff, and validation
evidence.

Scope:

- Update `.ai/specs/SPEC_INDEX.md`.
- Update `.codex/HANDOFF.md`.
- Confirm planning is consistent with SPEC-015 through SPEC-021.
- Run planning validation.

Acceptance criteria:

- SPEC-022 planning docs exist.
- SPEC index references SPEC-022 without reopening closed specs.
- Handoff points to SPEC-022 as the current planned spec.
- No product behavior is implemented.

Validation:

```bash
git diff --check
git status --short
```

## SPEC-022 Planning Closeout Checklist

- [x] Deterministic demo evaluation planned.
- [x] Telegram parser benchmark dataset planned.
- [x] English/Vietnamese RFQ test matrix planned.
- [x] Supported item accuracy metrics planned.
- [x] Unsupported item rejection metrics planned.
- [x] Mixed supported/unsupported safety checks planned.
- [x] Workflow lifecycle validation planned.
- [x] Approval/resume gate validation planned.
- [x] Reference evidence safety validation planned.
- [x] Catalog metadata display validation planned.
- [x] Outbound preview gate validation planned.
- [x] Frontend smoke checklist planned.
- [x] Regression checklist before demos planned.
- [x] Metrics format planned.
- [x] Future CI integration boundary planned.
- [x] User stories, risks, and mitigations documented.
- [x] No backend behavior changed.
- [x] No frontend behavior changed.
- [x] No Telegram behavior changed.
- [x] No API behavior changed.
- [x] No database models or migrations changed.
- [x] No Docker/Compose/CI behavior changed.
- [x] No provider calls or live web calls added.
- [x] No real email or final quote behavior added.
