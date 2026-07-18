# Acceptance Evidence Plan

This plan defines what later SPEC-015 tasks should capture to prove final
graduation readiness. It does not claim that evidence has already been
collected.

## Capture Rules

- Record command, date, environment profile, and summarized result.
- Prefer summaries and bounded excerpts over full logs.
- Redact secrets before saving output.
- Do not save local `.env` files.
- Do not include bearer tokens, refresh tokens, API keys, JWT secrets,
  database passwords, object storage credentials, raw prompts, provider
  payloads, raw embeddings, raw vector payloads, full unbounded documents, real
  customer data, or chain-of-thought.
- Mark evidence as `default no-key` or `optional RAG-enabled`.
- Link failures to exact blocker notes instead of editing evidence to look
  successful.

## Automated Command Evidence

Use existing commands only.

| Evidence item | Command | Expected proof | Artifact placeholder |
| --- | --- | --- | --- |
| Repository status before final capture | `git status --short` | Shows expected docs-only or release-polish changes | `docs/final/EVALUATION_REPORT.md#repository-state` |
| Local Compose config | `docker-compose config` | Compose config exits successfully | `docs/final/EVALUATION_REPORT.md#compose` |
| Production-demo Compose config | `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config` | Production-demo Compose config exits successfully with placeholder env | `docs/final/EVALUATION_REPORT.md#compose` |
| Compose gate script | `bash scripts/ci/compose-gate.sh` | Local and production-demo Compose config checks pass | `docs/final/EVALUATION_REPORT.md#quality-gates` |
| Backend quality gate | `bash scripts/ci/backend-gate.sh` | Backend-test build, Alembic upgrade, pytest, Ruff, Black, MyPy, demo seed dry-run, and knowledge ingest dry-run pass | `docs/final/EVALUATION_REPORT.md#backend-gate` |
| Frontend quality gate | `bash scripts/ci/frontend-gate.sh` | Frontend install, lint, build, typecheck, and test pass serially | `docs/final/EVALUATION_REPORT.md#frontend-gate` |
| Full local gate | `bash scripts/ci/all-gates.sh` | Compose, backend, frontend, production image build, and whitespace checks pass | `docs/final/EVALUATION_REPORT.md#quality-gates` |
| Production image build | `docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend` | Backend and frontend production-demo images build without real secrets | `docs/final/EVALUATION_REPORT.md#deployment-readiness` |
| Smoke script contract | `bash scripts/deployment/smoke-prod-demo.sh --help` | Smoke script options and non-mutating default are available | `docs/final/EVALUATION_REPORT.md#smoke` |
| E2E demo validation contract | `bash scripts/final/e2e-demo-validation.sh --help` | Final demo validation script options, mutation guard, and no-secret behavior are available | `docs/final/EVALUATION_REPORT.md#e2e-demo-validation` |
| Demo seed dry-run | `docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json` | Machine-readable non-committing seed summary | `docs/final/EVALUATION_REPORT.md#demo-data` |
| Knowledge ingest dry-run | `docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json` | Machine-readable non-committing ingestion summary with fake embeddings | `docs/final/EVALUATION_REPORT.md#rag-grounding` |
| Whitespace check | `git diff --check` | No whitespace errors; line-ending warnings are documented if present | `docs/final/EVALUATION_REPORT.md#repository-state` |

Optional production-demo smoke can be captured when a local machine supports
the stack:

```bash
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example up -d
bash scripts/deployment/smoke-prod-demo.sh --include-ready
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example down --remove-orphans
```

Use an untracked production-demo env file with replaced placeholders for a real
board demo. Do not commit that env file.

## Manual Demo Evidence

