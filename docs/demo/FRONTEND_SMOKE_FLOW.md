# Frontend Smoke Flow

Use this checklist after running the demo seed command from
`docs/demo/DEMO_RUNBOOK.md`.

For production-demo smoke checks, also use
`docs/deployment/SMOKE_CHECKS.md` and
`scripts/deployment/smoke-prod-demo.sh`.

The demo runbook may also ingest the local-demo knowledge base with
`python -m app.knowledge.ingest_demo --confirm-local-demo`. With
`RAG_ENABLED=true`, runtime grounding can attach bounded citations that the
workflow detail evidence panel displays. The frontend also includes lightweight
knowledge search and document catalog surfaces that use the existing backend
knowledge endpoints.

## Environment

Required local frontend variables:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The application should be available at:

```text
http://localhost:3000
```

## HTTP Route Checks

These checks can be performed in a browser, with curl, or through any local
HTTP smoke tool. Protected pages may render a login-required state when no
token is present.

| Route | Expected result |
| --- | --- |
| `/` | Public product bootstrap page renders. |
| `/login` | Login form renders with email, password, submit, and error/success states. |
| `/dashboard` | Authenticated shell renders, or login-required state renders if no token exists. |
| `/workflows` | Workflow table renders after login, or login-required state renders without token. |
| `/workflows/new` | Procurement workflow create form renders after login shell loads. |
| `/workflows/example-workflow-id` | Detail route renders an understandable not-found or load-error state after login. |
| `/workflows/dc5e7963-c2a4-5ad6-8f70-0741431597f0` | Seeded created workflow detail renders after login. |
| `/workflows/b0111d45-aff5-5b86-9ffd-9417704c9bab` | Seeded waiting-approval workflow renders with approval panel, empty approval history, event backlog, and timeline. |
| `/workflows/e1771f90-a85e-5684-98d1-7dd0458a4e89` | Seeded approved workflow renders with approval history and resume action. |
| `/workflows/6b99fd38-1ecf-5213-8d69-43abcca20856` | Seeded completed workflow renders approval/resume event history read-only. |

## Manual Smoke Checklist

### Login

- Open `/login`.
- Sign in with `manager@example.test` and `DemoPassword123!`.
- Confirm the success state appears with a link to `/dashboard`.
- Open `/dashboard`.
- Confirm the dashboard shell and navigation render.

### Navigation

- Confirm navigation labels are visible:
  - Dashboard
  - Workflows
  - Create Workflow
  - Runtime Events
- Confirm active navigation state is visible when moving between sections.
- Confirm the layout does not overflow on a narrow browser width.

### Workflow List

- Open `/workflows`.
- Confirm seeded workflows appear.
- Confirm IDs, domain/type, status, timestamps, and detail links fit within the
  table layout.
- Confirm no fake loaded data is shown.

### Workflow Detail And Backlog

- Open `/workflows/b0111d45-aff5-5b86-9ffd-9417704c9bab`.
- Confirm status is `WAITING_APPROVAL`.
- Confirm request/state details are visible.
- Confirm the Evidence and citations panel is visible.
- If no RAG-enabled runtime evidence exists, confirm the panel says no
  retrieved evidence has been attached yet.
- Confirm persisted event backlog includes runtime/stage events.
- Confirm event payload previews are bounded and readable.

### Evidence And Knowledge Search

- After running a workflow with `RAG_ENABLED=true` and ingested demo knowledge,
  confirm the Evidence and citations panel shows populated citation cards.
- Confirm citation cards show source title, source type, citation label,
  excerpt, relevance score, stage, and document id.
- Confirm long excerpts remain bounded and do not break the layout.
- Confirm raw embeddings, raw vector payloads, raw prompts, provider payloads,
  secrets, and chain-of-thought fields are not displayed.
- Use Knowledge search with:

```text
procurement policy approval evidence
```

- Confirm populated search results appear after ingestion, or an honest empty
  state appears if no vector results are available.
- Confirm a 403 response shows a readable forbidden message.
- Confirm a 503 response shows a retrieval-unavailable message.
- Confirm Demo documents lists deterministic policy, contract, supplier,
  pricing, and compliance-checklist metadata.
- Confirm no upload UI, admin document-management UI, delete/edit controls, or
  ingestion trigger UI appears.

### Approval Panel And History

- On `/workflows/b0111d45-aff5-5b86-9ffd-9417704c9bab`, confirm the approval
  panel is visible.
- Confirm Approve, Reject, and Request changes buttons are visible.
- Select Reject without a comment and confirm the frontend shows that rejections
  require a comment.
