# Production Automation Commands

## Purpose

This guide documents the first SPEC-027 read-only automation commands for
production-readiness review. The commands validate environment shape and scan
tracked files for secret risks without changing application state.

These commands do not start services, run migrations, seed data, call Telegram,
call LLM providers, call Tavily or live web providers, send email, approve
workflows, resume workflows, or create final quote behavior.

## Safety Contract

All scripts in this guide must preserve these properties:

- `deterministic=true`
- `destructive_actions=false`
- `provider_calls=false`
- `secrets_printed=false`

The stable defense/demo defaults remain:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
TELEGRAM_LLM_EXTRACTION_ENABLED=false
TELEGRAM_SALES_REPLY_ENABLED=false
```

Optional feature flags may be enabled for reviewed local demos, but the
automation reports risky deviations instead of silently treating them as the
safe baseline.

## Environment Validation

Run the read-only environment check from the repository root:

```bash
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example
```

JSON output:

```bash
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example \
  --json
```

Strict mode:

```bash
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example \
  --strict
```

Skip Compose config checks when Docker is unavailable:

```bash
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example \
  --skip-compose-check
```

The script checks:

- env file existence and parseability;
- stable no-key defaults;
- risky feature flag deviations;
- secret-bearing keys without printing values;
- tracked `docker-compose.override.yml` state;
- optional `docker compose config` and production-demo Compose config.

Risky flags warn in default mode and fail in strict mode:

- `LLM_RUNTIME_ENABLED=true`
- `PRICE_RESEARCH_ENABLED=true`
- `OUTBOUND_SEND_ENABLED=true`
- `RAG_ENABLED=true`
- `TELEGRAM_LLM_EXTRACTION_ENABLED=true`

## Tracked-File Secret Scan

Run the tracked-file secret scan from the repository root:

```bash
python3 scripts/ops/scan_secrets.py --allow-test-placeholders
```

JSON output:

```bash
python3 scripts/ops/scan_secrets.py --allow-test-placeholders --json
```

Strict mode:

```bash
python3 scripts/ops/scan_secrets.py --allow-test-placeholders --strict
```

The scanner:

- scans tracked files from `git ls-files`;
- skips `.git`, `node_modules`, `.venv`, build artifacts, coverage output, and
  cache directories;
- warns about local sensitive files such as `.env`,
  `backend/.env`, `frontend/.env.local`, and
  `docker-compose.override.yml`;
- detects suspicious Telegram tokens, API keys, bearer tokens, JWT-like values,
  private key markers, password assignments, provider API keys, MinIO secrets,
  and JWT secrets;
- prints redacted path/line summaries only;
- does not scan untracked local env files by default.

`--allow-test-placeholders` allows documented fake/demo/test/example values and
test fixtures. It does not permit real provider keys, Telegram tokens, JWTs, or
private keys in tracked files.

## Expected Release Review Sequence

Use this minimum read-only automation sequence before a release review:

```bash
python3 -m unittest scripts.ops.test_validate_environment scripts.ops.test_scan_secrets
python3 -m py_compile scripts/ops/validate_environment.py scripts/ops/scan_secrets.py
python3 scripts/ops/validate_environment.py \
  --env-file docs/deployment/.env.production.example
python3 scripts/ops/scan_secrets.py --allow-test-placeholders
git diff --check
git status --short
```

When Docker is available, also run:

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

## Interpreting Results

`PASS` means the script found no blocking issue for the selected mode.

`WARN` means operator review is needed. Examples include populated
secret-bearing env keys, optional feature flags enabled outside the stable
baseline, or local sensitive files present but untracked.

`FAIL` means the selected command found a blocking issue. Strict mode turns
risky deviations and suspicious findings into failures.

All secret-like values are redacted. If a finding points at a real token or key,
remove it from the tracked file and rotate the credential before release.

## Non-Goals

These scripts intentionally do not implement:

- production deployment automation;
- cloud provisioning;
- Kubernetes or Terraform;
- backup or restore execution;
- migration execution;
- live provider verification;
- Telegram polling;
- Tavily or web search calls;
- outbound email sending;
- workflow creation, approval, resume, or final quotation.

