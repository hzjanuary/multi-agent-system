# Demo Runbook

## Purpose

This runbook supports a board-ready Enterprise Procurement Workflow Automation
demo. It demonstrates the current implemented product path:

- Login with local demo users.
- View deterministic seeded workflows.
- Create a procurement quotation workflow.
- Run the deterministic runtime.
- Inspect persisted workflow events.
- Watch the workflow detail live event timeline.
- Show RBAC behavior through existing backend permissions.

This demo uses existing backend, frontend, runtime, workflow, and streaming
behavior. It does not add real LLM reasoning, RAG, approval continuation, email
sending, or production seed management.

For the board-stable demo, keep LLM runtime mode disabled:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

Optional real-provider local experimentation is documented separately in
`docs/llm/LOCAL_LLM_DEMO.md`. Real provider responses may vary and are not
required for the board walkthrough.

## Prerequisites

- Docker Desktop is running.
- Repository is checked out locally.
- Node.js 20 or later and npm are available for the frontend.
- Backend migrations can run through the `backend-test` Docker service.
- Frontend environment variables are configured from `frontend/.env.example`:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1
```

## Backend Setup

Run from the repository root:

```bash
docker-compose config
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

The seed command is explicit and local-demo only. It does not run on import,
backend startup, or through a public API endpoint.

To verify idempotency, run the same seed command a second time:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

The second run should report reused roles, users, workflows, and events instead
of creating duplicates.

For a machine-readable summary:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --json
```

Start the backend service after migrations and seeding:

```bash
docker-compose up --build backend
```

The backend API is expected at:

```text
http://localhost:8000/api/v1
```

## Frontend Setup

Run from the repository root:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000
```

Routes to use during the demo:

- `/`
- `/login`
- `/dashboard`
- `/workflows`
- `/workflows/new`
- `/workflows/dc5e7963-c2a4-5ad6-8f70-0741431597f0`
- `/workflows/b0111d45-aff5-5b86-9ffd-9417704c9bab`
- `/workflows/548e9b1b-4e35-5036-8604-fccbf9a12932`

## Demo Credentials

