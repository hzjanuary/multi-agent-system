# Demo Runbook

## Purpose

This runbook supports a board-ready Enterprise Procurement Workflow Automation
demo. It demonstrates the current implemented product path:

- Login with local demo users.
- View deterministic seeded workflows.
- Create a procurement quotation workflow.
- Run the deterministic runtime.
- Submit human approval decisions.
- Resume approved workflows through the explicit `/resume` path.
- Inspect retrieved evidence/citations when RAG is explicitly enabled.
- Search the local demo knowledge catalog after ingestion.
- Inspect persisted workflow events.
- Watch the workflow detail live event timeline.
- Show RBAC behavior through existing backend permissions.

This demo uses existing backend, frontend, runtime, workflow, knowledge, and
streaming behavior. It does not add real LLM reasoning, email sending, upload
UI, admin document management, or production seed management.

For the production-demo package, use `docs/deployment/RUNBOOK.md` and
`docs/deployment/DEMO_PACKAGE.md`. This local demo runbook remains the detailed
workflow walkthrough and troubleshooting reference.

For the board-stable demo, keep LLM runtime mode disabled:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
RAG_ENABLED=false
```

For the optional grounded-evidence demo, keep fake embeddings and enable only
RAG grounding:

```text
EMBEDDING_PROVIDER=fake
RAG_ENABLED=true
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
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
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

