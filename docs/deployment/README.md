# Deployment Documentation

SPEC-014 tracks production-demo deployment and observability work. This folder
contains environment planning artifacts only; it does not add deployment
infrastructure by itself.

Use these files when preparing a deployable demo stack:

- `RUNBOOK.md` is the production-demo operator runbook.
- `DEMO_PACKAGE.md` is the board-demo packaging checklist and walkthrough.
- `SMOKE_CHECKS.md` documents automated and manual smoke checks.
- `BACKUP_RESTORE.md` documents honest backup, restore, and rollback basics.
- `TROUBLESHOOTING.md` covers common deployment and board-demo failures.
- `ENVIRONMENT.md` explains the `local-demo`, `ci-test`, and
  `production-demo` environment profiles.
- `.env.production.example` is a placeholder-only production-demo template for
  backend and frontend environment injection.
- `.env.ci.example` is a no-key CI/test template for deterministic validation.
- `../../docker-compose.prod.yml` defines the additive production-demo Compose
  stack for backend, frontend, Postgres, Redis, Qdrant, and MinIO.

Do not commit real `.env` files, provider API keys, JWT secrets, database
passwords, object storage credentials, or cloud credentials.

Recommended production-demo order:

```bash
bash scripts/ci/compose-gate.sh
docker-compose -f docker-compose.prod.yml --env-file .env.production.local build backend frontend
docker-compose -f docker-compose.prod.yml --env-file .env.production.local up -d
COMPOSE_ENV_FILE=.env.production.local bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

See `RUNBOOK.md` before using these commands for a board demo. The runbook also
covers explicit migrations, demo seed, and knowledge ingestion.

## Production-Demo Compose

Validate the production-demo Compose file without starting services:

```bash
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
```

Build the production-demo application images:

```bash
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend
```

The production-demo stack is additive. It does not replace the local
`docker-compose.yml` developer stack and it does not run demo seeding or
knowledge ingestion automatically.

By default, only the frontend and backend ports are published. Postgres, Redis,
Qdrant, and MinIO stay on the internal Compose network. Do not expose stateful
service ports publicly without explicit network and credential hardening.

## Health And Readiness

Backend process checks:

- `GET /health` stays lightweight and reports that the app process responds.
- `GET /live` stays lightweight and reports liveness.
- `GET /ready` checks required infrastructure: Postgres, Redis, Qdrant, and
  MinIO/object storage.

The Compose backend healthcheck remains on `/health` so dependency startup does
not cause backend container restart loops. Use `/ready` for deployment
readiness gates and diagnostics. Readiness checks are bounded by
`READINESS_TIMEOUT_SECONDS` and never run migrations, demo seed, knowledge
ingestion, Qdrant upserts, MinIO writes, LLM calls, or email sending.

## Observability And Metrics

Backend operational observability is vendor-neutral:

- logs are structured JSON by default with `LOG_FORMAT=json`
- request IDs are propagated through the `X-Request-ID` response header and
  included in request completion logs
- log redaction is enabled by default with `LOG_REDACTION_ENABLED=true`
- request logs include method, bounded route/path label, status code, and
  duration
- request logs do not include request bodies, response bodies, authorization
  headers, cookies, raw prompts, raw documents, raw embeddings, provider
  payloads, or secrets

The backend exposes bounded in-process metrics at:

```text
GET /api/v1/observability/metrics
```

The route requires authentication and is limited to Admin and Manager roles.
The response includes uptime, process start time, counters, and HTTP request
duration summaries by low-cardinality labels. It does not expose environment
variables, headers, request bodies, raw embeddings, vector payloads, prompts,
provider payloads, or secrets.

This task does not add Prometheus, OpenTelemetry exporters, telemetry vendor
SDKs, cost dashboards, token streaming, or agent-thought streaming. Protect the
metrics route with deployment network controls or a reverse proxy in real
deployments.

## CI Quality Gates

SPEC-014 provides a repository CI workflow at `.github/workflows/ci.yml` and
matching local scripts under `scripts/ci/`.

The CI gate runs with fake/no-key defaults and does not deploy, push images,
call real LLM providers, call external SaaS providers, or require cloud
credentials. It validates:

- local Docker Compose config
- production-demo Docker Compose config
- backend-test image build
- Alembic upgrade
- backend pytest, Ruff, Black, and MyPy
- demo seed dry-run JSON
- knowledge ingestion dry-run JSON
- frontend install, lint, production build, typecheck, and tests
- production-demo backend/frontend image build
- `git diff --check`

Frontend build and typecheck intentionally run serially to avoid races around
generated `.next/types`.

Run the local gates from the repository root:

```bash
bash scripts/ci/compose-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
```

`backend-gate.sh` starts Postgres, Redis, Qdrant, and MinIO for validation. It
does not remove volumes and does not clean up services unless explicitly
requested:

```bash
BACKEND_GATE_CLEANUP=1 bash scripts/ci/backend-gate.sh
```

Manual cleanup without deleting volumes:

```bash
docker-compose down --remove-orphans
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example down --remove-orphans
```

## Production-Demo Smoke Script

`scripts/deployment/smoke-prod-demo.sh` checks a running production-demo stack
using existing endpoints only. By default it does not start services, seed demo
data, ingest knowledge, call real LLM providers, or mutate application state.

Default checks:

- backend `/health`
- backend `/live`
- frontend root page

Run against an already-running stack:

```bash
bash scripts/deployment/smoke-prod-demo.sh
```

Start the production-demo Compose stack first:

```bash
bash scripts/deployment/smoke-prod-demo.sh --start
```

Include readiness checks when dependencies are expected to be healthy:

```bash
bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

The script supports URL and Compose file overrides:

```bash
BACKEND_BASE_URL=http://localhost:8000 \
FRONTEND_BASE_URL=http://localhost:3000 \
COMPOSE_FILE=docker-compose.prod.yml \
COMPOSE_ENV_FILE=docs/deployment/.env.production.example \
bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

For the full smoke checklist, including manual browser and metrics checks, see
`SMOKE_CHECKS.md`.
