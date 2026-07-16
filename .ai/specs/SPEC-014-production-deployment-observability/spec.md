# SPEC-014 - Production Deployment and Observability

## Status

Draft

## Context

Enterprise Multi-Agent OS now has a complete local/demo product path:

- SPEC-001 provides the FastAPI backend, Dockerfile, Docker Compose services,
  structured logging foundation, request id middleware, and `/`, `/health`,
  `/ready`, and `/live` endpoints.
- SPEC-004 provides Redis, Qdrant, and MinIO provider abstractions and local
  container dependencies.
- SPEC-008 streams persisted workflow events over WebSocket through Redis
  pub/sub.
- SPEC-009 provides the Next.js frontend dashboard.
- SPEC-010 provides deterministic local demo seeding and demo runbooks.
- SPEC-011 adds safe no-key LLM provider defaults and feature-flagged runtime
  LLM behavior.
- SPEC-012 adds human approval and explicit workflow resume.
- SPEC-013 adds demo knowledge ingestion, retrieval/search APIs, RAG grounding
  behind `RAG_ENABLED=false`, and frontend evidence/search/catalog surfaces.

SPEC-014 plans the deployment and operations slice needed to run the board demo
outside an individual developer machine. It should make packaging,
configuration, health/readiness, observability, CI, and deployment runbooks
bounded and reviewable before implementation.

## Product Goal

- Package the backend, frontend, Postgres, Redis, Qdrant, and MinIO into a
  reliable deployable demo stack.
- Support a board-ready deployment path on a single demo VM/VPS or equivalent
  local demo server.
- Make operational status observable through health/readiness checks,
  structured logs, planned metrics/tracing boundaries, and clear runbooks.
- Preserve local deterministic demo behavior.
- Avoid requiring real LLM or embedding provider keys for the default demo.
- Keep production secrets out of the repository.

## Non-goals

- Kubernetes implementation.
- Cloud-provider-specific Terraform or managed service provisioning.
- Production secret vault integration.
- Autoscaling.
- Billing or provider-cost dashboards.
- Provider-management UI.
- LLM token streaming or agent thought streaming.
- Enterprise SSO.
- Production email sending.
- Multi-tenant isolation.
- Real secrets, real API keys, or real customer data.
- Global response envelope rollout.
- Backend/frontend/runtime behavior changes during planning.
- Database model or migration changes during planning.

## Deployment Target Strategy

The primary SPEC-014 target is a Docker Compose production-demo stack on one
VM/VPS or controlled demo server.

Planned services:

- backend
- frontend
- postgres
- redis
- qdrant
- minio

Rationale:

- Docker Compose already exists and is understood by the current runbooks.
- A single-host stack is reproducible for graduation evaluation and board demos.
- It avoids Kubernetes, Terraform, and cloud-provider decisions before the
  product needs them.
- It can still document future split deployment options, such as hosting the
  Next.js frontend separately on Vercel later.

Local development Compose behavior must remain intact. Production-demo Compose
should be additive, likely through a separate file such as
`docker-compose.prod.yml` or a Compose profile, not a replacement for the
current local developer flow.

## Environment And Secrets Strategy

SPEC-014 should plan environment templates without committing real secrets.

Environment tiers:

- local demo: current deterministic local defaults
- production demo: explicit values supplied by deployment operator
- CI/test: fake/no-key defaults and ephemeral service credentials

Required backend categories:

- `APP_ENV`, `DEBUG`, `APP_NAME`, `API_V1_PREFIX`, `LOG_LEVEL`
- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `MINIO_ENDPOINT`, `MINIO_BUCKET_NAME`, `MINIO_ACCESS_KEY`,
  `MINIO_SECRET_KEY`
- `JWT_SECRET_KEY`, token expiry settings
- `BACKEND_CORS_ORIGINS`
- LLM settings from SPEC-011
- embedding and RAG settings from SPEC-013

