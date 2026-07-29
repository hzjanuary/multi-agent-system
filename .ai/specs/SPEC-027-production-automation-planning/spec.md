# SPEC-027 - Production Automation Planning

## Status

Planning / Draft

## Product Objective

Plan safe production automation after SPEC-026 Production Hardening.

SPEC-027 turns the SPEC-026 runbooks into a future automation roadmap. The
goal is to define which checks can become non-destructive scripts, which checks
must remain operator-reviewed, and which actions are blocked until a later
approved implementation spec.

This planning task does not implement automation. It does not change product
behavior, backend code, frontend code, Telegram behavior, providers, API
behavior, database schema, migrations, Docker/Compose behavior, CI behavior,
dependencies, runtime defaults, outbound email behavior, or final quote
behavior.

## Context

The repository currently includes:

- `v1.0.0-demo-release` tagged and pushed;
- `v1.0.1-maintenance-docs` tagged and pushed;
- `v1.0.3-production-hardening` tagged and pushed in the current planning
  context;
- SPEC-001 through SPEC-026 completed or ready for closeout review in the
  current planning context;
- stable deterministic no-key demo;
- Telegram intake demo;
- deterministic catalog expansion;
- manual-only provider live verification;
- approved outbound preview only;
- governance docs;
- evaluation benchmark runners;
- dependency/security triage with remaining npm audit findings documented and
  deferred;
- production hardening runbooks under `docs/production/`.

SPEC-026 is runbook-based. SPEC-027 plans the next step: controlled
non-destructive automation that helps operators run those checks consistently
without silently changing systems or weakening safety boundaries.

## Stable Defaults And Boundaries To Preserve

Production automation must preserve these stable defaults unless a future
approved implementation spec changes them:

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

Safety boundaries:

- no real email sending;
- no outbound send endpoint;
- no automatic live provider calls;
- no Telegram live price research;
- no final quote before Manager/Admin approval and explicit resume;
- no automatic approval;
- no automatic resume;
- no production data deletion;
- no automatic production migrations;
- no automatic rollback;
- no backup deletion;
- no secret printing;
- no committed provider keys, Telegram tokens, passwords, JWTs, cookies,
  Authorization headers, raw prompts, provider payloads, embeddings, vector
  payloads, chain-of-thought, or real customer data;
- remaining npm audit findings remain documented/deferred, not silently fixed.

## Automation Objective

Plan automation that converts SPEC-026 checklists into safe scripts and command
wrappers.

Automation should improve repeatability for release reviewers and operators
while staying non-destructive by default. Every future script must make its
scope visible, redact sensitive values, use deterministic exit codes, and
separate required no-key validation from optional manual/live checks.

## Automation Candidates

### Production Environment Validation Script

Planned purpose:

- read a selected env file;
- check required keys are present;
- detect placeholder values for production-like runs;
- confirm browser-visible `NEXT_PUBLIC_*` values contain no secrets;
- summarize stable defaults and risky feature flags.

Initial behavior must be read-only and non-mutating.

### Secret Placeholder And Tracked-File Scan

Planned purpose:

- scan tracked files for known secret variable names and suspicious patterns;
- confirm `docker-compose.override.yml` is untracked;
- warn on local `.env` files if they appear in tracked paths;
- print bounded filenames/line numbers only;
- never print discovered secret values.

### Compose Config Validation Wrapper

Planned purpose:

- run `docker compose config`;
- run production-demo Compose config with
  `docs/deployment/.env.production.example`;
- optionally accept `--env-file` for operator-reviewed local validation;
- never push images or deploy cloud resources.

### Production Smoke Command Runner

Planned purpose:

- aggregate required deterministic checks from
  `docs/production/PRODUCTION_SMOKE_TEST_CHECKLIST.md`;
- run evaluation benchmarks;
- optionally run `bash scripts/ci/all-gates.sh`;
- summarize pass/fail status in text and JSON.

