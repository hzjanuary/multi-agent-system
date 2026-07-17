# Production-Demo Troubleshooting

Use this guide when the production-demo stack, smoke checks, or board demo fail.

## Docker Compose Config Failure

Run:

```bash
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
```

Common causes:

- missing env file
- placeholder syntax edited incorrectly
- unsupported Docker Compose version
- port already in use

## Backend Cannot Connect To Postgres

Symptoms:

- `/ready` returns `503` for Postgres
- migrations fail
- backend logs show database connection errors

Check:

- `DATABASE_URL`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- Postgres container health
- that the backend and Postgres are on the same Compose network

Do not run migrations from application startup. Run them explicitly.

## Redis Unavailable

Symptoms:

- `/ready` reports Redis failed
- live event streaming may not deliver near-real-time messages

Check:

- `REDIS_URL`
- Redis container health
- internal service name and port

## Qdrant Unavailable Or Collection Missing

Symptoms:

- `/ready` reports Qdrant failed when service is unreachable
- knowledge search returns empty results
- RAG evidence panel stays empty after a RAG-enabled run

Check:

- `QDRANT_URL`
- Qdrant container health
- knowledge ingestion completed successfully
- collection name matches the ingestion/search settings

Readiness checks Qdrant service reachability; it does not upsert or repair
collections.

## MinIO Bucket Or Credential Issue

Symptoms:

- `/ready` reports object storage failed
- knowledge ingestion fails before writing source documents

Check:

- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET_NAME`
- MinIO container health

Readiness does not create buckets or objects. Keep MinIO private to the
deployment network unless explicitly hardened.

## /health Works But /ready Fails

This is expected when the backend process is alive but a required dependency is
not ready. Use `/health` for container process health and `/ready` for
dependency readiness.

## CORS Mismatch

Symptoms:

- frontend loads but API calls fail in the browser
- browser console shows CORS errors

Check:

- `BACKEND_CORS_ORIGINS` includes the frontend origin exactly
- scheme, host, and port match the browser URL
- backend was restarted after env changes

## Frontend API Base URL Mismatch

Symptoms:

- frontend pages load but login/workflow requests go to the wrong host

Check:

- `NEXT_PUBLIC_API_BASE_URL`
- frontend image was rebuilt if public env changed at build time
- browser network tab request URLs

## WebSocket URL Mismatch

Symptoms:

- workflow detail loads but live timeline does not connect

Check:

- `NEXT_PUBLIC_WS_BASE_URL`
- browser console WebSocket URL
- reverse proxy supports WebSocket upgrade if one is added later
- Redis readiness if persisted events work but live updates do not

## JWT Secret Missing Or Placeholder

Symptoms:

- auth token validation fails after restart
- production-demo security review fails

Check:

- `JWT_SECRET_KEY` is not `change-me-in-production`
- the same secret is used by all backend instances in the demo stack
- the secret is injected through env, not committed

## Demo Login Fails

Check:

- migrations ran
- demo seed ran explicitly
- using local-demo credentials from `docs/demo/DEMO_RUNBOOK.md`
- frontend API URL points to the seeded backend

Demo credentials are local-demo/board-demo only.

## Workflow Run Fails Before WAITING_APPROVAL

Check:

- workflow status before running
- backend logs for safe error category
- `/ready` dependencies
- `LLM_RUNTIME_ENABLED=false` for deterministic no-key mode
- no real provider key is required unless real LLM runtime is enabled

## RAG Evidence Missing

Check:

- `RAG_ENABLED=true` for the backend process
- knowledge ingestion ran successfully
- Qdrant is reachable
- workflow was run after RAG was enabled
- evidence panel empty state is expected when no citations are attached

## Knowledge Search Empty

Check:

- knowledge ingestion ran explicitly
- Qdrant collection name matches
- query is not too narrow
- source type/domain filters are not excluding all results

## LLM Provider Key Missing

Default no-key mode does not need provider keys. If a real provider is
enabled, configure the matching key and model:

- `GROQ_API_KEY` / `GROQ_MODEL`
- `OPENROUTER_API_KEY` / `OPENROUTER_MODEL`
- `GEMINI_API_KEY` / `GEMINI_MODEL`
- local Ollama server/model for `ollama`

Never commit real keys.

## npm Audit Advisories

Run the normal frontend gate first:

```bash
bash scripts/ci/frontend-gate.sh
```

Do not apply broad dependency upgrades during a deployment runbook task unless
the security fix is explicitly scoped.

## Frontend Build/Typecheck Race

Run frontend build and typecheck serially. The CI and local scripts already do
this to avoid `.next/types` races:

```bash
npm run build
npm run typecheck
```

## Windows Bash Caveat

On Windows, `bash` may launch WSL and fail if no distro is installed. Use Git
Bash instead:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' scripts/ci/compose-gate.sh
```

## What Not To Expect

The current production-demo stack does not include:

- Kubernetes or Terraform
- cloud deployment automation
- production secret vault
- production email sending
- upload/admin document-management UI
- external telemetry vendor
- Prometheus scrape config
- OpenTelemetry exporter
- token streaming
- agent-thought streaming
- zero-downtime rollback