- Optional non-final branch: select Request changes with a short comment and
  confirm approval history records the decision while the workflow remains
  `WAITING_APPROVAL`.
- Select Approve with a bounded comment.
- Confirm the workflow refreshes to `APPROVED`.
- Confirm approval history shows the final decision, actor, comment, previous
  status, next status, and decided timestamp.
- Confirm duplicate or invalid-state approval attempts show a readable 409
  conflict message.
- Sign in as `viewer@example.test` or another non-approval role and confirm a
  forbidden approval action shows an understandable 403 message. Backend RBAC
  remains authoritative.

### Resume Flow

- After approving the waiting workflow, confirm the Resume workflow action is
  visible.
- Select Resume workflow.
- Confirm the frontend calls `POST /api/v1/workflows/{workflow_id}/resume`; it
  must not call `/run` for resume.
- Confirm the workflow refreshes to `COMPLETED`.
- Confirm workflow detail, persisted events, and approval history refresh after
  resume.
- Confirm a completed/already-resumed workflow shows a readable 409 conflict if
  resume is attempted again.
- Open `/workflows/e1771f90-a85e-5684-98d1-7dd0458a4e89` to smoke a seeded
  resume-ready workflow without changing the primary live walkthrough workflow.
- Open `/workflows/6b99fd38-1ecf-5213-8d69-43abcca20856` to verify read-only
  completed approval/resume history.

### Live Timeline

- On the workflow detail page, confirm the timeline shows one of:
  - Stream connecting
  - Stream connected
  - Stream disconnected
  - Stream error
- If connected, leave the page open while running another workflow to observe
  live messages.
- Use the Reconnect button to verify manual reconnect behavior.
- Confirm malformed or missing events are not displayed as fake data.
- Confirm approval and resume events appear from persisted backend events after
  refresh. Live WebSocket streaming remains the existing SPEC-008 behavior.
- Confirm no fake streamed events are created when Redis or WebSocket delivery
  is unavailable.
- Confirm RAG grounding events remain ordinary persisted/live workflow events;
  the frontend does not create fake streamed evidence.

### Create Workflow

- Open `/workflows/new`.
- Use:

```text
Domain: it_equipment
Customer name: Acme Manufacturing Group
Request text: We would like to purchase 50 standard business laptops for a new operations team. We signed a master agreement in May 2026. Please provide your best quotation.
Items JSON: [{"name":"Standard business laptop","quantity":50}]
Metadata JSON: {"tags":{"source":"smoke-flow"},"attributes":{}}
```

- Submit the form.
- Confirm success displays the created workflow ID and a detail link.
- Open the created workflow detail page.

### Run Workflow

- On the created workflow detail page, select `Run workflow`.
- Confirm the button shows a running state.
- Confirm the runtime result appears.
- Confirm status reaches the expected waiting-for-approval behavior.
- Confirm events refresh after the run.
- Confirm the timeline remains visible.

### RBAC Check

- Clear the session with the dashboard logout action or browser local storage.
- Sign in as `sales@example.test` with `DemoPassword123!`.
- Open a workflow detail page and select `Run workflow`.
- Confirm the UI shows a clear denied message because Sales cannot run
  workflows.
- Optional: sign in as `viewer@example.test` and confirm read-only pages load.

## Screenshot Checklist

Capture these for final presentation if screenshots are needed:

- `/login` with local demo credentials entered, before submit.
- `/dashboard` after Manager/Admin login.
- `/workflows` showing seeded RFQ-001 workflows.
- Waiting-approval workflow detail with status and persisted event backlog.
- Timeline connection state on the workflow detail page.
- `/workflows/new` create form filled with RFQ-001-style data.
- Runtime result panel after selecting `Run workflow`.
- Approval panel on a `WAITING_APPROVAL` workflow.
- Approval history after approve or request changes.
- Evidence and citations panel with populated RAG citations, if RAG is enabled.
- Knowledge search results and demo document catalog after ingestion.
- Resume action and completed state after explicit resume.
- Timeline showing approval/resume events.
- RBAC denial message from a role that cannot run workflows.

## Auth And Session Expectations

- The frontend stores local MVP tokens in `localStorage`.
- REST calls attach the bearer token.
- WebSocket stream connections use the same access token as an `access_token`
  query parameter.
- Missing tokens should show login-required states or stream errors instead of
  fake loaded data.
- Expired or invalid tokens should be resolved by signing in again.

## Known Limitations

- No real LLM provider behavior yet.
- No document upload/indexing UI yet.
- No admin document-management UI yet.
- No admin user-management UI yet.
- No production deployment automation yet.
- No fake live events should be used to mask backend or Redis issues.