### Backend Health/Readiness Smoke Script

Planned purpose:

- check `/health`, `/live`, and `/ready`;
- optionally check protected metrics only when an operator supplies a token;
- redact tokens and Authorization headers;
- return deterministic exit codes for health failures.

### Frontend Build/Static Smoke Wrapper

Planned purpose:

- delegate to `bash scripts/ci/frontend-gate.sh`;
- optionally check configured public frontend routes when a base URL is
  supplied;
- avoid browser automation unless a future frontend smoke spec approves it.

### Evaluation Runner Aggregation

Planned purpose:

- run `scripts/evaluation/evaluate_telegram_parser.py`;
- run `scripts/evaluation/evaluate_demo_safety.py`;
- optionally write a combined JSON summary outside the repository by default;
- keep benchmarks no-key, no-network, no-database, and deterministic.

### Backup Dry-Run / Checklist Helper

Planned purpose:

- inspect planned backup targets and required command availability;
- print operator checklist for Postgres, Redis, MinIO, and Qdrant;
- never perform a backup unless a future task explicitly approves a safe
  operator-confirmed command;
- never delete old backups.

### Restore Checklist Helper

Planned purpose:

- generate restore order and validation checklist from existing runbooks;
- require explicit operator input for environment/backup identity;
- never restore data automatically in Sprint 1.

### Migration Preflight Helper

Planned purpose:

- report current Alembic revision where safe;
- check migration file presence;
- require backup confirmation;
- never run production migrations automatically;
- never downgrade or rollback automatically.

### Observability Health Summary Script

Planned purpose:

- summarize service health/readiness endpoints;
- optionally check metrics with a redacted token;
- print request IDs/status codes where available;
- avoid exposing logs, secrets, stack traces, raw provider payloads, raw prompts,
  embeddings, vector payloads, or chain-of-thought.

### Release Snapshot Script

Planned purpose:

- record Git branch, commit, tag state, dirty status, and validation command
  results;
- summarize docs/spec status;
- write a bounded release snapshot file outside the repository by default or to
  a clearly reviewed path;
- never generate screenshots, PDFs, DOCX, slides, videos, or final thesis
  artifacts.

## Safety Classification

| Category | Examples | Allowed in first implementation sprint |
| --- | --- | --- |
| Read-only safe checks | env key presence, tracked-file scan, Compose config, Git status, docs link inventory | Yes |
| Local validation commands | evaluation runners, backend/frontend/all gates, health checks against local services | Yes, when explicitly invoked |
| Dry-run only helpers | backup checklist, restore checklist, migration preflight, release snapshot preview | Yes, dry-run/checklist only |
| Operator-reviewed commands | production image build, provider live smoke, authenticated metrics check, explicit local smoke | Not by default; require flags and docs |
| Destructive commands, future only | data deletion, volume reset, restore overwrite, production migration, rollback, backup pruning | No |
| Blocked automation | outbound send, final quote issuance, auto-approval, auto-resume, live provider calls by default, secret printing | No |

## Non-Destructive-First Policy

Sprint 1 of SPEC-027 implementation must only implement read-only or
non-destructive automation.

Rules:

- backup/restore automation starts as dry-run/checklist only;
- no production data deletion;
- no automatic migrations against production;
- no automatic rollback unless a future approved spec defines policy,
  confirmation, evidence preservation, and recovery;
- no backup deletion or pruning automation;
- no secret printing;
- no live provider calls by default;
- no outbound send automation;
- no final quote behavior;
- no Telegram live price research;
- no runtime-default changes.

## Script Location Proposal

Use `scripts/ops/` for SPEC-027 production automation.

Rationale:

- `scripts/ci/` already owns CI gate wrappers;
- `scripts/demo/` owns local demo bridges and provider smoke utilities;
- `scripts/final/` owns graduation/final validation helpers;
- production automation crosses release, environment, smoke, observability, and
  storage runbook boundaries, so `scripts/ops/` is the clearest neutral home.

