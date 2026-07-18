# Final Quality Gate

This document lists the final validation commands for graduation release
readiness. Commands use fake/no-key defaults and do not require live LLM keys
or external provider services.

Run commands from the repository root unless a command explicitly changes
directory.

## Required Commands

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
bash scripts/ci/compose-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend
bash scripts/deployment/smoke-prod-demo.sh --help
bash scripts/final/e2e-demo-validation.sh --help
bash scripts/final/final-quality-gate.sh --help
bash scripts/final/final-quality-gate.sh
git diff --check
git diff --cached --check
```

The backend gate already covers:

```bash
docker-compose build backend-test
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
```

The frontend gate already covers these commands serially:

```bash
cd frontend
npm install
npm run lint
npm run build
npm run typecheck
npm test
```

Running `npm run build` and `npm run typecheck` serially avoids the known
`.next/types` race.

## Optional E2E Commands

These commands mutate local-demo data and must be run only when the local demo
environment is intentionally prepared:

```bash
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-rag
bash scripts/deployment/smoke-prod-demo.sh --start --include-ready
```

Do not run optional E2E commands against production data. They are for
local-demo or board-demo environments only.

## No-Secret Scan

Use a focused scan before release. Review matches manually because docs may
include intentional placeholder or warning language.

```bash
rg -n "sk-|AIza|ghp_|xox[baprs]-|BEGIN (RSA|OPENSSH|PRIVATE)|password=|api[_-]?key|secret" . \
  --glob "!frontend/node_modules/**" \
  --glob "!frontend/.next/**" \
  --glob "!backend/.venv/**" \
  --glob "!harness.db"
```

Expected result: no real provider keys, JWT secrets, access tokens, cookies,
private keys, or production passwords in tracked files. Placeholder text and
security warnings are acceptable only after manual review.

## Unsupported-Claim Scan

Use a focused scan for phrases that could imply unimplemented production
capabilities. Review matches manually because limitations docs intentionally
mention deferred scope.

```bash
rg -n "cloud deployed|Kubernetes implemented|Terraform implemented|secret vault implemented|enterprise SSO implemented|production email implemented|upload UI implemented|production OCR implemented|zero-downtime|token streaming implemented|agent thought streaming implemented" docs README.md backend/README.md frontend/README.md scripts
```

Expected result: no unsupported completed-capability claims. Deferred,
future-work, limitation, or "do not claim" language is acceptable.

## Final Gate Wrapper

The wrapper script delegates to existing gates and remains non-deploying and
non-mutating by default:

```bash
bash scripts/final/final-quality-gate.sh
```

Use this only as a convenience wrapper. If it fails, run the underlying command
shown in the output and record the failure in the evidence report.

