# Production-Demo Smoke Checks

Use these checks before a board demo or after a production-demo stack restart.
They validate the current bounded deployment surface without mutating data.

## Automated Smoke

Check a running stack:

```bash
bash scripts/deployment/smoke-prod-demo.sh
```

Default checks:

- backend `GET /health`
- backend `GET /live`
- frontend root page

Include dependency readiness when Postgres, Redis, Qdrant, and MinIO are
expected to be healthy:

```bash
bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

Start the production-demo Compose stack first:

```bash
bash scripts/deployment/smoke-prod-demo.sh --start
```

Override URLs and env file when needed:

```bash
BACKEND_BASE_URL=https://api.example.test \
FRONTEND_BASE_URL=https://app.example.test \
COMPOSE_ENV_FILE=.env.production.local \
bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

The smoke script does not run migrations, seed demo data, ingest knowledge,
call real LLM providers, or modify workflow state.

## Manual Backend Checks

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/live
curl -fsS http://localhost:8000/ready
```

Interpretation:

- `/health` and `/live` can pass while dependencies are still unavailable.
- `/ready` returns `503` when a required dependency fails.
- A `503` readiness result should include only safe dependency status
  summaries, not connection strings, secrets, or stack traces.

## Manual Frontend Checks

Open the frontend URL and confirm:

- login page loads
- dashboard route loads after login
- workflow list renders
- workflow detail renders run panel, approval panel/history, evidence panel,
  knowledge search/catalog, and timeline

## Board Demo Checks

Before presenting:

- demo seed has been run explicitly
- knowledge ingestion has been run explicitly when RAG evidence is expected
- `RAG_ENABLED=true` only for the evidence demo
- no real LLM key is required for the default no-key demo
- frontend API and WebSocket URLs match the backend public origin
- `BACKEND_CORS_ORIGINS` includes the frontend origin
- Manager/Admin credentials work for demo login
- Viewer can show forbidden approval/resume behavior if needed

## Observability Checks

As Admin or Manager, check metrics only when an access token is available:

```bash
curl -fsS \
  -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/observability/metrics
```

The metrics response is in-process production-demo visibility. It is not a
Prometheus scrape endpoint and should be protected by deployment controls.

## Expected Non-Checks

These are intentionally not part of the smoke script:

- production email sending
- cloud-provider deployment
- image push
- real LLM provider calls
- upload/admin document management
- external telemetry vendor checks
- destructive volume cleanup
