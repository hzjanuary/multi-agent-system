# SPEC-014 Tasks - Production Deployment and Observability

## Task List

### TASK 014.1 - Deployment Configuration Plan and Environment Templates

Goal: Add production-demo environment template documentation and settings
validation planning artifacts without changing runtime behavior.

Scope:

- Add production-demo `.env` template files or docs with placeholders only.
- Separate local demo, production demo, and CI/test environment guidance.
- Document required backend and frontend environment variables.
- Add tests for production settings validation if settings checks are
  implemented.
- Update README links to deployment docs if applicable.

Acceptance criteria:

- No real secrets or real provider keys are committed.
- Production-demo env placeholders are explicit and non-working.
- Local deterministic defaults remain documented.
- CI/test env does not require real LLM or cloud credentials.
- No Docker, runtime, API, frontend behavior, migrations, or model changes are
  added unless explicitly scoped by this task.

Validation:

```bash
git status --short
docker-compose config
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 014.2 - Production Docker Compose and Container Hardening

Goal: Add an additive production-demo container/Compose path for backend,
frontend, Postgres, Redis, Qdrant, and MinIO while preserving local developer
Compose behavior.

Scope:

- Add or update frontend production Dockerfile if needed.
- Add `docker-compose.prod.yml` or a production profile.
- Keep backend runtime image separate from backend-test/dev target.
- Configure production-demo health checks.
- Restrict public ports where practical.
- Define named volumes for persistent services.
- Add smoke validation commands for production-demo Compose config.

Acceptance criteria:

- Current `docker-compose.yml` local dev behavior remains intact.
- Production-demo stack includes backend, frontend, Postgres, Redis, Qdrant,
  and MinIO.
- No real secrets are embedded in Compose.
- Services use env-file or environment injection with placeholders only.
- No Kubernetes, Terraform, cloud-provider resources, migrations, models, API
  contract changes, or frontend feature changes are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config
docker-compose build backend-test
docker-compose run --rm backend-test pytest
cd frontend && npm install
cd frontend && npm run build
git diff --check
```

If the implementation uses a Compose profile instead of
`docker-compose.prod.yml`, replace the production config command with the
documented profile command.

### TASK 014.3 - Readiness, Dependency Checks, and Safe Startup Behavior

Goal: Harden backend readiness checks and startup safety without making
optional LLM providers required for deployment.

Scope:

- Extend `/ready` or readiness service to check critical dependencies:
  Postgres, Redis, Qdrant, and MinIO.
- Keep `/live` lightweight.
- Keep `/health` stable unless clearly documented.
- Add typed readiness response details without introducing a global response
  envelope.
- Add production settings validation for critical insecure defaults if not
  already implemented.
- Add tests proving demo seed and knowledge ingestion do not auto-run on
  backend startup.

Acceptance criteria:

- Readiness verifies critical infrastructure with safe timeouts.
- Missing optional real LLM provider keys do not fail readiness by default.
- Readiness failures return safe bounded details.
- Startup remains free of automatic demo seed or knowledge ingestion.
- Existing API routes and runtime behavior remain unchanged.
- No migrations/models are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis qdrant minio
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 014.4 - Structured Observability and Metrics Foundations

Goal: Harden structured operational logging, redaction, and metrics foundation
without adding a telemetry vendor.

Scope:

- Review request logging, request ID propagation, and exception logging.
- Add log redaction helpers/tests for secrets, tokens, provider payloads, raw
  prompts, raw documents, and embeddings.
- Add minimal in-process metrics counters or metrics DTO/service if scoped.
- Document planned metrics for request latency/status, workflow runs/resumes,
  approvals, RAG retrieval, and LLM calls.
- Keep audit logs and workflow events as domain evidence, not substitutes for
  operational logs.

Acceptance criteria:

- Logs remain structured JSON.
- Request IDs remain present in logs and responses.
- Error logs and operational event payloads do not leak secrets.
- Metrics foundation is bounded and vendor-neutral.
- No external telemetry vendor, token streaming, agent thought streaming,
  migrations, models, or API contract changes are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

