# Frontend Smoke Flow

Use this checklist after running the demo seed command from
`docs/demo/DEMO_RUNBOOK.md`.

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
| `/workflows/b0111d45-aff5-5b86-9ffd-9417704c9bab` | Seeded waiting-approval workflow renders with event backlog and timeline. |

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
- Confirm persisted event backlog includes runtime/stage events.
- Confirm event payload previews are bounded and readable.

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

- No `/resume` approval continuation yet.
- No real LLM provider behavior yet.
- No RAG or document upload/indexing UI yet.
- No admin user-management UI yet.
- No production deployment automation yet.
- No fake live events should be used to mask backend or Redis issues.
