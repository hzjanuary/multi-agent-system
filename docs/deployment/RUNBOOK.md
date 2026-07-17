# Production-Demo Deployment Runbook

This runbook packages the current board-demo stack for a single-host
production-demo deployment. It is intentionally bounded: Docker Compose starts
the services, operators run migrations, demo seed, and knowledge ingestion
explicitly, and no cloud deployment or secret vault automation is included.

## Prerequisites

- Docker and Docker Compose.
- Git.
- Bash for the repository scripts. On Windows, use Git Bash if `bash` opens WSL
  without a configured distro.
- Node/npm only when running frontend gates outside Docker.
- No real LLM keys are required for the default demo.
- Real provider keys are optional and only needed when explicitly enabling a
  real LLM provider/runtime.

Never commit real `.env` files, JWT secrets, provider keys, database
passwords, object storage credentials, or cloud credentials.

## Environment Setup

Create an untracked deployment env file from the placeholder template:

```bash
cp docs/deployment/.env.production.example .env.production.local
```

Replace the production-demo placeholders in `.env.production.local`:

- `JWT_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- public frontend/backend URLs and CORS origins

Keep the no-key defaults for the stable board demo:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

For the optional RAG evidence demo, still no real LLM key is required:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

Align browser URLs before starting the stack:

- `NEXT_PUBLIC_API_BASE_URL` must point to the public backend HTTP origin.
- `NEXT_PUBLIC_WS_BASE_URL` must point to the public backend WebSocket origin.
- `BACKEND_CORS_ORIGINS` must include the frontend origin.

## Build And Start

Set the env file path once:

```bash
ENV_FILE=.env.production.local
```

Validate Compose first:

```bash
bash scripts/ci/compose-gate.sh
docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" config
```

Build application images:

```bash
docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" build backend frontend
```

Start the production-demo stack:

```bash
docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up -d
docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" ps
```

Run process-level smoke checks:

```bash
COMPOSE_ENV_FILE="$ENV_FILE" bash scripts/deployment/smoke-prod-demo.sh
```

When dependencies are expected to be ready, include `/ready`:

```bash
COMPOSE_ENV_FILE="$ENV_FILE" bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

The smoke script does not seed demo data, ingest knowledge, call real LLM
providers, or mutate application state.

## Database And Demo Preparation

Migrations, demo seed, and knowledge ingestion are explicit operator actions.
The application does not auto-run them on startup.

For local validation and CI-style preparation, use the backend-test target:

```bash
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Dry-run checks:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
```

For a production-demo stack using a different database volume or credentials,
run the same Alembic, seed, and ingestion commands from an operator-controlled
one-off container pointed at that stack's environment. One template is:

```bash
set -a
. ./.env.production.local
set +a

PROD_NETWORK="${COMPOSE_PROJECT_NAME:-graduation-project-2}_enterprise-os-internal"

docker-compose run --rm --network "$PROD_NETWORK" \
  -e DATABASE_URL -e REDIS_URL -e QDRANT_URL \
  -e MINIO_ENDPOINT -e MINIO_ACCESS_KEY -e MINIO_SECRET_KEY -e MINIO_BUCKET_NAME \
  backend-test alembic upgrade head

docker-compose run --rm --network "$PROD_NETWORK" \
  -e DATABASE_URL -e REDIS_URL -e QDRANT_URL \
  -e MINIO_ENDPOINT -e MINIO_ACCESS_KEY -e MINIO_SECRET_KEY -e MINIO_BUCKET_NAME \
  backend-test python -m app.demo.seed --confirm-local-demo

docker-compose run --rm --network "$PROD_NETWORK" \
  -e DATABASE_URL -e REDIS_URL -e QDRANT_URL \
  -e MINIO_ENDPOINT -e MINIO_ACCESS_KEY -e MINIO_SECRET_KEY -e MINIO_BUCKET_NAME \
  backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Keep this as an operator step; the current production-demo runtime image does
not auto-migrate, auto-seed, or auto-ingest.

Demo credentials are local-demo/board-demo only. Do not treat them as
production users.

## Board Demo Script

1. Open the frontend URL.
2. Login as Manager or Admin.
3. Show the workflow dashboard and seeded procurement workflows.
4. Open the primary procurement workflow.
5. Run the workflow to `WAITING_APPROVAL`.
6. Show persisted timeline events.
7. If `RAG_ENABLED=true`, show:
   - evidence/citations panel
   - knowledge search/catalog
   - `knowledge.grounding.*` timeline events
8. Submit approval with a short comment.
9. Resume the workflow explicitly.
10. Show `COMPLETED` state and final timeline.
11. Optionally login as Viewer and show forbidden approval/resume behavior.
12. Optionally check metrics as Admin/Manager.

Use no-key mode for the default demo. Real-provider LLM mode is optional and
should be introduced only when the variability is acceptable for the audience.

## Observability

Backend endpoints:

- `GET /health`: lightweight process health.
- `GET /live`: lightweight process liveness.
- `GET /ready`: dependency readiness for Postgres, Redis, Qdrant, and MinIO.
- `GET /api/v1/observability/metrics`: Admin/Manager-only in-process metrics.

Request logs include request IDs and safe structured fields. Logs and metrics
must not include authorization headers, cookies, tokens, API keys, raw prompts,
raw documents, raw embeddings, provider payloads, chain-of-thought, request
bodies, or response bodies.

Not included in SPEC-014:

- external telemetry vendor
- Prometheus scrape configuration
- OpenTelemetry exporter
- provider cost dashboard
- token streaming
- agent-thought streaming

## CI And Local Gates

The repository CI workflow mirrors these local gates:

```bash
bash scripts/ci/compose-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
```

The gates use fake/no-key defaults, run frontend build and typecheck serially,
and do not deploy or push images.

## Stop And Cleanup

Stop the production-demo stack without deleting volumes:

```bash
docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" down --remove-orphans
```

Do not delete named volumes unless a reset is intentional and the data has been
backed up.

## Related Docs

- `docs/deployment/DEMO_PACKAGE.md`
- `docs/deployment/SMOKE_CHECKS.md`
- `docs/deployment/BACKUP_RESTORE.md`
- `docs/deployment/TROUBLESHOOTING.md`
- `docs/deployment/ENVIRONMENT.md`
- `docs/demo/DEMO_RUNBOOK.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
