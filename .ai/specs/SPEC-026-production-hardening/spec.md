# SPEC-026 - Production Hardening

## Status

Sprint 3 implemented / ready for closeout review

## Product Objective

Plan production hardening for Multi-Agent System / Enterprise Multi-Agent OS
after SPEC-001 through SPEC-025 are completed and approved.

SPEC-026 turns the current release-ready demonstration package into a bounded
production-hardening roadmap. It defines what must be reviewed, documented,
validated, and accepted before the project is operated beyond the local
graduation/demo environment.

This is planning only. It does not change backend code, frontend code,
Telegram behavior, provider behavior, API contracts, database models,
migrations, Docker/Compose configuration, CI behavior, dependencies, runtime
defaults, outbound email behavior, or final quotation behavior.

## Current Context

The repository currently includes:

- `v1.0.0-demo-release` tagged and pushed;
- `v1.0.1-maintenance-docs` tagged and pushed;
- SPEC-001 through SPEC-025 completed and approved in the current planning
  context;
- stable deterministic no-key backend demo;
- Violet Operations Console frontend with dashboard, workflow detail, workflow
  list, and Agent Monitor;
- local Telegram intake demo with deterministic parser, optional Ollama
  extraction, sales-style replies, and fail-closed unsupported mixed-item
  handling;
- deterministic catalog expansion;
- reference evidence foundation;
- manual-only Tavily/provider live verification;
- approved outbound communication preview only;
- governance policies;
- deterministic evaluation benchmark runners;
- release-readiness docs and final package docs;
- dependency/security triage with remaining npm audit findings documented and
  deferred.
- production environment, secrets, backup/restore, observability, smoke, and
  closeout runbooks under `docs/production/`.

## Stable Defaults To Preserve

Production hardening must preserve the stable no-key release/demo defaults
unless a future approved implementation spec changes them:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
TELEGRAM_LLM_EXTRACTION_ENABLED=false
TELEGRAM_SALES_REPLY_ENABLED=false
```

Additional default boundaries:

- no real email sending;
- no outbound send endpoint;
- no automatic live provider calls;
- no Telegram live price research;
- no final quote before Manager/Admin approval and explicit resume;
- remaining npm audit findings remain documented/deferred, not silently fixed;
- provider keys and Telegram tokens are never required for deterministic
  validation or CI.

## Scope

SPEC-026 covers planning for:

- production environment validation;
- secrets management;
- deployment hardening;
- database and storage hardening;
- observability and operational response;
- production smoke validation;
- security maintenance carryover;
- demo versus production boundaries;
- final closeout review;
- hardening user stories;
- acceptance criteria;
- implementation task sequence;
- validation and closeout expectations.

## Non-Goals

- No deployment automation changes.
- No Docker/Compose changes.
- No CI changes.
- No dependency upgrades.
- No backend feature changes.
- No frontend feature changes.
- No Telegram behavior changes.
- No provider calls.
- No live web calls.
- No API changes.
- No database models or migrations.
- No production secret vault implementation.
- No enterprise SSO implementation.
- No Kubernetes or Terraform implementation.
- No real email sending.
- No outbound send endpoint.
- No automatic live provider automation.
- No final quote behavior.
- No committed secrets or provider keys.

## Production Environment Validation

Production hardening must define a checklist for reviewing environment
configuration before any production-demo or production-like run.

Required validation areas:

- required backend app settings are present;
- required infrastructure connection strings are present;
- browser-visible frontend settings contain no secrets;
- placeholder secrets such as `change-me-in-production` are forbidden in real
  deployments;
- development defaults such as `DEBUG=true` are forbidden outside local
  development;
- risky features remain disabled unless explicitly approved;
- optional provider settings are empty unless a manual operator intentionally
  configures them;
- production `.env` files remain local and untracked;
- `docs/deployment/.env.production.example` remains placeholders only.

Settings and flags to document:

- `APP_ENV`
- `DEBUG`
- `BACKEND_CORS_ORIGINS`
- `LOG_FORMAT`
- `LOG_REDACTION_ENABLED`
- `METRICS_ENABLED`
- `METRICS_ROUTE_ENABLED`
- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `JWT_SECRET_KEY`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_WS_BASE_URL`
- `LLM_PROVIDER`
- `LLM_RUNTIME_ENABLED`
- `RAG_ENABLED`
- `PRICE_RESEARCH_ENABLED`
- `OUTBOUND_COMMUNICATION_ENABLED`
- `OUTBOUND_SEND_ENABLED`
- `TELEGRAM_LLM_EXTRACTION_ENABLED`
- `TELEGRAM_SALES_REPLY_ENABLED`
- `TAVILY_API_KEY`
- Groq, OpenRouter, Gemini, and Ollama settings already documented by the
  provider setup docs.

## Secrets Management

Production hardening must define a secrets checklist and operator runbook.

Required coverage:

- no committed secrets;
- no committed local `.env` files;
- no committed `docker-compose.override.yml`;
- provider keys must be local/manual unless a future secret-management spec
  introduces managed storage;
