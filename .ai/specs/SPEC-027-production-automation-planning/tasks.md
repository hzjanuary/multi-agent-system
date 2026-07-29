# SPEC-027 Tasks - Production Automation Planning

## Task List

### TASK 027.1 - Production Automation Inventory And Safety Classification

Status: Planned.

Goal: Turn the SPEC-026 runbooks into an automation inventory with explicit
safety classification.

Scope:

- Inventory automation candidates from production environment, secrets,
  backup/restore, observability, smoke, evaluation, and release docs.
- Classify each candidate as read-only, local validation, dry-run only,
  operator-reviewed, destructive future-only, or blocked.
- Define which candidates can run in CI, locally, or manually only.
- Confirm stable defaults and safety boundaries are unchanged.

Acceptance criteria:

- Automation inventory exists.
- Every candidate has a safety classification.
- Destructive and blocked actions are clearly identified.
- No scripts or behavior changes are implemented in this task unless a future
  TASK 027.1 implementation explicitly scopes them.

Validation:

```bash
git diff --check
git status --short
```

### TASK 027.2 - Read-Only Environment And Secret Scan Script

Status: Implemented / ready for review.

Goal: Implement the first non-destructive automation script for env shape and
tracked-file secret/placeholder scanning.

Scope:

- Add a script under `scripts/ops/`.
- Support `--help`, `--env-file`, `--json`, and `--strict`.
- Check required env keys and forbidden placeholders.
- Check tracked files for known secret markers without printing secret values.
- Confirm local `.env` and `docker-compose.override.yml` are not tracked.
- Keep checks read-only.

Acceptance criteria:

- Script performs no mutation.
- Script prints bounded, redacted output.
- Script exits deterministically.
- Script can run in CI with example env files.
- Tests or help validation are added.

Validation:

```bash
python3 -m unittest scripts.ops.test_validate_environment scripts.ops.test_scan_secrets
python3 -m py_compile scripts/ops/validate_environment.py scripts/ops/scan_secrets.py
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example --skip-compose-check
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example --skip-compose-check --json
python3 scripts/ops/scan_secrets.py --allow-test-placeholders
python3 scripts/ops/scan_secrets.py --allow-test-placeholders --json
git diff --check
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Implemented deliverables:

- `scripts/ops/__init__.py`
- `scripts/ops/validate_environment.py`
- `scripts/ops/scan_secrets.py`
- `scripts/ops/test_validate_environment.py`
- `scripts/ops/test_scan_secrets.py`
- `docs/production/PRODUCTION_AUTOMATION_COMMANDS.md`
- `docs/production/PRODUCTION_ENVIRONMENT_CHECKLIST.md` linked to the
  automation command guide.

Safety properties:

- read-only by default;
- no destructive action;
- no provider call;
- no Telegram call;
- no workflow mutation;
- no backend/frontend/runtime behavior change;
- no Docker/Compose/CI behavior change;
- no secret values printed.

### TASK 027.3 - Production Smoke Aggregator Script

Status: Planned.

Goal: Implement a safe wrapper for deterministic production smoke commands.

Scope:

- Add a script under `scripts/ops/`.
- Run Compose config checks.
- Run Telegram parser benchmark.
- Run demo safety benchmark.
- Optionally run `bash scripts/ci/all-gates.sh`.
- Optionally write JSON summary.
- Keep provider live verification, Telegram live smoke, and authenticated
  metrics checks out of the default path.

Acceptance criteria:

- Required path is no-key and non-mutating.
- Optional all-gates execution is explicit.
- Output is bounded and safe for reviewed evidence.
- No provider, Telegram network, live web, or email call occurs by default.

Validation:

```bash
git diff --check
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

### TASK 027.4 - Backup/Restore Dry-Run Checklist Helper

Status: Planned.

Goal: Implement a dry-run/checklist helper for backup and restore readiness.

Scope:

- Add a script under `scripts/ops/`.
- Print service inventory for Postgres, Redis, MinIO, and Qdrant.
- Check required local command availability where safe.
- Accept `--dry-run` and `--json`.
- Generate a restore checklist from the runbook.
- Do not perform backup, restore, overwrite, migration, volume reset, or backup
  deletion.

Acceptance criteria:

