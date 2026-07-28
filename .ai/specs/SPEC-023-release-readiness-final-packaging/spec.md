# SPEC-023 - Release Readiness and Final Packaging

## Status

Implemented / ready for closeout review

## Product Objective

Define the final release-readiness package for Multi-Agent System /
Enterprise Multi-Agent OS after SPEC-001 through SPEC-022 are completed and
approved.

SPEC-023 is a packaging and verification specification. It does not add product
features. Its purpose is to make the repository ready for final evaluator,
teacher, demo reviewer, and future developer handoff by consolidating release
checklists, documentation entry points, validation commands, safety boundaries,
known limitations, and post-release roadmap guidance.

Implemented release package docs:

- `docs/release/RELEASE_READINESS_CHECKLIST.md`
- `docs/release/FINAL_PROJECT_PACKAGE.md`
- `docs/release/DEMO_COMMANDS.md`
- `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md`

## Context

The project currently includes:

- deterministic backend procurement workflow demo;
- Telegram inbound demo bridge with deterministic parser and optional local
  Ollama RFQ extraction;
- expanded deterministic demo catalog;
- reference evidence and price research foundation;
- manual-only provider live verification guidance;
- approved outbound preview only, with no send path;
- governance policies for catalog, provider evidence, approval, and outbound
  communication;
- SPEC-022 deterministic evaluation benchmark runners;
- Violet Operations Console frontend with dashboard, Agent Monitor, workflow
  list/detail, approval/resume, reference evidence, catalog metadata, and
  outbound preview surfaces.

SPEC-015 already created graduation evaluation/report/demo assets. SPEC-023 is
the final repository packaging layer that checks whether those assets, the
post-demo specs, and executable gates are aligned before release.

## Scope

SPEC-023 covers release packaging docs for:

- final release checklist;
- documentation index consistency;
- demo runbook consistency;
- evaluation command checklist;
- backend/frontend gate checklist;
- stable environment defaults;
- optional feature flag inventory;
- safety boundary checklist;
- known limitations;
- screenshots/manual smoke checklist references;
- final evidence package structure;
- repository hygiene and no-secret checks;
- future roadmap after release;
- acceptance criteria;
- task sequence.

## Non-Goals

- No backend code changes.
- No frontend code changes.
- No Telegram bridge behavior changes.
- No API changes.
- No database models or migrations.
- No Docker/Compose/CI behavior changes.
- No provider calls.
- No live web calls.
- No LLM calls.
- No real email.
- No final quote behavior.
- No auto-approval or auto-resume.
- No screenshots, videos, slides, PDF, DOCX, or thesis generation in planning.
- No cloud deployment automation.
- No Kubernetes or Terraform implementation.
- No production secret vault, enterprise SSO, OCR/upload UI, or production
  notification delivery.

## Release Package Model

```text
Repository release package
  -> source code
      -> backend
      -> frontend
      -> scripts
  -> executable validation
      -> compose gates
      -> backend gate
      -> frontend gate
      -> final quality gate
      -> SPEC-022 evaluation runners
  -> demo operation docs
      -> final live demo runbook
      -> Telegram inbound demo
      -> frontend operator guide
      -> deployment runbook
  -> final evidence docs
      -> evaluation matrix
      -> evidence plan
      -> E2E validation checklist
      -> screenshot checklist
      -> report assets
      -> diagram sources
  -> release safety review
      -> no secrets
      -> no unsupported claims
      -> no final quote
      -> no live provider requirement
      -> known limitations
```

## Final Release Checklist

The final checklist should confirm:

- working tree contains only intentional release changes;
- branch name and commit hash are recorded in the final evidence package;
- root README is the public landing page;
- docs entry points are reachable and not stale;
- demo runbooks match current commands and route names;
- evaluation runners pass with deterministic/no-key defaults;
- backend and frontend gates pass;
- production-demo Compose config validates;
- production-demo image build passes when release validation is run;
- screenshots/evidence are either intentionally absent or stored in the
  approved final evidence location;
- no generated artifacts are accidentally committed;
- no real secrets, provider keys, Telegram tokens, cookies, passwords, JWTs, or
  customer data are committed.

## Documentation Index Consistency

Release readiness must check these entry points:

- `README.md`
- `backend/README.md`
- `frontend/README.md`
- `scripts/README.md`
- `docs/demo/DEMO_RUNBOOK.md`
- `docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md`
- `docs/demo/FRONTEND_OPERATOR_GUIDE.md`
- `docs/demo/TELEGRAM_INBOUND_DEMO.md`
- `docs/deployment/README.md`
- `docs/deployment/RUNBOOK.md`
- `docs/deployment/SMOKE_CHECKS.md`
- `docs/final/README.md`
- `docs/report/README.md`
- `docs/report/diagrams/README.md`
- `docs/evaluation/SPEC_022_EVALUATION_GUIDE.md`
- `docs/evaluation/DEMO_REGRESSION_CHECKLIST.md`
- `docs/governance/GOVERNANCE_CHANGE_CHECKLIST.md`

The release package should not introduce a separate documentation site unless a
future task explicitly scopes it.

## Demo Runbook Consistency

Final demo docs must agree on:

- stable backend mode:
  - `LLM_PROVIDER=fake`
  - `LLM_RUNTIME_ENABLED=false`
  - `PRICE_RESEARCH_ENABLED=false`
  - `RAG_ENABLED=false` unless explicitly enabled for a RAG demo;
- Telegram bridge path:
  - local Telegram token only;
  - deterministic parser by default;
  - optional Ollama extraction only for Telegram RFQ extraction;
  - no Telegram live price research;
- workflow path:
  - customer RFQ creates workflow;
  - `/run` stops at `WAITING_APPROVAL`;
  - Manager/Admin approval is required;
  - `/resume` is explicit;
  - completion produces preview/evidence surfaces only when workflow state
    contains explicit data;
- outbound path:
  - preview-only;
  - no Gmail/SMTP send;
  - no real email sent.

## Evaluation Command Checklist

Release readiness should preserve this deterministic evaluation set:

```bash
python3 -m unittest scripts.evaluation.test_evaluate_telegram_parser
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_telegram_parser.py \
  --output-json /tmp/telegram_eval_metrics.json

python3 -m unittest scripts.evaluation.test_evaluate_demo_safety
python3 scripts/evaluation/evaluate_demo_safety.py
python3 scripts/evaluation/evaluate_demo_safety.py \
  --output-json /tmp/demo_safety_metrics.json
```

Expected evaluation boundaries:

- deterministic;
- no backend API calls;
- no database required;
- no Telegram network calls;
- no LLM/provider calls;
- no Tavily/live web calls;
- no email delivery.

## Backend And Frontend Gate Checklist

Release validation should include:

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config

bash scripts/ci/compose-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
bash scripts/final/final-quality-gate.sh
```

Backend-specific release evidence should include:

- pytest summary;
- Ruff result;
- Black check result;
- MyPy result;
- demo seed dry-run summary;
- knowledge ingestion dry-run summary.

Frontend-specific release evidence should include:

- lint result;
- production build result;
- typecheck result;
- test result;
- manual smoke notes for core pages.

## Stable Environment Defaults

The final release must keep these defaults stable unless a future approved spec
changes them:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
PRICE_RESEARCH_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
TELEGRAM_LLM_EXTRACTION_ENABLED=false
TELEGRAM_SALES_REPLY_ENABLED=false
```

Production-demo env templates must use placeholders only and must not require
real provider keys.

## Optional Feature Flags

Optional features should remain explicit:

- `TELEGRAM_LLM_EXTRACTION_ENABLED=true` for local Telegram/Ollama extraction;
- `TELEGRAM_SALES_REPLY_ENABLED=true` for local sales-style replies;
- `RAG_ENABLED=true` only with explicit knowledge ingestion;
- `PRICE_RESEARCH_ENABLED=true` only for future explicitly integrated
  reference evidence flows;
- `TAVILY_API_KEY` only for manual live provider verification;
- `OUTBOUND_COMMUNICATION_ENABLED=true` only for preview loading after
  approval/resume evidence;
- `OUTBOUND_SEND_ENABLED=false` must remain the safe release default.

## Safety Boundaries

Release readiness must confirm:

- no final quotation before Manager/Admin approval and explicit resume;
- no auto-approval;
- no auto-resume;
- no real email sending;
- no stock availability claim;
- no delivery promise;
- no discount approval claim;
- no unsupported item silently dropped;
- no fake reference evidence;
- no provider live verification required in CI;
- no raw prompts, provider payloads, embeddings, vector payloads,
  chain-of-thought, tokens, cookies, passwords, API keys, or real customer data
  in docs, examples, logs, screenshots, tests, or committed files.