Future script examples:

```text
scripts/ops/validate-production-env.sh
scripts/ops/scan-release-secrets.sh
scripts/ops/production-smoke.sh
scripts/ops/health-summary.sh
scripts/ops/backup-checklist.sh
scripts/ops/migration-preflight.sh
scripts/ops/release-snapshot.sh
```

Do not add these scripts in this planning task.

## CLI Design

Future scripts should share these behaviors:

- `--help` prints usage and safety boundaries;
- `--dry-run` is available for any script that might later perform an
  operator-reviewed action;
- `--json` emits bounded machine-readable summaries;
- `--strict` treats warnings as failures where appropriate;
- `--env-file <path>` accepts an operator-selected env file for validation;
- `--base-url <url>` is used for health/frontend smoke scripts instead of
  hardcoding production hosts;
- deterministic exit codes:
  - `0` pass;
  - `1` validation failure;
  - `2` unsafe configuration or blocked action;
  - `3` missing local dependency or unavailable service;
- no secrets printed;
- safe redaction for key names and values;
- clear `PASS`, `WARN`, `FAIL`, and `SKIP` output;
- output should be bounded and suitable for release evidence after review.

## Validation And CI Boundary

### CI-Safe Candidates

These can run in CI after implementation, if they remain no-key and
non-mutating:

- tracked-file secret placeholder scan;
- `docker compose config`;
- production-demo Compose config with placeholder env;
- deterministic evaluation runner aggregation;
- docs/spec status inventory;
- script `--help` tests;
- dry-run release snapshot generation to a temporary path.

### Local-Only Candidates

These should remain local/manual because they depend on running services or
operator-selected environments:

- backend `/health`, `/live`, `/ready` smoke against a local or
  production-demo stack;
- frontend route smoke against a running frontend;
- authenticated metrics check;
- optional full `bash scripts/ci/all-gates.sh` when it builds images;
- production image build validation.

### Docker-Required Candidates

- Compose config validation;
- backend/frontend/all gates;
- production-demo image build;
- migration preflight if it inspects containerized Alembic state;
- service health checks against a Compose stack.

### Env-Review-Required Candidates

- validation against any non-example production env file;
- provider live verification;
- backup/restore checklist using real paths;
- migration preflight against a production-like database;
- release snapshot intended for public or evaluator submission.

### Must Never Run Automatically

- production database migration;
- restore overwrite;
- volume deletion/reset;
- backup deletion/pruning;
- provider live calls;
- outbound send;
- final quote issuance;
- auto-approval;
- auto-resume;
- secret rotation;
- cloud resource creation or teardown.

## User Stories

### Operator Running Pre-Deploy Checks

As an operator, I want a single non-destructive pre-deploy command so that I can
validate env shape, Compose config, stable defaults, and known safety
boundaries before starting a production-demo stack.

Acceptance evidence:

- environment validation script is planned;
- Compose config wrapper is planned;
- risky flags and placeholders are checked;
- no mutation is performed.

### Developer Validating Release Readiness

As a developer, I want an automation wrapper for deterministic release checks
so that parser benchmark, demo safety benchmark, Compose config, and optional
all-gates status can be summarized consistently.

Acceptance evidence:

- production smoke aggregator is planned;
- evaluation runner aggregation is planned;
- JSON output and deterministic exit codes are defined.

### Security Reviewer Checking Secrets

As a security reviewer, I want a tracked-file scan that detects suspicious
secret markers without printing secret values.

Acceptance evidence:

- secret scan scope is planned;
- no-secret printing and redaction requirements are defined;
- CI-safe boundary is documented.

### Admin Reviewing Backup/Restore Readiness

As an admin, I want dry-run backup and restore checklist helpers so that I can
verify required services, target paths, and recovery order without modifying
data.