Required frontend categories:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_WS_BASE_URL`

Rules:

- Secrets are injected by environment only.
- No real keys or production credentials are committed.
- Demo credentials remain local-demo only and must not be production defaults.
- Production-demo templates should use placeholders such as
  `change-me-in-deployment`, not working credentials.
- Rotation, backup encryption, and vault integration should be documented as
  later operational guidance, not implemented in this spec.

## Container And Compose Strategy

Implementation should review the current backend Dockerfile and existing
Compose file before changing them.

Planned container work:

- keep backend runtime and dev/test targets separate
- add or refine frontend production container packaging
- add a production-demo Compose file or profile
- include service health checks where supported
- keep only required public ports exposed
- keep Postgres, Redis, Qdrant, and MinIO internal where possible for the
  production-demo stack

Service health expectations:

- backend: `/health`, `/ready`, and `/live`
- postgres: `pg_isready`
- redis: `redis-cli ping`
- qdrant: HTTP health or collection/client readiness check where practical
- minio: `mc ready` or provider health check

Data volumes/backups:

- Postgres data volume and documented backup/restore commands
- Qdrant storage volume and documented backup/export guidance
- MinIO data volume and documented object backup guidance

Reverse proxy and HTTPS:

- Optional later task scope may add a reverse proxy such as Caddy, Nginx, or
  Traefik.
- SPEC-014 should document HTTPS/reverse-proxy guidance, but must not require
  a cloud provider.

## Backend Production Readiness

The backend currently starts with:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

SPEC-014 should plan whether to keep this for the bounded demo or add a
production command with explicit workers. Gunicorn/Uvicorn worker mode may be
planned if it fits the current dependencies and container shape.

Backend readiness work should include:

- production-safe settings validation for insecure defaults
- explicit `APP_ENV=production` behavior
- CORS allowlist validation
- optional trusted-host guidance if implemented
- request ID logging remains enabled
- safe unhandled-error responses remain enabled
- startup does not run demo seed or knowledge ingestion automatically
- readiness checks verify critical dependencies where appropriate:
  - Postgres
  - Redis
  - Qdrant
  - MinIO

Readiness must not become brittle for optional LLM providers. Missing Groq,
OpenRouter, Gemini, or Ollama config should not fail readiness unless that
provider path is explicitly enabled and required by a later production policy.

## Frontend Production Readiness

The frontend currently provides a Next.js App Router dashboard with scripts:

```text
npm run lint
npm run build
npm run typecheck
npm test
```

SPEC-014 should plan:

- Next.js production build flow
- whether to use standalone output for container packaging
- a frontend Dockerfile if one is not already present
- runtime environment handling for:
  - `NEXT_PUBLIC_API_BASE_URL`
  - `NEXT_PUBLIC_WS_BASE_URL`
- same-stack Compose deployment or later optional Vercel deployment
- no frontend feature changes during deployment hardening

If Vercel is documented later, it remains optional and should not become the
primary SPEC-014 dependency.

## Observability Strategy

Current backend logging uses structlog JSON output and request completion logs
with request id, method, path, status code, and duration.

SPEC-014 should harden and document observability around:

- structured JSON logs
- request ID propagation and response header behavior
- safe exception logging without secrets
- audit logs and workflow events as app-domain evidence, not operational logs
- log redaction for:
  - API keys
  - bearer tokens
  - JWTs
  - provider payloads
  - raw prompts
  - raw documents
  - raw embeddings/vector payloads

Planned metrics foundations:

- request count, duration, and status code
- workflow run/resume count and duration
- approval decisions by type
- WebSocket connection count/failure count
- RAG search count and retrieval failures
- knowledge ingestion counts
- LLM provider calls/failures/latency when LLM runtime is enabled

Tracing:

- OpenTelemetry may be planned as an optional later integration.
- No telemetry vendor should be required in SPEC-014.

## CI Quality Gate Strategy

SPEC-014 should plan a GitHub Actions or equivalent CI workflow. No CI exists
currently.

Backend gate:

```bash
docker-compose config
docker-compose build backend-test
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
```

Frontend gate:

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run typecheck
npm test
```

Important CI note: run frontend build and typecheck serially. Parallel build
and typecheck can race on generated `.next/types`.

CI must not require real LLM keys, real embedding providers, external SaaS
credentials, or cloud-provider secrets. Dependency install/build network access
is expected unless the CI platform caches dependencies.