### TASK 014.5 - CI Quality Gates and Deployment Smoke Scripts

Goal: Add CI validation and local smoke scripts for backend, frontend, demo
seed, and knowledge ingestion without real provider keys or cloud resources.

Scope:

- Add GitHub Actions workflow or equivalent CI configuration.
- Backend CI gate:
  - `docker-compose config`
  - backend-test build
  - Alembic upgrade head
  - pytest
  - Ruff
  - Black
  - MyPy
  - demo seed dry-run JSON
  - knowledge ingest dry-run JSON
- Frontend CI gate:
  - `npm ci`
  - `npm run lint`
  - `npm run build`
  - `npm run typecheck`
  - `npm test`
- Add deployment smoke script if useful and bounded.
- Run frontend build and typecheck serially to avoid `.next/types` races.

Acceptance criteria:

- CI does not require real LLM keys, embedding provider keys, cloud secrets, or
  live external provider calls.
- CI validates both backend and frontend.
- Smoke scripts are safe for local/CI demo use.
- Existing local validation commands remain documented.
- No deployment to a real cloud target is performed.

Validation:

```bash
git status --short
docker-compose config
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
cd frontend && npm ci
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

### TASK 014.6 - Deployment Runbook and Demo Packaging Docs

Goal: Add deployment and operations documentation for the production-demo
stack, including smoke checks, backup/restore basics, rollback, and
troubleshooting.

Scope:

- Add deployment runbook under `docs/deployment/` or equivalent.
- Document prerequisites, env setup, image build, service startup, migrations,
  seed, knowledge ingestion, frontend startup, and smoke checks.
- Document health/readiness checks.
- Document backup/restore basics for Postgres, Qdrant, and MinIO volumes.
- Document rollback basics.
- Link from root/backend/frontend/demo README files where appropriate.
- Keep demo credentials clearly local-demo only.

Acceptance criteria:

- Runbook can be followed from a clean host with Docker and Node/npm where
  needed.
- Smoke flow includes login, workflow run to `WAITING_APPROVAL`, evidence
  panel, approval, resume, completed timeline, and knowledge search/catalog.
- Troubleshooting covers database, Redis, Qdrant, MinIO, CORS, frontend API/WS
  URLs, JWT secret, and optional real LLM provider configuration.
- Docs do not claim Kubernetes, Terraform, cloud deployment, secret vault,
  production email, upload UI, or enterprise SSO exist.
- No backend/frontend/runtime behavior changes are added.

Validation:

```bash
git status --short
docker-compose config
git diff --check
```

Optional, if scripts/docs include executable smoke commands:

```bash
docker-compose build backend-test
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
cd frontend && npm run build
```

### TASK 014.7 - Production Deployment Hardening and SPEC-014 Final Review

Goal: Verify that SPEC-014 is deployable, production-demo safe, observable,
documented, and ready to close.

Scope:

- Review deployment env templates for accidental secrets.
- Review Compose/container changes for local-dev compatibility.
- Review readiness checks and startup safety.
- Review logging/redaction and metrics foundation.
- Review CI workflow and smoke scripts.
- Review deployment runbook and docs.
- Make only tiny docs/test/hardening fixes if blocking.

Acceptance criteria:

- Production-demo stack is documented and validated.
- Local deterministic demo behavior remains intact.
- No real secrets, real provider keys, or cloud resources are committed.
- No auto-seed or auto-ingestion on backend startup.
- Health/readiness behavior is safe and tested.
- CI gates are deterministic and do not require live provider credentials.
- Observability is structured, redacted, and vendor-neutral.
- No migrations/models, global response envelope, token streaming, production
  email, Kubernetes, Terraform, secret vault, or provider-management UI were
  added unless explicitly approved by a later spec.

Validation:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

Output:

- SPEC-014 status: Approved or Rejected.
- Evidence summary.
- Deployment/container summary.
- Environment/secrets summary.
- Readiness/startup summary.
- Observability summary.
- CI/runbook summary.
- Blocking issues.
- Non-blocking issues.
- Backlog items.
- Recommendation for next SPEC.