| Evidence item | Manual source | Expected artifact |
| --- | --- | --- |
| Manager/Admin login | `docs/demo/DEMO_RUNBOOK.md` and frontend `/login` | Screenshot or checklist row showing successful authenticated state |
| Workflow dashboard | `/dashboard` and `/workflows` | Screenshot of seeded workflow list without fake data |
| Workflow detail before run | Seeded or newly created workflow detail route | Screenshot/checklist row with state, run panel, timeline, approval/evidence panels |
| Runtime to `WAITING_APPROVAL` | Workflow detail run action | Status progression table and timeline evidence |
| Event timeline | Workflow detail timeline | Persisted/live event notes; no fake streamed events |
| Approval panel/history | Waiting workflow detail | Approval action result and history row |
| Explicit resume | Approved workflow detail | Resume result, `COMPLETED` status, and final timeline evidence |
| Viewer/RBAC forbidden path | Viewer or non-approval role session | Screenshot/checklist row with understandable 403 behavior |
| RAG evidence panel | Optional `RAG_ENABLED=true` workflow run after ingestion | Citation cards with bounded excerpts and source metadata |
| Knowledge search/catalog | Workflow detail knowledge panels | Search result and document catalog evidence after ingestion |
| Readiness checks | `/health`, `/live`, `/ready` | Endpoint result summary |
| Metrics checks | Admin/Manager metrics endpoint | Safe JSON summary without secrets |

## No-Key Evaluation Modes

Default mode:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

Expected behavior:

- no real provider keys required
- no live LLM network calls
- deterministic runtime path
- workflow still stops at `WAITING_APPROVAL`
- approval and resume remain explicit

Optional RAG-enabled mode:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

Expected behavior:

- no real LLM keys required
- knowledge ingestion is explicit
- fake embeddings remain deterministic
- RAG citations may appear only after ingestion and a RAG-enabled workflow run
- empty evidence states are acceptable when RAG is disabled or evidence has not
  been attached

## Safety Evidence Checklist

Capture final safety proof with checklist rows, not raw secret-bearing logs.

- Tracked env templates use placeholders only.
- No local `.env` file with real secrets is tracked.
- Demo credentials are marked local-demo/board-demo only.
- No raw prompts, provider payloads, embeddings, vector payloads, secrets, or
  chain-of-thought are displayed in UI, logs, API responses, metrics, or saved
  evidence.
- Metrics endpoint access is limited to Admin/Manager.
- Approval/resume mutations are backend-authorized.
- Startup does not auto-run migrations, demo seed, knowledge ingestion, RAG
  ingestion, LLM provider calls, or email sending.
- Production-demo docs warn not to publicly expose Postgres, Redis, Qdrant, or
  MinIO without network and credential hardening.
- CI and local gates use fake/no-key defaults and do not deploy or push images.
- Cloud resources, Kubernetes, Terraform, secret vault, enterprise SSO,
  production email, upload UI, admin document management, token streaming, and
  agent-thought streaming remain documented future work.

Suggested no-secret scan commands for later release polish:

```bash
rg -n "sk-|AIza|ghp_|xox[baprs]-|BEGIN (RSA|OPENSSH|PRIVATE)|password=|api[_-]?key|secret" . --glob "!frontend/node_modules/**" --glob "!frontend/.next/**" --glob "!backend/.venv/**" --glob "!harness.db"
git status --short
```

These commands may produce false positives in placeholder docs. Review matches
manually before claiming final safety status.

## Expected Final Artifacts

Later tasks should fill or create these artifacts:

- `docs/final/EVALUATION_REPORT.md` with captured final results.
- `docs/final/E2E_EVIDENCE_CAPTURE_TEMPLATE.md` copied or referenced with
  completed run-specific notes when TASK 015.2 evidence is captured.
- `docs/final/screenshots/` with reviewed screenshot assets, if screenshots
  are captured.
- `docs/final/diagrams/` or markdown diagram files, if diagram tasks create
  source diagrams.
- `docs/final/demo-checklist.md` or equivalent E2E checklist from TASK 015.2.
- `docs/final/release-checklist.md` or equivalent release polish evidence from
  TASK 015.6.

Do not create final evidence artifacts until the evidence has actually been
captured.