For a non-persisting knowledge ingestion check:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
```

The knowledge ingestion command is explicit and local-demo only. It chunks
deterministic demo procurement documents, stores source text in MinIO, and
upserts fake-embedded chunk vectors into Qdrant. Authenticated read-only
knowledge search/catalog APIs are available under `/api/v1/knowledge`.
Feature-flagged backend runtime grounding can use those citations when
`RAG_ENABLED=true`; it is disabled by default.

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
- `/workflows/e1771f90-a85e-5684-98d1-7dd0458a4e89`
- `/workflows/6b99fd38-1ecf-5213-8d69-43abcca20856`
- `/workflows/a14f5f3d-b4e0-5397-ad81-7f97913090d1`
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
| `rfq-001-waiting-approval-history` | `b0111d45-aff5-5b86-9ffd-9417704c9bab` | `WAITING_APPROVAL` | Live approval walkthrough with no final seeded decision |
| `rfq-001-approved-ready-to-resume` | `e1771f90-a85e-5684-98d1-7dd0458a4e89` | `APPROVED` | Resume-ready workflow with final approval history |
| `rfq-001-completed-resumed-history` | `6b99fd38-1ecf-5213-8d69-43abcca20856` | `COMPLETED` | Read-only approval and resume timeline history |
| `rfq-001-rejected-history` | `a14f5f3d-b4e0-5397-ad81-7f97913090d1` | `REJECTED` | Read-only rejection history |
| `rfq-001-completed-conflict` | `548e9b1b-4e35-5036-8604-fccbf9a12932` | `COMPLETED` | Optional run conflict/precondition demo |

The primary RFQ-001 reference data is:

- Domain: `it_equipment`
- Customer: `CUST-001`, Acme Manufacturing Group
- Product: `IT-LAP-001`, standard business laptop
- Quantity: 50
- Contract: `CON-2026-ACME-IT`
- Static expected total: `47628 USD`

The deterministic `/run` path stops at `WAITING_APPROVAL`. Human approval is
explicit. After a Manager/Admin approves a waiting workflow, the separate
`/resume` path continues the bounded post-approval email-preparation stage and
reaches `COMPLETED` without sending real email.

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
9. Show that approval history is empty and the approval panel is available.
10. Optional branch: select `Request changes` with a short comment. Confirm the
    workflow remains `WAITING_APPROVAL` and the history shows a non-final
    changes-requested decision.
11. Select `Approve` with a comment such as:

```text
Approved for customer response after warranty review.
```

12. Confirm the workflow becomes `APPROVED`, approval history shows the final
    decision, and the event timeline includes the approval event.
13. Select `Resume workflow`.
14. Confirm the workflow reaches `COMPLETED`, the runtime result says the
    resume completed, and the timeline includes resume-requested,
    email-preparation, and resumed events. No real email is sent.
15. Optional read-only history: open
    `/workflows/6b99fd38-1ecf-5213-8d69-43abcca20856` to show a completed
    approval/resume history, or
    `/workflows/a14f5f3d-b4e0-5397-ad81-7f97913090d1` to show a rejected
    workflow.
16. Open `/workflows/new`.
17. Create a new procurement quotation workflow with:

```text
Domain: it_equipment
Customer name: Acme Manufacturing Group
Request text: We would like to purchase 50 standard business laptops for a new operations team. We signed a master agreement in May 2026. Please provide your best quotation.
Items JSON: [{"name":"Standard business laptop","quantity":50}]
Metadata JSON: {"tags":{"source":"board-demo"},"attributes":{}}
```

18. Open the created workflow detail page from the success link.
19. Select `Run workflow`.
20. Confirm the runtime result shows `WAITING_APPROVAL` behavior and completed
    stages up to approval.
21. Confirm the detail page refreshes persisted events and the live timeline
    remains visible.
22. If `RAG_ENABLED=true` and demo knowledge was ingested before the run, inspect
    the Evidence and citations panel. It should show compliance,
    validation/finance, and approval citations with source title/type, citation
    label, excerpt, score, stage, and document id.
23. Use the Knowledge search panel with a query such as:

```text
procurement policy approval evidence
```

24. Confirm search results show bounded citation excerpts, or an honest empty
    state if the knowledge collection has not been ingested.
25. Confirm the Demo documents catalog lists the deterministic policy,
    contract, supplier, pricing, and compliance-checklist documents.
26. Optional RBAC checkpoint: sign out, sign in as `sales@example.test`, open a
    workflow detail page, and run the workflow. The backend should reject the
    run action with a clear 403-style message because Sales can create/read but
    cannot run workflows.
27. Optional approval RBAC checkpoint: sign in as `viewer@example.test`, open
    the waiting-approval workflow, and try an approval action. The backend
    should reject the decision with an understandable forbidden message.

## Expected Checkpoints

- Login succeeds with local demo credentials.
- `/dashboard` renders the authenticated app shell.
- `/workflows` shows seeded workflows without fake loaded data.
- Seeded workflow detail loads by stable workflow ID.
- Event backlog is visible for the waiting-approval workflow.
- Timeline shows a clear connection state.
- Approval panel is visible for a `WAITING_APPROVAL` workflow.
- `request_changes` records a non-final approval history entry.
- Approval changes the workflow to `APPROVED`.
- Resume changes the workflow to `COMPLETED`.
- Approval and resume events appear in the persisted timeline after refresh.
- Create workflow succeeds through the backend API.
- Run workflow succeeds for Manager/Admin and reaches the expected
  `WAITING_APPROVAL` behavior.
- A denied RBAC action shows an understandable error.
- No screen claims that real LLM reasoning, RAG, or email sending is
  implemented.
- Demo knowledge documents can be ingested into MinIO/Qdrant and searched
  through authenticated backend knowledge APIs. Runtime grounding is opt-in with
  `RAG_ENABLED=true`.
- Workflow detail shows an honest empty evidence state when no RAG citations
  are attached.
- RAG-enabled runs with ingested demo knowledge can show bounded citations in
  the Evidence and citations panel.
- Knowledge search/catalog surfaces use existing `/api/v1/knowledge` endpoints
  and do not expose raw embeddings or raw vector payloads.

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

### Knowledge Ingestion Command Refuses To Run

Mutating knowledge ingestion also requires the confirmation flag:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Use `--dry-run --json` for a non-persisting summary.

### Qdrant Or MinIO Is Unavailable During Knowledge Ingestion

Run:

```bash
docker-compose ps qdrant minio
docker-compose logs qdrant
docker-compose logs minio
```

The ingestion CLI requires Qdrant and MinIO. It does not affect workflow seed
records or frontend behavior if those services are unavailable.

### Evidence Panel Is Empty

The evidence panel is populated only after all of the following are true:

```text
RAG_ENABLED=true
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
workflow runtime has run after RAG was enabled
```

With `RAG_ENABLED=false`, or before a RAG-enabled run attaches citations, the
frontend correctly shows that no retrieved evidence has been attached yet.

### Knowledge Search Returns No Results

Confirm Qdrant and MinIO are running, then rerun the ingestion command:

```bash
docker-compose up -d qdrant minio
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Search and catalog endpoints require a valid frontend session. A 403 indicates
the backend rejected the current role/session. A 503 indicates the retrieval
provider is unavailable or the vector collection cannot be reached.

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

### Approval Or Resume Returns 409

Refresh the workflow detail page and check the current workflow status. Approval
decisions are accepted only from `WAITING_APPROVAL`. Resume is accepted only
after a final approve decision leaves the workflow in `APPROVED`. Rejected,
completed, request-changes-only, and already-resumed workflows should return
clear conflict messages.

### npm Audit Warnings

`npm install` may report package audit notices. Treat them as package-manager
advisories unless they break `npm run lint`, `npm run build`,
`npm run typecheck`, or `npm test`.

### Vite CJS Deprecation Warning

Vitest may emit a Vite CJS deprecation warning in some Node/npm combinations.
Treat it as non-blocking if the frontend test command exits successfully.

## Known Limitations

- Real LLM provider behavior is optional local experimentation only; the
  board-stable demo defaults to deterministic runtime mode.
- Runtime RAG grounding is disabled by default. When enabled and demo knowledge
  has been ingested, the workflow detail evidence panel can display bounded
  backend-attached citations.
- No document upload/indexing UI.
- No admin user-management UI.
- No production deployment automation.
- No real procurement pricing, compliance, approval, or email sending logic.
