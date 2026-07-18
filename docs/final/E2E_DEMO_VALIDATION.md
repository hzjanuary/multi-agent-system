# End-to-End Demo Validation

This checklist validates the board-demo path for Enterprise Multi-Agent OS using
existing commands and API endpoints only. It is intended for local-demo or
production-demo stacks and does not require real LLM keys by default.

## Safety Model

- Full workflow validation is mutating and requires `--confirm-local-demo`.
- The script never prints access tokens, refresh tokens, passwords, cookies, or
  Authorization headers.
- The script does not delete volumes, reset databases, deploy, push images, send
  email, or call real LLM providers.
- Demo seed and knowledge ingestion remain explicit commands; application
  startup must not auto-seed or auto-ingest.
- Demo credentials are local-demo/board-demo only and must not be used for
  production accounts.

## Prerequisites

- Backend and frontend are running, either through local development commands or
  the production-demo Compose stack.
- Docker Compose is available when running the full mutating flow because the
  script runs backend CLI commands in a container.
- The backend can reach Postgres. For `--include-rag`, it must also be able to
  reach Qdrant and MinIO.
- No real provider keys are required for the default validation mode.

Recommended preflight:

```bash
bash scripts/ci/compose-gate.sh
bash scripts/deployment/smoke-prod-demo.sh --include-ready
```

## Environment Variables

The script has safe local-demo defaults and supports overrides:

| Variable | Default |
| --- | --- |
| `BACKEND_URL` | `http://localhost:8000` |
| `FRONTEND_URL` | `http://localhost:3000` |
| `DEMO_MANAGER_EMAIL` | `manager@example.test` |
| `DEMO_MANAGER_PASSWORD` | `DemoPassword123!` |
| `DEMO_VIEWER_EMAIL` | `viewer@example.test` |
| `DEMO_VIEWER_PASSWORD` | `DemoPassword123!` |
| `TARGET_WORKFLOW_ID` | `dc5e7963-c2a4-5ad6-8f70-0741431597f0` |
| `COMPOSE_FILE` | `docker-compose.yml` |
| `COMPOSE_ENV_FILE` | empty |
| `BACKEND_CLI_SERVICE` | `backend-test` |

For production-demo containers:

```bash
COMPOSE_FILE=docker-compose.prod.yml \
COMPOSE_ENV_FILE=docs/deployment/.env.production.example \
BACKEND_CLI_SERVICE=backend \
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready
```

Use an untracked production-demo env file with real deployment secrets when
validating a real demo environment. Do not commit that file.

## No-Key Default Mode

Default final validation is compatible with:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

In this mode, the workflow should still run deterministically to
`WAITING_APPROVAL`, accept approval, resume through `/resume`, and finish at
`COMPLETED`.

## Optional RAG Mode

RAG validation remains no-key compatible when fake embeddings are used:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
```

Before the RAG workflow run, ingest demo knowledge:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Or let the validation script run ingestion by adding `--include-rag`. The script
then verifies:

- knowledge document catalog is available
- knowledge search returns bounded citation results
- the workflow state includes attached evidence/citations after a RAG-enabled run
- no raw embeddings, prompts, provider payloads, or secrets are printed

If `RAG_ENABLED=false`, the evidence panel may be empty by design.

## Script Usage

Help:

```bash
bash scripts/final/e2e-demo-validation.sh --help
```

Non-mutating smoke only:

```bash
bash scripts/final/e2e-demo-validation.sh
```

Full no-key local-demo validation:

```bash
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready
```

Full validation with optional RAG evidence:

```bash
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready --include-rag
```

Full validation with optional Viewer/RBAC and metrics checks:

```bash
bash scripts/final/e2e-demo-validation.sh \
  --confirm-local-demo \
  --include-ready \
  --include-rbac \
  --include-metrics
```

Machine-readable summary:

```bash
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --json-summary
```

## Validation Flow

1. Check backend `/health` and `/live`.
2. Optionally check backend `/ready`.
3. Check frontend root unless `--skip-frontend` is used.
4. Run `alembic upgrade head` unless `--skip-migrations` is used.
5. Run `python -m app.demo.seed --confirm-local-demo --json` unless
   `--skip-seed` is used.
6. For `--include-rag`, run
   `python -m app.knowledge.ingest_demo --confirm-local-demo --json` unless
   `--skip-ingest` is used.
7. Login as Manager/Admin and keep the token in memory only.
8. List workflows and fetch the deterministic clean workflow.
9. Call `POST /api/v1/workflows/{workflow_id}/run`.
10. Verify the workflow reaches `WAITING_APPROVAL` and does not auto-resume.
11. Fetch persisted events.
12. For `--include-rag`, check knowledge search and workflow evidence.
13. Submit approval with a bounded comment through
    `POST /api/v1/workflows/{workflow_id}/approval`.
14. Verify approval history shows a final approval and `can_resume=true`.
15. Resume through `POST /api/v1/workflows/{workflow_id}/resume`.
16. Verify the workflow reaches `COMPLETED`.
17. Verify the timeline contains approval, resume, and `email_preparation`
    continuation evidence.
18. Optionally verify Viewer mutation denial.
19. Optionally verify Admin/Manager metrics access.

## Expected Outcomes

- Health and liveness return HTTP 200.
- Readiness returns HTTP 200 when all required infrastructure is available.
- Demo seed completes with a bounded JSON summary.
- The clean seeded workflow starts from `CREATED`.
- `/run` stops at `WAITING_APPROVAL`.
- Approval transitions the workflow to `APPROVED`.
- Approval history contains the approval decision.
- `/resume` transitions the workflow to `COMPLETED`.
- Timeline events include approval/resume continuation evidence.
- Optional RAG mode returns knowledge search results and attached citations.
- Optional metrics check returns a safe bounded response.

## Evidence Capture Checklist

Capture the following for the final evaluation report:

- run date/time and commit SHA
- command line used, with secrets omitted
- backend/frontend URLs
- no-key or RAG-enabled mode
- health/live/ready summary
- seed and knowledge ingestion summaries
- workflow id and status transitions
- approval decision summary
- resume summary
- timeline event count and event type summary
- RAG citation count if enabled
- metrics endpoint status if enabled
- skipped optional checks
- screenshots listed in `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md`

Use `docs/final/E2E_EVIDENCE_CAPTURE_TEMPLATE.md` for placeholder notes.

## Troubleshooting

- `/health` fails: confirm the backend process is running and the backend URL is
  correct.
- `/health` works but `/ready` fails: inspect Postgres, Redis, Qdrant, and MinIO
  connectivity using `docs/deployment/TROUBLESHOOTING.md`.
- Frontend root fails: confirm `FRONTEND_URL` and production-demo port mappings.
- Login fails: run demo seed and confirm local-demo credentials only.
- Target workflow is not `CREATED`: rerun demo seed without `--skip-seed`.
- Workflow run does not reach `WAITING_APPROVAL`: inspect backend logs and
  workflow events.
- RAG search is empty: ensure Qdrant/MinIO are running and knowledge ingestion
  completed successfully.
- RAG evidence is missing: confirm backend was started with `RAG_ENABLED=true`
  before running the workflow.
- Metrics returns 401/403: use a Manager/Admin token and confirm metrics route
  is enabled.

## Limitations

- The script validates the existing demo flow; it is not a load test.
- It does not capture screenshots automatically.
- It does not verify WebSocket rendering in a browser.
- It does not verify real LLM providers or external SaaS services.
- It does not implement deployment, backup, rollback, or cleanup automation.