## Known Limitations

SPEC-023 should keep limitations explicit:

- production cloud deployment is not implemented;
- Kubernetes/Terraform are not implemented;
- enterprise SSO is not implemented;
- production secret vault is not implemented;
- production email sending is not implemented;
- production backup automation is not implemented;
- OCR/upload document management UI is not implemented;
- provider-management UI is not implemented;
- live external price research is manual-only and not part of the stable demo;
- reference evidence is not an approved quotation;
- catalog remains demo-governed and bounded;
- multi-tenant isolation and billing are future work.

## Screenshots And Manual Smoke Checklist

SPEC-023 should reference, not recreate, screenshot and smoke assets:

- `docs/final/SCREENSHOT_CHECKLIST.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
- `docs/demo/FRONTEND_OPERATOR_GUIDE.md`
- `docs/evaluation/DEMO_REGRESSION_CHECKLIST.md`

Manual smoke should cover:

- `/login`
- `/demo`
- `/agent-monitor`
- `/agent-monitor?workflowId=<workflow_id>`
- `/workflows`
- `/workflows/<workflow_id>`
- `/dashboard`
- approval/resume controls;
- Agent Activity;
- timeline/events;
- catalog metadata;
- reference evidence;
- outbound preview.

## Future Roadmap After Release

Recommended post-release work:

1. Cloud deployment automation with secret management.
2. Enterprise SSO and production RBAC administration.
3. Production catalog management and pricing governance UI.
4. Approved live provider verification workflow and evidence audit storage.
5. Production email/Gmail integration with approval and audit controls.
6. Document upload/admin UI with OCR/PDF parsing.
7. Multi-tenant isolation, backup automation, and operational SLOs.
8. Expanded evaluation automation and optional CI integration for
   deterministic benchmarks.

## Acceptance Criteria

- SPEC-023 spec and tasks docs exist.
- SPEC index references SPEC-023 without number conflict.
- Handoff points to SPEC-023 as implemented and ready for closeout review.
- Final release checklist is defined.
- Documentation index consistency checks are defined.
- Demo runbook consistency checks are defined.
- Evaluation command checklist is defined.
- Backend/frontend gate checklist is defined.
- Stable environment defaults and optional flags are documented.
- Safety boundaries and known limitations are explicit.
- Screenshot/manual smoke references are included.
- Future roadmap after release is included.
- No product behavior, backend code, frontend code, Telegram behavior, API,
  database, Docker/Compose/CI behavior, provider call, live web call, real
  email, or final quote behavior is changed.

## Implemented Deliverables

- Release readiness checklist with stable defaults, optional feature flags,
  backend/frontend/evaluation gates, Compose checks, secret/untracked override
  review, final approval checklist, known limitations, and no-send/no-final-
  quotation boundaries.
- Final project package summary with purpose, architecture overview, completed
  spec status, core user journey, stable demo path, optional Telegram/Ollama
  path, optional provider verification path, catalog/governance/evaluation
  layers, safety model, docs map, and future roadmap.
- Demo command sheet with supported copy-ready commands for local services,
  health checks, frontend dev run, demo seed, Telegram bridge dry run/manual
  run, evaluation runners, provider dry run, quality gates, E2E help, smoke
  help, and safe shutdown.
- Known limitations and roadmap doc covering no real email, no outbound send
  endpoint, no automatic live provider calls, no Telegram live price research,
  no final quote before approval/resume, manual-only provider verification,
  deterministic demo catalog boundaries, and bounded future roadmap.
- README release-doc links.
- SPEC index and handoff status updates.

No backend code, frontend code, Telegram behavior, API contract, database
model/migration, Docker/Compose/CI behavior, provider call, live web call, real
email, or final quote behavior was changed.

## Validation

Closeout validation run for SPEC-023:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
bash scripts/ci/all-gates.sh
```

Observed result summary:

- whitespace check passed;
- working tree contains only intended SPEC-023 docs/spec/handoff/README changes
  and new `docs/release/` files;
- local and production-demo Compose config validation passed;
- Telegram parser benchmark passed: 25/25 cases, accuracy 1.0000, 0 safety
  violations;
- demo safety benchmark passed: 39/39 cases, accuracy 1.0000, 0 safety
  violations;
- full `all-gates.sh` passed, including backend tests/static checks,
  frontend lint/build/typecheck/tests, production-demo image build, and
  whitespace check.