## Deployment Runbook Strategy

SPEC-014 should add a deployment runbook in a later task that covers:

1. prerequisites
2. environment file creation
3. image build
4. service startup
5. database migrations
6. deterministic demo seed
7. demo knowledge ingestion
8. frontend startup and URL validation
9. health/readiness checks
10. smoke flow
11. backup basics
12. restore basics
13. rollback basics
14. troubleshooting

Smoke flow:

- login as Manager/Admin
- workflow list/detail loads
- run workflow to `WAITING_APPROVAL`
- evidence panel displays empty or populated RAG state honestly
- approve workflow
- resume workflow
- completed timeline shows approval/resume events
- knowledge search/catalog works after ingestion

Troubleshooting topics:

- database unavailable
- Redis unavailable
- Qdrant missing collection
- MinIO bucket/credential issue
- CORS mismatch
- frontend API URL mismatch
- WebSocket URL mismatch
- JWT secret missing or insecure
- LLM provider key missing only when real provider mode is enabled
- demo seed/knowledge ingestion rerun behavior

## Security Hardening Strategy

SPEC-014 should plan security checks appropriate for a deployable demo:

- no default production secrets
- reject or warn on development JWT secret in production
- production `DEBUG=false`
- CORS allowlist required for production-demo deployment
- frontend `NEXT_PUBLIC_*` values documented as public
- MinIO, Qdrant, Postgres, and Redis should not be publicly exposed unless a
  runbook explicitly justifies it for local demo
- HTTPS and reverse proxy guidance
- demo credentials clearly scoped to local/demo only
- no real customer data
- no raw prompts, provider payloads, documents, embeddings, or secrets in logs

Rate limiting, WAF, enterprise SSO, and secret vault integration are deferred.

## Testing Strategy

Implementation tasks should add tests proportionate to the operational surface:

- Compose config validation.
- Backend production settings validation.
- Readiness dependency checks with mocked provider clients.
- Logging redaction tests.
- Safe startup tests proving demo seed and knowledge ingestion do not auto-run.
- CI workflow syntax/check tests if practical.
- Deployment docs smoke command checks.
- Frontend production build validation.
- No tests requiring real cloud provider keys or live LLM provider credentials.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Production-demo stack accidentally uses local insecure secrets | Add production settings validation and placeholder templates |
| Readiness fails because optional LLM providers are unconfigured | Readiness checks only critical infrastructure by default |
| Compose production profile breaks local dev flow | Additive prod file/profile, keep current compose behavior intact |
| Frontend public env variables leak secrets | Document `NEXT_PUBLIC_*` as public and keep secrets backend-only |
| CI becomes flaky due to generated Next types | Run build and typecheck serially |
| Demo seed/knowledge ingestion accidentally run on startup | Keep explicit CLI-only behavior and add startup safety tests |

## Suggested Task Breakdown

- TASK 014.1 - Deployment Configuration Plan and Environment Templates
- TASK 014.2 - Production Docker Compose and Container Hardening
- TASK 014.3 - Readiness, Dependency Checks, and Safe Startup Behavior
- TASK 014.4 - Structured Observability and Metrics Foundations
- TASK 014.5 - CI Quality Gates and Deployment Smoke Scripts
- TASK 014.6 - Deployment Runbook and Demo Packaging Docs
- TASK 014.7 - Production Deployment Hardening and SPEC-014 Final Review

## Acceptance Criteria

- Production-demo deployment target is clearly defined.
- Environment/secrets strategy is documented without real secrets.
- Container/Compose strategy is bounded and additive.
- Backend and frontend production readiness requirements are defined.
- Observability strategy covers logs, request IDs, metrics, tracing, redaction,
  and app-domain audit/event evidence.
- CI quality gate strategy covers backend and frontend validation without real
  provider keys.
- Deployment runbook and smoke strategy are defined.
- Security hardening and risks are explicit.
- Planning preserves local deterministic demo behavior.
- Planning does not implement deployment code, CI workflows, observability
  code, Docker changes, backend/frontend/runtime behavior, migrations, models,
  cloud resources, or real secrets.