- Telegram bot tokens must be local-only and rotated if exposed in logs,
  screenshots, shell history, or chat;
- Tavily keys must be used only for manual provider live verification until a
  future provider automation spec is approved;
- LLM provider keys must not be required for deterministic demo or CI;
- JWT secrets, database passwords, MinIO credentials, and provider keys must
  be unique per environment and never use example placeholders;
- rotation and revocation steps must be documented;
- screenshots, logs, CI output, and demo evidence must be reviewed for tokens,
  cookies, Authorization headers, provider payloads, raw prompts, embeddings,
  vector payloads, and chain-of-thought.

## Deployment Hardening

Production hardening must review the existing production-demo Compose stack
without changing it in this planning slice.

Required coverage:

- `docker compose config` validation;
- production-demo Compose validation with
  `docs/deployment/.env.production.example`;
- production-demo backend/frontend image build validation;
- healthcheck and readiness behavior;
- public port exposure review;
- internal network review;
- startup runbook;
- graceful shutdown runbook;
- rollback plan;
- image rebuild policy;
- data-volume preservation policy;
- explicit statement that current Compose is production-demo, not cloud
  deployment automation, Kubernetes, Terraform, zero-downtime deployment, or a
  managed production platform.

## Database And Storage Hardening

Production hardening must define backup, restore, migration, and data retention
plans for stateful services.

Required coverage:

- Postgres backup and restore planning;
- Postgres migration safety checklist:
  - backup before migration;
  - migration dry-run where practical;
  - rollback decision point;
  - post-migration smoke checks;
- Redis persistence expectations and acceptable data-loss boundaries;
- MinIO object backup and restore planning;
- Qdrant collection export/snapshot planning;
- storage volume inventory;
- restore rehearsal checklist;
- retention and redaction policy placeholders;
- explicit statement that production backup automation is not implemented yet.

## Observability And Operations

Production hardening must define operational readiness checks and incident
response notes.

Required coverage:

- structured JSON logs;
- request IDs;
- log redaction;
- health, liveness, and readiness endpoints;
- protected metrics endpoint;
- metrics safety and bounded labels;
- workflow event/audit trail expectations;
- approval history audit expectations;
- incident triage flow:
  - confirm service health;
  - inspect readiness dependencies;
  - inspect logs by request ID;
  - inspect workflow events and approval history;
  - preserve evidence;
  - avoid modifying data until the failure mode is understood;
- production smoke checklist;
- known warning and limitation register.

## Security Maintenance Carryover

Production hardening must carry forward SPEC-024 and SPEC-025 dependency
policies.

Required coverage:

- current frontend npm audit findings remain documented and deferred;
- `npm audit fix` is not automatic;
- `npm audit fix --force` remains prohibited without a reviewed compatibility
  sprint;
- broad `npm update` remains prohibited;
- Next major, React major, ESLint major, Tailwind major, and TypeScript major
  upgrades require separate compatibility specs;
- backend dependency review should be rerun in an environment with Poetry
  available;
- dependency changes must pass backend, frontend, production-demo, and
  all-gates validation;
- remaining findings are production-hardening backlog items, not hidden
  fixes.

## Demo Versus Production Boundary

Production hardening must make the difference between demo, production-demo,
manual verification, and future production explicit.

Stable demo:

- deterministic;
- no-key;
- no live provider calls;
- no real email;
- no final quote before approval/resume.

Production-demo Compose:

- validates operational packaging;
- uses Docker Compose and placeholder env templates;
- is not a claim of hardened cloud deployment;
- does not include managed secrets, SSO, Kubernetes, Terraform, or production
  backup automation.

Optional manual paths:

- Telegram/Ollama extraction is local and optional;
- Tavily/provider live verification is manual-only;
- RAG is optional and requires explicit ingestion;
- outbound communication remains preview-only.

Future production:

- requires secrets management;
- requires backup/restore procedures;
- requires stronger dependency/security posture;
- requires deployment rollback procedure;
- requires incident response runbook;
- may require enterprise SSO, cloud infrastructure, and external
  observability integration in future specs.

## User Stories

### Operator Deploying Production-Demo

As an operator, I want a production-demo environment checklist so that I can
validate Compose configuration, placeholder replacement, service health,
startup order, shutdown, and rollback before presenting or operating the stack.

Acceptance evidence:

- production environment checklist exists;
- Compose config commands are documented;
- production image build checks are documented;
- startup/shutdown/rollback runbook is documented.

### Developer Verifying Environment Safety

As a developer, I want a checklist for stable defaults and optional feature
flags so that production-hardening work does not accidentally enable provider
calls, outbound send, LLM runtime, price research, RAG, or Telegram extraction.

Acceptance evidence:

- stable defaults are listed;
- optional flags are listed with defaults and risk notes;
- forbidden production placeholders are listed;
- no behavior change is made in the planning task.

### Security Reviewer Checking Secrets And Dependencies