These credentials are local-demo only. They are intentionally obvious and must
not be reused as production credentials.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@example.test` | `DemoPassword123!` |
| Manager | `manager@example.test` | `DemoPassword123!` |
| Sales | `sales@example.test` | `DemoPassword123!` |
| Legal | `legal@example.test` | `DemoPassword123!` |
| Finance | `finance@example.test` | `DemoPassword123!` |
| Viewer | `viewer@example.test` | `DemoPassword123!` |

Recommended primary presenters:

- Manager or Admin for create/run access.
- Sales for create access and run denial.
- Viewer, Legal, or Finance for read-only behavior.

## Seeded Workflows

The seed command creates deterministic RFQ-001 workflow examples:

| Key | Stable workflow ID | Expected status | Demo use |
| --- | --- | --- | --- |
| `rfq-001-clean-created` | `dc5e7963-c2a4-5ad6-8f70-0741431597f0` | `CREATED` | Primary workflow ready to run |
| `rfq-001-waiting-approval-history` | `b0111d45-aff5-5b86-9ffd-9417704c9bab` | `WAITING_APPROVAL` | Detail page and event backlog demo |
| `rfq-001-completed-conflict` | `548e9b1b-4e35-5036-8604-fccbf9a12932` | `COMPLETED` | Optional run conflict/precondition demo |

The primary RFQ-001 reference data is:

- Domain: `it_equipment`
- Customer: `CUST-001`, Acme Manufacturing Group
- Product: `IT-LAP-001`, standard business laptop
- Quantity: 50
- Contract: `CON-2026-ACME-IT`
- Static expected total: `47628 USD`

The deterministic runtime stops at `WAITING_APPROVAL`; approval continuation and
`/resume` are deferred.

## Board Walkthrough

1. Open `/login`.
2. Sign in as `manager@example.test` with `DemoPassword123!`.
3. Open `/dashboard`.
4. Point out the dashboard shell and navigation: Dashboard, Workflows, Create
   Workflow, and Runtime Events.
5. Open `/workflows`.
6. Confirm the seeded RFQ-001 workflows appear in the list.
7. Open the waiting-approval workflow:
   `/workflows/b0111d45-aff5-5b86-9ffd-9417704c9bab`.
8. Show workflow status, request/state details, persisted event backlog, and
   live event timeline connection state.
9. Open `/workflows/new`.
10. Create a new procurement quotation workflow with:

```text
Domain: it_equipment
Customer name: Acme Manufacturing Group
Request text: We would like to purchase 50 standard business laptops for a new operations team. We signed a master agreement in May 2026. Please provide your best quotation.
Items JSON: [{"name":"Standard business laptop","quantity":50}]
Metadata JSON: {"tags":{"source":"board-demo"},"attributes":{}}
```

11. Open the created workflow detail page from the success link.
12. Select `Run workflow`.
13. Confirm the runtime result shows `WAITING_APPROVAL` behavior and completed
    stages up to approval.
14. Confirm the detail page refreshes persisted events and the live timeline
    remains visible.
15. Optional RBAC checkpoint: sign out, sign in as `sales@example.test`, open a
    workflow detail page, and run the workflow. The backend should reject the
    run action with a clear 403-style message because Sales can create/read but
    cannot run workflows.

## Expected Checkpoints

- Login succeeds with local demo credentials.
- `/dashboard` renders the authenticated app shell.
- `/workflows` shows seeded workflows without fake loaded data.
- Seeded workflow detail loads by stable workflow ID.
- Event backlog is visible for the waiting-approval workflow.
- Timeline shows a clear connection state.
- Create workflow succeeds through the backend API.
- Run workflow succeeds for Manager/Admin and reaches the expected
  `WAITING_APPROVAL` behavior.
- A denied RBAC action shows an understandable error.
- No screen claims that real LLM reasoning, RAG, approval continuation, or email
  sending is implemented.

## Troubleshooting

### Docker Is Not Running

Run `docker info`. If it fails, start Docker Desktop and rerun the backend setup
commands.

### Postgres Is Not Healthy

Run:

```bash
docker-compose ps postgres
docker-compose logs postgres
```

Wait for the health check to pass before running migrations or the seed command.

### Migrations Are Not Applied

Run:

```bash
docker-compose run --rm backend-test alembic upgrade head
```

Then rerun the seed command.

### Seed Command Refuses To Run

Mutating execution requires the confirmation flag:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

Use `--dry-run` only when you want the command to roll back instead of
persisting records.

### Frontend Cannot Reach Backend

Check `frontend/.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1
```

Also verify the backend is running at port `8000` and that CORS includes
`http://localhost:3000`.

### WebSocket Connection Is Rejected

Sign in again from `/login`. The frontend WebSocket client uses the current
access token as an `access_token` query parameter. Missing or expired tokens are
rejected by the backend stream endpoint.

### Redis Is Unavailable

Run:

```bash
docker-compose ps redis
docker-compose logs redis
```

The persisted event backlog still comes from Postgres, but live WebSocket
delivery depends on Redis pub/sub.

### npm Audit Warnings

`npm install` may report package audit notices. Treat them as package-manager
advisories unless they break `npm run lint`, `npm run build`,
`npm run typecheck`, or `npm test`.

### Vite CJS Deprecation Warning

Vitest may emit a Vite CJS deprecation warning in some Node/npm combinations.
Treat it as non-blocking if the frontend test command exits successfully.

## Known Limitations

- No `/resume` endpoint or human approval continuation.
- Real LLM provider behavior is optional local experimentation only; the
  board-stable demo defaults to deterministic runtime mode.
- No RAG or document upload/indexing UI.
- No admin user-management UI.
- No production deployment automation.
- No real procurement pricing, compliance, approval, or email sending logic.
