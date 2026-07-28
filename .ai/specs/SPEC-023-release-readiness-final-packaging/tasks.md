# SPEC-023 Tasks - Release Readiness and Final Packaging

## Task List

### TASK 023.1 - Release Checklist And Packaging Inventory

Status: Planned.

Goal: Create the final release-readiness checklist and package inventory for
source, docs, scripts, validation outputs, and optional manually captured
evidence.

Scope:

- Add or update release checklist docs.
- Define required repository state checks.
- Define expected final evidence package contents.
- Define no-generated-artifact and no-secret checks.
- Cross-link existing final/report/evaluation/demo/deployment docs.

Acceptance criteria:

- Release checklist covers repository state, docs entry points, env/secrets,
  validation gates, screenshots/evidence, unsupported claims, and submission
  package.
- Checklist does not require screenshots, PDFs, DOCX, slides, videos, or live
  provider evidence unless explicitly collected later.
- No product behavior changes.

Validation:

```bash
git diff --check
git status --short
```

### TASK 023.2 - Documentation Index Consistency Review

Status: Planned.

Goal: Verify and document that README, demo docs, deployment docs, final docs,
report docs, scripts docs, governance docs, and evaluation docs are reachable
and consistent.

Scope:

- Review documentation entry points.
- Fix stale links or stale command references only where clearly docs-only.
- Confirm SPEC-001 through SPEC-022 references remain accurate.
- Confirm SPEC-023 is indexed.

Acceptance criteria:

- Root README points evaluators to current demo, deployment, final, report,
  governance, and evaluation entry points.
- Docs do not refer to retired repository names, stale routes, stale scripts, or
  stale demo assumptions.
- No backend/frontend/runtime behavior changes.

Validation:

```bash
git diff --check
git status --short
```

### TASK 023.3 - Demo Runbook And Manual Smoke Consistency

Status: Planned.

Goal: Ensure the final live demo path and frontend/manual smoke guidance are
consistent with the implemented stable demo.

Scope:

- Review `docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md`.
- Review `docs/demo/TELEGRAM_INBOUND_DEMO.md`.
- Review `docs/demo/FRONTEND_OPERATOR_GUIDE.md`.
- Review `docs/demo/FRONTEND_SMOKE_FLOW.md`.
- Cross-check workflow status semantics and route names.
- Keep provider live verification optional/manual.

Acceptance criteria:

- Demo docs agree that backend runtime remains deterministic/no-key by default.
- Telegram/Ollama extraction is optional and local.
- `/run` stops at `WAITING_APPROVAL`.
- Manager/Admin approval is required.
- `/resume` is explicit.
- no real email, final quote, auto-approval, or auto-resume is claimed.

Validation:

```bash
git diff --check
git status --short
```

### TASK 023.4 - Final Validation Command Checklist

Status: Planned.

Goal: Consolidate the final release validation commands and expected outputs.

Scope:

- Document deterministic SPEC-022 evaluation commands.
- Document backend and frontend gate commands.
- Document Compose and production-demo config commands.
- Document final quality gate command.
- Document optional manual smoke commands.
- Keep live provider verification manual-only.

Acceptance criteria:

- Checklist includes `evaluate_telegram_parser.py` and
  `evaluate_demo_safety.py`.
- Checklist includes backend/frontend/all gates.
- Checklist includes production-demo Compose config.
- Checklist distinguishes required no-key commands from optional manual/live
  commands.
- No CI behavior changes.

Validation:

```bash
git diff --check
git status --short
```

### TASK 023.5 - Stable Defaults, Feature Flags, And Safety Boundary Audit

Status: Planned.

Goal: Produce a release audit section for stable defaults, optional feature
flags, safety boundaries, and known limitations.

Scope:

- Confirm no-key default values.
- Confirm optional feature flags remain explicit.
- Confirm env templates contain placeholders only.
- Confirm no live provider key is required for release validation.
- Confirm safety boundaries and limitations are documented.

Acceptance criteria:

- `LLM_PROVIDER=fake`, `LLM_RUNTIME_ENABLED=false`,
  `PRICE_RESEARCH_ENABLED=false`, `RAG_ENABLED=false`,
  `OUTBOUND_COMMUNICATION_ENABLED=false`, and `OUTBOUND_SEND_ENABLED=false`
  remain documented as stable defaults.
- Optional flags for Telegram LLM extraction, sales replies, RAG, price
  research, Tavily, and outbound preview are documented.
- No final quote, real email, stock/delivery promise, discount approval,
  auto-approval, auto-resume, or unsupported silent item dropping is permitted.

Validation:

```bash
git diff --check
git status --short
```

### TASK 023.6 - Final Evidence Package Template

Status: Planned.

Goal: Define the final evidence capture structure for release reviewers without
capturing evidence in the planning task.

Scope:

- Define evidence artifact paths.
- Reference existing final evaluation report template.
- Reference screenshot checklist.
- Reference evaluation metrics JSON output locations.
- Reference manual smoke notes.
- Keep placeholders clearly marked.

Acceptance criteria:

- Evidence template makes it clear which files are expected later.
- Template does not claim evidence has already been captured.
- Template contains no secrets, real customer data, raw prompts, provider
  payloads, embeddings, vector payloads, or chain-of-thought.

Validation:

```bash
git diff --check
git status --short
```

### TASK 023.7 - Release Closeout Review

Status: Planned.

Goal: Perform final SPEC-023 closeout review and recommend release approval or
rejection.

Scope:

- Verify TASK 023.1 through TASK 023.6 deliverables.
- Run final documentation validation.
- Optionally run full quality gates when practical.
- Update SPEC-023 status and handoff.
- Document blocking and non-blocking issues.

Acceptance criteria:

- SPEC-023 deliverables exist and are indexed.
- Documentation and command references are consistent.
- Required release checks are documented and, when run, results are recorded.
- Known limitations are explicit.
- No product behavior changes are introduced.
- Release status is clearly `Approved / Closed` or `Rejected / blocked`.

Validation:

```bash
git diff --check
git status --short
```

Optional validation:

```bash
bash scripts/ci/all-gates.sh
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
```

## SPEC-023 Planning Deliverables

Implemented in this planning task:

- `.ai/specs/SPEC-023-release-readiness-final-packaging/spec.md`
- `.ai/specs/SPEC-023-release-readiness-final-packaging/tasks.md`
- `.ai/specs/SPEC_INDEX.md` updated
- `.codex/HANDOFF.md` updated

No backend code, frontend code, Telegram behavior, API contract, database
model/migration, Docker/Compose/CI behavior, provider call, live web call, real
email, or final quote behavior is changed by this planning task.
