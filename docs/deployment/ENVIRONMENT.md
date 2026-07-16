# Environment Configuration

SPEC-014 separates environment configuration into three profiles: `local-demo`,
`ci-test`, and `production-demo`. The goal is to keep the board demo
reproducible while making production-demo configuration explicit and safe.

This document describes environment profiles for the current Docker Compose
production-demo, readiness, and observability foundations. CI workflows, secret
vaults, and cloud resources are not implemented yet.

## Profiles

### local-demo

Use `backend/.env.example` and `frontend/.env.example` for local development and
the deterministic demo path.

Defaults:

- `APP_ENV=development`
- `DEBUG=true`
- `LLM_PROVIDER=fake`
- `LLM_RUNTIME_ENABLED=false`
- `EMBEDDING_PROVIDER=fake`
- `RAG_ENABLED=false`

No LLM provider key is required. The workflow runtime remains deterministic by
default. Demo seed and knowledge ingestion are explicit commands and are never
run automatically on backend startup:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

For a no-key RAG demo, keep fake embeddings and explicitly enable RAG only for
the backend process that will run the workflow:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
```

Run knowledge ingestion before the workflow if you expect populated evidence.

### ci-test

Use `docs/deployment/.env.ci.example` as a reference for CI jobs and local
quality gates.

CI should use:

- fake/offline LLM defaults
- fake embeddings
- no real provider keys
- no production secrets
- dry-run seed/ingestion checks unless a job explicitly starts local services

Recommended validation commands remain the spec-level gates, such as
`docker-compose config`, backend tests/lint/typecheck, frontend
lint/build/typecheck/tests, demo seed dry-run, and knowledge ingestion dry-run.

### production-demo

Use `docs/deployment/.env.production.example` as a reference for environment
variables injected by the deployment target. Do not copy committed placeholder
values into a live deployment without replacing secrets.

Production-demo configuration must make external URLs explicit:

- backend API origin
- frontend origin
- WebSocket origin
- CORS allowlist
- database, Redis, Qdrant, and MinIO endpoints

The production-demo stack can still run in no-key mode:

```text
LLM_RUNTIME_ENABLED=false
LLM_PROVIDER=fake
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

Real LLM provider keys are optional and are only needed if the deployment
intentionally enables the LLM runtime path and selects a real provider.

Validate the production-demo Compose configuration with:

```bash
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
```

The production-demo Compose file publishes only the frontend and backend ports
by default. Postgres, Redis, Qdrant, and MinIO are internal to the Compose
network.

## Backend Environment Categories

Application and API:

- `APP_NAME`
- `APP_ENV`
- `DEBUG`
- `API_V1_PREFIX`
- `LOG_LEVEL`
- `LOG_FORMAT`
- `LOG_REDACTION_ENABLED`
- `METRICS_ENABLED`
- `METRICS_ROUTE_ENABLED`
- `METRICS_MAX_PATH_LABEL_LENGTH`

Core infrastructure:

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET_NAME`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `BACKEND_PUBLIC_PORT`
- `FRONTEND_PUBLIC_PORT`

Authentication and browser access:

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `BACKEND_CORS_ORIGINS`

LLM provider abstraction:

- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_RUNTIME_ENABLED`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_FALLBACK_ENABLED`
- `LLM_FALLBACK_PROVIDER`
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Embeddings:

- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS`
- `EMBEDDING_BATCH_SIZE`

RAG grounding:

- `RAG_ENABLED`
- `RAG_TOP_K`
- `RAG_MINIMUM_SCORE`
- `RAG_MAX_CONTEXT_CHARS`
- `RAG_EVENT_PAYLOAD_MAX_CHARS`

Readiness:

- `READINESS_TIMEOUT_SECONDS`

Observability defaults:

- `LOG_FORMAT=json`
- `LOG_REDACTION_ENABLED=true`
- `METRICS_ENABLED=true`
- `METRICS_ROUTE_ENABLED=true`
- `METRICS_MAX_PATH_LABEL_LENGTH=120`

Operational metrics are in-process and safe for production-demo visibility.
They are not a replacement for an external telemetry backend and do not include
Prometheus, OpenTelemetry exporters, cost dashboards, token streaming, or
agent-thought streaming.

Only document variables supported by the current settings module here. Trusted
host allowlists, production secret vault settings, and deployment-specific
reverse proxy settings are deferred until the implementation tasks that add
those behaviors.

## Frontend Environment Categories

The frontend only uses public browser-readable variables:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_WS_BASE_URL`

Do not put secrets in `NEXT_PUBLIC_*` variables. They are bundled for browser
use by design.

## Secret Handling

Rules:

- Never commit real secrets, API keys, provider tokens, JWT signing secrets,
  database passwords, object storage secrets, or cloud credentials.
- Use non-working placeholders such as `change-me-in-production` in committed
  examples.
- Inject production-demo secrets through the deployment environment, not source
  control.
- Keep local demo credentials and demo users local-demo only.
- Rotate production-demo secrets and back up stateful service data as an
  operational responsibility.

Production secret vault integration is not implemented yet.

## Production-Demo Safety Checks

Before running a production-demo deployment:

- Replace `JWT_SECRET_KEY` with a strong deployment-injected value.
- Set `DEBUG=false`.
- Set `APP_ENV=production`.
- Use explicit `BACKEND_CORS_ORIGINS`; do not use broad wildcards.
- Verify frontend `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_WS_BASE_URL`
  point to the public backend origin.
- Keep Postgres, Redis, Qdrant, and MinIO private to the deployment network
  unless protected by explicit network and authentication controls.
- Do not expose MinIO or Qdrant admin surfaces publicly without hardening.
- Do not use local demo user credentials for production access.
- Keep LLM provider keys empty unless a real provider is intentionally enabled.
- Confirm the backend does not auto-seed demo workflows or auto-ingest
  knowledge on startup.
- Use `/health` and `/live` for process checks.
- Use `/ready` for bounded dependency checks against Postgres, Redis, Qdrant,
  and MinIO/object storage.
- Protect `GET /api/v1/observability/metrics` with authenticated Admin/Manager
  access plus deployment network controls.
- Keep log redaction enabled unless debugging in a controlled local-only
  environment.

## Optional RAG-Enabled Demo

The RAG demo does not require real LLM keys:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
LLM_PROVIDER=fake
```

Run deterministic knowledge ingestion explicitly:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

With `RAG_ENABLED=true`, workflow runtime grounding can attach bounded
citations from the local demo knowledge base. With `RAG_ENABLED=false`, the
frontend evidence panel should show an honest empty state.