As a security reviewer, I want a secrets and dependency carryover checklist so
that I can confirm no real secrets are committed, local override policy is
clear, provider key policy is clear, and remaining npm audit findings are
tracked through SPEC-024/SPEC-025.

Acceptance evidence:

- secrets checklist exists;
- rotation/revocation checklist is planned;
- dependency maintenance policy references SPEC-024/SPEC-025;
- no unsafe force upgrades are introduced.

### Admin Reviewing Backup/Restore Readiness

As an admin, I want a storage and migration hardening plan so that Postgres,
Redis, MinIO, and Qdrant state can be backed up, restored, and validated before
production-like use.

Acceptance evidence:

- backup/restore plan is scoped for each stateful service;
- migration safety checklist is defined;
- restore rehearsal is included as a future task;
- current lack of production backup automation remains documented.

### Incident Responder Reviewing Logs And Health

As an incident responder, I want operational guidance for health, readiness,
metrics, logs, request IDs, workflow events, and approval history so that
runtime failures can be diagnosed without exposing secrets or altering workflow
state prematurely.

Acceptance evidence:

- observability checklist exists;
- incident response runbook is planned;
- audit trail expectations are documented;
- metrics and logs safety boundaries are documented.

### Release Reviewer Running Production Smoke

As a release reviewer, I want a production smoke checklist so that I can verify
Compose config, deterministic evaluation runners, backend health/readiness,
frontend routes, workflow approval/resume, optional Telegram smoke, optional
provider verification, and safety boundaries without adding automation or
requiring live providers.

Acceptance evidence:

- production smoke checklist exists;
- required deterministic commands are listed;
- optional/manual provider and Telegram paths are separated from required
  checks;
- no provider call, real email, auto-approval, auto-resume, or final quote
  behavior is introduced.

## Acceptance Criteria

- SPEC-026 planning docs exist.
- SPEC-026 is indexed in `.ai/specs/SPEC_INDEX.md`.
- `.codex/HANDOFF.md` points to SPEC-026 as the active production-hardening
  planning slice.
- Production environment validation scope is complete and actionable.
- Secrets checklist scope is complete and actionable.
- Deployment hardening scope is complete and actionable.
- Backup/restore and migration safety scope is complete and actionable.
- Observability/incident response scope is complete and actionable.
- Production smoke checklist is complete and actionable.
- SPEC-026 closeout checklist is complete and actionable.
- Security maintenance carryover from SPEC-024/SPEC-025 is documented.
- Demo versus production boundary is explicit.
- Stable no-key defaults remain documented.
- Optional feature flags remain documented.
- Known limitations and future roadmap are honest.
- Task sequence is small enough for future Codex-executable tasks.
- No backend, frontend, Telegram, API, database, Docker/Compose, CI,
  dependency, provider, outbound email, runtime default, or final quote
  behavior changes are introduced.

## Task Sequence

Future implementation should proceed in small, reviewable tasks:

1. TASK 026.1 - Production Environment Checklist
2. TASK 026.2 - Secrets And Provider Key Runbook
3. TASK 026.3 - Backup/Restore And Migration Safety Plan
4. TASK 026.4 - Observability And Incident Response Runbook
5. TASK 026.5 - Production Smoke Checklist
6. TASK 026.6 - Final Validation And Closeout

Each task must remain documentation/checklist/runbook work unless a future
approved scope explicitly allows implementation changes.

## Validation Strategy

Planning validation:

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

Future implementation task validation should expand to the specific surface
being documented or hardened, but must preserve deterministic/no-key defaults
unless explicitly changed by an approved future spec.

## Implemented Deliverables

- `docs/production/PRODUCTION_ENVIRONMENT_CHECKLIST.md`
- `docs/production/SECRETS_AND_PROVIDER_KEYS_RUNBOOK.md`
- `docs/production/BACKUP_RESTORE_AND_MIGRATION_RUNBOOK.md`
- `docs/production/OBSERVABILITY_AND_INCIDENT_RESPONSE_RUNBOOK.md`
- `docs/production/PRODUCTION_SMOKE_TEST_CHECKLIST.md`
- `docs/production/PRODUCTION_HARDENING_CLOSEOUT.md`

Sprint 3 added production smoke and closeout documentation only. It did not
change product behavior, backend/frontend code, Telegram behavior, APIs,
database schema or migrations, Docker/Compose, CI, dependencies, provider
behavior, runtime defaults, outbound email behavior, or final quote behavior.

## Future Roadmap After SPEC-026

Production-hardening follow-up work should be split into separately approved
specs or tasks, such as:

1. production environment checklist and runbook implementation;
2. secrets management and rotation runbook;
3. backup/restore rehearsal and migration safety docs;
4. incident response and operations runbook;
5. dependency/security compatibility sprints for remaining audit findings;
6. cloud deployment automation only after a dedicated architecture decision;
7. managed secrets, enterprise SSO, and external observability integration;
8. approved outbound send behavior only after a dedicated send-policy spec.

These roadmap items are not implemented by SPEC-026 planning.