Acceptance evidence:

- backup dry-run/checklist helper is planned;
- restore checklist helper is planned;
- destructive restore and backup deletion are blocked.

### Incident Responder Running Health Summary

As an incident responder, I want a health summary command so that I can quickly
see backend health, readiness, frontend availability, and safe metrics status
without exposing secrets.

Acceptance evidence:

- observability health summary script is planned;
- token redaction and safe output rules are defined;
- no logs or raw payloads are dumped.

### Maintainer Preparing A Release Tag

As a maintainer, I want a release snapshot command so that I can capture branch,
commit, tag, dirty status, and validation summaries for review.

Acceptance evidence:

- release snapshot script is planned;
- output location and evidence safety rules are defined;
- generated artifacts are not committed by default.

## Acceptance Criteria

- SPEC-027 spec and tasks docs exist.
- SPEC index references SPEC-027 without number conflict.
- Handoff points to SPEC-027 as the current production automation planning
  slice.
- Production automation objective is clear.
- Automation candidates are listed.
- Safety classification is documented.
- Non-destructive-first policy is explicit.
- Script location convention is proposed.
- CLI behavior is defined.
- CI/local/manual/destructive boundaries are documented.
- User stories are included.
- Stable feature flags and envs to respect are documented.
- Non-goals are explicit.
- Future task sequence is small enough for Codex-executable tasks.
- No automation is implemented in this planning task.
- No product behavior changes are introduced.

## Task Sequence

Future implementation should proceed in small, reviewable tasks:

1. TASK 027.1 - Production Automation Inventory And Safety Classification
2. TASK 027.2 - Read-Only Environment And Secret Scan Script
3. TASK 027.3 - Production Smoke Aggregator Script
4. TASK 027.4 - Backup/Restore Dry-Run Checklist Helper
5. TASK 027.5 - Observability Health Summary Script
6. TASK 027.6 - Release Snapshot Automation
7. TASK 027.7 - Final Validation And Closeout

Each implementation task must remain non-destructive unless a future approved
scope explicitly authorizes a stronger action.

## Feature Flags And Envs To Respect

Future automation must detect and respect:

- `LLM_PROVIDER`
- `LLM_RUNTIME_ENABLED`
- `PRICE_RESEARCH_ENABLED`
- `EMBEDDING_PROVIDER`
- `RAG_ENABLED`
- `OUTBOUND_COMMUNICATION_ENABLED`
- `OUTBOUND_SEND_ENABLED`
- `TELEGRAM_LLM_EXTRACTION_ENABLED`
- `TELEGRAM_SALES_REPLY_ENABLED`
- `TAVILY_API_KEY`
- Groq, OpenRouter, Gemini, Ollama, and other provider API keys already
  documented in provider/secrets docs;
- database/storage envs already documented in
  `docs/production/PRODUCTION_ENVIRONMENT_CHECKLIST.md`;
- frontend public envs `NEXT_PUBLIC_API_BASE_URL` and
  `NEXT_PUBLIC_WS_BASE_URL`.

Automation must never print values for keys, tokens, passwords, cookies,
Authorization headers, or provider secrets.

## Non-Goals

- No code implementation in this planning task.
- No automation scripts in this planning task.
- No Docker/Compose changes.
- No CI changes.
- No dependency changes.
- No backend feature changes.
- No frontend feature changes.
- No Telegram behavior changes.
- No provider behavior changes.
- No API behavior changes.
- No database models or migrations.
- No automatic production migration.
- No automatic backup deletion.
- No automatic restore.
- No automatic rollback.
- No production data deletion.
- No production secret vault implementation.
- No cloud deployment automation.
- No Kubernetes or Terraform implementation.
- No real email sending.
- No outbound send endpoint.
- No live provider automation.
- No final quote behavior.
- No secrets added.

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

Future implementation tasks must add focused tests or script help checks for
the specific automation they introduce.