- Helper is dry-run/checklist only.
- No data is modified.
- No backups are deleted.
- No restore is performed.
- Output warns that operator review is required before real operations.

Validation:

```bash
git diff --check
git status --short
```

### TASK 027.5 - Observability Health Summary Script

Status: Planned.

Goal: Implement a non-destructive health summary for running local or
production-demo services.

Scope:

- Add a script under `scripts/ops/`.
- Check `/health`, `/live`, and `/ready` against a configurable backend base
  URL.
- Optionally check frontend route availability.
- Optionally check protected metrics only when a token is provided.
- Redact tokens and Authorization headers.
- Avoid dumping logs or raw payloads.

Acceptance criteria:

- Script is non-mutating.
- Health failures return deterministic exit codes.
- Token values are never printed.
- Metrics check is optional and redacted.
- No external monitoring integration is introduced.

Validation:

```bash
git diff --check
```

Optional when services are running:

```bash
scripts/ops/<health-script> --help
scripts/ops/<health-script> --backend-url http://localhost:8000
```

### TASK 027.6 - Release Snapshot Automation

Status: Planned.

Goal: Implement a release snapshot helper that records repository and
validation metadata for operator review.

Scope:

- Add a script under `scripts/ops/`.
- Record Git branch, commit, tag state, dirty status, and selected validation
  command results.
- Support `--dry-run`, `--json`, and output path selection.
- Default output should be outside the repository or clearly marked for review.
- Do not generate screenshots, PDFs, DOCX, slides, videos, or final thesis
  artifacts.

Acceptance criteria:

- Snapshot output contains no secrets.
- Generated files are not committed by default.
- Dirty working tree is reported honestly.
- Snapshot does not mutate product state.

Validation:

```bash
git diff --check
git status --short
```

### TASK 027.7 - Final Validation And Closeout

Status: Planned.

Goal: Verify SPEC-027 deliverables, update status, and recommend approval or
rejection.

Scope:

- Verify TASK 027.1 through TASK 027.6 deliverables.
- Confirm scripts remain non-destructive by default.
- Confirm CI/local/manual boundaries are documented.
- Confirm no behavior, dependency, Docker/CI, API, database, Telegram,
  provider, outbound email, or final quote changes were introduced without
  approval.
- Run final validation.
- Update `.codex/HANDOFF.md`.

Acceptance criteria:

- SPEC-027 implementation tasks are complete or clearly deferred.
- Automation remains safe, bounded, and non-destructive by default.
- Destructive actions remain blocked or future-only.
- Validation commands pass or failures are reported honestly.

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

## SPEC-027 Planning Deliverables

Implemented in this planning task:

- `.ai/specs/SPEC-027-production-automation-planning/spec.md`
- `.ai/specs/SPEC-027-production-automation-planning/tasks.md`
- `.ai/specs/SPEC_INDEX.md` updated
- `.codex/HANDOFF.md` updated

No automation scripts, backend/frontend behavior, Telegram behavior, provider
behavior, API behavior, database schema/migration, Docker/Compose behavior, CI
behavior, dependency change, outbound send, real email, or final quote behavior
is implemented by the SPEC-027 planning task.

## SPEC-027 Sprint 1 Deliverables

Implemented after planning approval for TASK 027.2:

- read-only production environment validator;
- read-only tracked-file secret scanner;
- unit tests for both scripts;
- production automation commands guide;
- production environment checklist link to the automation guide.

The Sprint 1 scripts remain non-mutating and do not call providers, Telegram,
backend APIs, workflow runtime, outbound email, or live web services.

## Closeout Checklist For Planning

- [x] SPEC-027 spec exists.
- [x] SPEC-027 tasks doc exists.
- [x] SPEC index references SPEC-027 without number conflict.
- [x] Older SPEC-027 CI/CD placeholder is retired or reassigned.
- [x] Handoff points to SPEC-027 as active planning.
- [x] Production automation objective is clear.
- [x] Automation candidates are listed.
- [x] Safety classification is documented.
- [x] Non-destructive-first policy is explicit.
- [x] `scripts/ops/` is proposed as the future script location.
- [x] CLI design is documented.
- [x] CI/local/manual/destructive boundaries are documented.
- [x] Feature flags/envs to respect are documented.
- [x] Non-goals are explicit.
- [x] No product behavior changes are present.
