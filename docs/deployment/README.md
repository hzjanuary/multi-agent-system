# Deployment Documentation

SPEC-014 tracks production-demo deployment and observability work. This folder
contains environment planning artifacts only; it does not add deployment
infrastructure by itself.

Use these files when preparing a deployable demo stack:

- `ENVIRONMENT.md` explains the `local-demo`, `ci-test`, and
  `production-demo` environment profiles.
- `.env.production.example` is a placeholder-only production-demo template for
  backend and frontend environment injection.
- `.env.ci.example` is a no-key CI/test template for deterministic validation.
- `../../docker-compose.prod.yml` defines the additive production-demo Compose
  stack for backend, frontend, Postgres, Redis, Qdrant, and MinIO.

Do not commit real `.env` files, provider API keys, JWT secrets, database
passwords, object storage credentials, or cloud credentials.

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
