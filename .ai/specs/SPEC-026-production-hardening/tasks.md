# SPEC-026 Tasks - Production Hardening

## Task List

### TASK 026.1 - Production Environment Checklist

Status: Implemented / ready for review.

Goal: Create a production environment validation checklist for production-demo
and future production-like deployments.

Scope:

- Document required backend, frontend, database, Redis, Qdrant, and MinIO
  environment variables.
- Identify forbidden placeholder values for real deployments.
- Document stable deterministic defaults.
- Document optional feature flags and their default disabled state.
- Document production `.env` review procedure.
- Confirm browser-visible `NEXT_PUBLIC_*` values contain no secrets.

Acceptance criteria:

- Checklist covers required env vars.
- Checklist flags forbidden default secrets and placeholders.
- Risky features remain disabled by default.
- Production `.env` review steps are explicit.
- No runtime defaults or Compose behavior are changed.

Validation:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Implementation:

- Added `docs/production/PRODUCTION_ENVIRONMENT_CHECKLIST.md`.
- Documented stable no-key defaults, required environment files, local override
  policy, required production checks, forbidden production defaults, feature
  flag review, pre-deploy checklist, post-deploy smoke checklist, rollback
  readiness checklist, known limitations, and deferred security findings.
- Kept the checklist documentation-only. No runtime defaults, Compose config,
  CI, backend, frontend, Telegram, provider, outbound email, or final quote
  behavior changed.

### TASK 026.2 - Secrets And Provider Key Runbook

Status: Implemented / ready for review.

Goal: Create a secrets-management runbook for local override policy, provider
keys, Telegram tokens, JWT/database/storage secrets, and rotation.

Scope:

- Document no-committed-secret policy.
- Document local `.env` and `docker-compose.override.yml` handling.
- Document Telegram token handling.
- Document Tavily key handling.
- Document Groq, OpenRouter, Gemini, Ollama, and future provider key handling.
- Document JWT secret, database password, and MinIO credential handling.
- Document rotation/revocation checklist.
- Document screenshot/log/evidence review checklist.

Acceptance criteria:

- Runbook distinguishes local-demo credentials from production secrets.
- Provider keys are local/manual unless a future secret-management spec exists.
- Token exposure response steps are documented.
- No keys, tokens, passwords, or local env files are committed.
- No provider automation is introduced.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added `docs/production/SECRETS_AND_PROVIDER_KEYS_RUNBOOK.md`.
- Documented database, JWT/auth, MinIO, Telegram, Tavily, LLM provider,
  future outbound/email provider, and frontend public value secret categories.
- Documented no-committed-secret policy, local ignored override policy,
  rotation schedule, leak response checklist, provider key policy, redaction
  policy, CI policy, future production requirements, and quick review commands.
- Confirmed provider keys remain local/manual and default CI/deterministic demo
  validation requires no live provider keys.
- Kept the runbook documentation-only. No secret store, provider automation,
  outbound send, runtime default, Docker/Compose, CI, backend, frontend, API,
  database, Telegram, or final quote behavior changed.

### TASK 026.3 - Backup/Restore And Migration Safety Plan

Status: Planned.

Goal: Define backup, restore, and migration-safety planning for stateful
services.

Scope:

- Plan Postgres backup and restore procedure.
- Plan Redis persistence expectations and acceptable loss boundaries.
- Plan MinIO backup and restore procedure.
- Plan Qdrant export/snapshot procedure.
- Document storage volume inventory.
- Document migration safety checklist.
- Document restore rehearsal checklist.
- Document data retention and redaction placeholders.

Acceptance criteria:

- Each stateful service has a backup/restore planning section.
- Migration safety steps are explicit.
- Restore rehearsal is included.
- Current lack of production backup automation is documented.
- No database models, migrations, or storage behavior are changed.

Validation:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

### TASK 026.4 - Observability And Incident Response Runbook

Status: Planned.

Goal: Create an operations runbook for logs, request IDs, metrics, readiness,
workflow events, approval history, and incident response.

Scope:

- Document structured log expectations.
- Document request ID usage.
- Document redaction expectations.
- Document `/health`, `/live`, and `/ready` checks.
- Document protected metrics endpoint review.
- Document workflow event and approval audit expectations.
- Document incident triage flow.
- Document evidence preservation and no-secret rules.

Acceptance criteria:

- Observability checklist is actionable.
- Incident response flow is clear.
- Metrics/log safety boundaries are documented.
- Audit trail expectations are documented.
- No external observability vendor integration is added.

Validation:

```bash
git diff --check
git status --short
```

### TASK 026.5 - Production Smoke Checklist

Status: Planned.

Goal: Create a production-demo smoke checklist that verifies environment,
service health, readiness, core workflow behavior, and safety boundaries without
adding automation.

Scope:

- Document Compose config validation.
- Document production image build check.
- Document startup and shutdown checks.
- Document backend health/live/ready checks.
- Document frontend route smoke checks.
- Document login/workflow/approval/resume smoke path.
- Document no-send/no-final-quote checks.
- Document optional manual provider verification as separate from required
  smoke.

Acceptance criteria:

- Smoke checklist uses existing commands only.
- Checklist distinguishes required deterministic checks from optional manual
  checks.
- No live provider calls are required.
- No real email is sent.
- No workflow auto-approval or auto-resume is introduced.

Validation:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Optional validation:

```bash
bash scripts/ci/all-gates.sh
```

### TASK 026.6 - Final Validation And Closeout

Status: Planned.

Goal: Verify SPEC-026 deliverables, update status, and recommend approval or
rejection.

Scope:

- Verify TASK 026.1 through TASK 026.5 deliverables.
- Confirm docs are indexed and cross-linked where appropriate.
- Confirm stable defaults remain unchanged.
- Confirm dependency/security carryover remains documented.
- Confirm no behavior, dependency, Docker/CI, API, database, Telegram,
  provider, outbound email, or final quote changes were introduced.
- Run final planning validation.
- Update `.codex/HANDOFF.md`.

Acceptance criteria:

- SPEC-026 docs are complete and ready for review.
- Production hardening checklist is actionable.
- Secrets checklist is actionable.
- Backup/restore plan is actionable.
- Observability and incident response plan is actionable.
- Production smoke checklist is actionable.
- Validation commands pass or failures are reported honestly.
- No product behavior changes are present.

Validation:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Optional validation:

```bash
bash scripts/ci/all-gates.sh
```

## SPEC-026 Closeout Checklist

Before closing SPEC-026, confirm:

- `LLM_PROVIDER=fake` remains the stable default.
- `LLM_RUNTIME_ENABLED=false` remains the stable default.
- `PRICE_RESEARCH_ENABLED=false` remains the stable default.
- `RAG_ENABLED=false` remains the stable default unless explicitly enabled for
  a RAG demo.
- `OUTBOUND_COMMUNICATION_ENABLED=false` remains the stable default.
- `OUTBOUND_SEND_ENABLED=false` remains the stable default.
- Telegram LLM extraction and sales replies remain optional/local.
- Tavily/provider live verification remains manual-only.
- No provider keys are required in CI.
- No real email sending exists.
- No send endpoint exists.
- No final quote is issued before Manager/Admin approval and explicit resume.
- Remaining npm audit findings remain documented/deferred through
  SPEC-024/SPEC-025.
- No unsafe dependency remediation command was run.
- No Docker/Compose/CI behavior changed.
- No backend/frontend/API/database/Telegram/provider behavior changed.
- No real secrets, provider keys, tokens, cookies, JWTs, or customer data were
  added.
