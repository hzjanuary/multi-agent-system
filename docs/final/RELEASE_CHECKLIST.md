# Final Release Checklist

Use this checklist before the final graduation submission. It is a release
readiness checklist, not proof that final evidence has already been captured.

## 1. Repository State

| Check | Status | Notes |
|---|---|---|
| Working tree is clean after the final commit. | Pending | Run `git status --short`. |
| Branch name and final commit hash are recorded. | Pending | Record in the evaluation report or evidence template. |
| CI is passing for the final commit. | Pending | Use GitHub Actions and local gate output. |
| No untracked important files are left outside the release package. | Pending | Review `git status --short`. |
| No generated build artifacts are accidentally committed. | Pending | Exclude `.next`, node modules, caches, local DBs, and temporary logs. |
| No screenshots with secrets are committed. | Pending | Follow `docs/final/SCREENSHOT_CHECKLIST.md`. |

## 2. Documentation Entry Points

| Entry Point | Expected Coverage | Status |
|---|---|---|
| `README.md` | backend, frontend, demo, deployment, final evaluation, report assets, scripts | Pending |
| `backend/README.md` | backend setup, tests, demo seed, knowledge ingest, health/readiness/metrics | Pending |
| `frontend/README.md` | frontend setup, API/WS env, workflow/evidence UI scope, checks | Pending |
| `docs/final/README.md` | final evaluation, E2E validation, screenshots, demo script, Q&A, release checklist | Pending |
| `docs/report/README.md` | report outline, narratives, phases, architecture, diagrams, appendices | Pending |
| `docs/deployment/README.md` | env, production-demo Compose, runbook, smoke, troubleshooting, backup guidance | Pending |
| `scripts/README.md` | CI gates, smoke script, E2E script, final quality gate | Pending |

## 3. Environment And Secrets

| Check | Status | Notes |
|---|---|---|
| Env templates use placeholders only. | Pending | Review backend, frontend, CI, and production-demo examples. |
| No real provider keys are committed. | Pending | Run the no-secret scan in `FINAL_QUALITY_GATE.md`. |
| No production JWT secret is committed. | Pending | Production-demo templates must use placeholders. |
| No committed local `.env` files contain secrets. | Pending | Local real env files must remain untracked. |
| Demo credentials are marked local-demo/board-demo only. | Pending | See demo inventory and runbooks. |
| No real customer data is committed. | Pending | Demo data must stay synthetic. |

## 4. Quality Gates

| Gate | Command | Status |
|---|---|---|
| Compose gate | `bash scripts/ci/compose-gate.sh` | Pending |
| Backend gate | `bash scripts/ci/backend-gate.sh` | Pending |
| Frontend gate | `bash scripts/ci/frontend-gate.sh` | Pending |
| All gates | `bash scripts/ci/all-gates.sh` | Pending |
| Production image build | `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend` | Pending |
| Smoke script help | `bash scripts/deployment/smoke-prod-demo.sh --help` | Pending |
| E2E script help | `bash scripts/final/e2e-demo-validation.sh --help` | Pending |
| Final quality gate wrapper | `bash scripts/final/final-quality-gate.sh` | Pending |
| Whitespace | `git diff --check` and `git diff --cached --check` | Pending |
| Optional full E2E | `bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready` | Optional |
| Optional RAG E2E | `bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-rag` | Optional |

## 5. Final Evidence Assets

| Asset | Status |
|---|---|
| Evaluation matrix exists. | Pending |
| Acceptance evidence plan exists. | Pending |
| E2E checklist exists. | Pending |
| Evidence capture template exists. | Pending |
| Screenshot checklist exists. | Pending |
| Report narrative assets exist. | Pending |
| Mermaid diagram sources exist. | Pending |
| Final demo script exists. | Pending |
| Timing plan and fallback summary exist. | Pending |
| Defense Q&A bank exists. | Pending |

## 6. Safety And Overclaim Check

Before release, confirm docs and scripts do not claim these are implemented:

- cloud deployment automation
- Kubernetes or Terraform deployment
- production secret vault
- enterprise SSO
- production email sending
- production OCR
- upload/admin document management UI
- provider-management UI
- zero-downtime deployment
- production backup automation
- external telemetry vendor
- token streaming
- agent-thought streaming

Also confirm docs, examples, UI snippets, logs, and evidence do not expose raw
prompts, provider payloads, embeddings, vector payloads, tokens, cookies, API
keys, JWTs, secrets, or real customer data.

## 7. Final Submission Package

The final submission package should include:

- source repository
- root README
- backend and frontend READMEs
- demo runbook and frontend smoke flow
- deployment runbook and demo package docs
- final evaluation docs
- report narrative docs
- Mermaid diagram source docs
- screenshot checklist
- final demo script and timing plan
- defense Q&A bank
- optional screenshots and evidence files collected later after redaction

