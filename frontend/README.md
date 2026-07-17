# Enterprise Multi-Agent OS Frontend

Next.js dashboard foundation for Enterprise Multi-Agent OS.

This frontend currently provides the SPEC-009 foundation: project structure,
TypeScript, Tailwind CSS, shadcn/ui-compatible conventions, typed backend API
client helpers, a local-development token session layer, the first authenticated
dashboard shell, workflow list/detail pages, and workflow create/run actions.
Workflow detail pages now include a live WebSocket event timeline backed by the
existing SPEC-008 stream endpoint and a SPEC-012 approval/resume panel backed by
the existing approval and resume workflow endpoints. SPEC-013 adds read-only
knowledge search/catalog clients and a workflow evidence panel for bounded RAG
citations already attached by the backend runtime.

## Requirements

- Node.js 20 or later
- npm

## Environment

Copy the example environment file:

```bash
cp .env.example .env.local
```

Configured variables:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/api/v1
```

Do not put secrets in `NEXT_PUBLIC_*` variables. They are exposed to the
browser by design.

Deployment environment profiles and production-demo public URL templates are
documented in `../docs/deployment/ENVIRONMENT.md`.

The production-demo frontend image is built by `Dockerfile` and the additive
Compose stack in `../docker-compose.prod.yml`. `NEXT_PUBLIC_API_BASE_URL` and
`NEXT_PUBLIC_WS_BASE_URL` are passed during image build and also documented as
runtime public values; do not place secrets in them.

## Install

```bash
npm install
```

## Development

```bash
npm run dev
```

The app starts at:

```text
http://localhost:3000
```

## Quality Checks

```bash
bash ../scripts/ci/frontend-gate.sh
```

Or run the frontend checks individually:

```bash
npm run lint
npm run build
npm run typecheck
npm test
```

Run `npm run build` and `npm run typecheck` serially. Running them in parallel
can race on generated `.next/types`.

## Current Scope

Implemented in TASK 009.1:

- Next.js App Router foundation
- TypeScript configuration
- Tailwind CSS configuration
- shadcn/ui-compatible `components/ui` and `lib/utils.ts` structure
- Static placeholder dashboard shell

Implemented in TASK 009.2:

- Runtime config helpers for `NEXT_PUBLIC_API_BASE_URL` and
  `NEXT_PUBLIC_WS_BASE_URL`
- Fetch-based typed API client
- Auth API helpers for login, refresh, logout, and current user
- Local-development MVP token storage helpers
- Minimal `/login` page
- Unit tests for URL construction, token attachment, error handling, auth
  endpoint usage, and session storage helpers

Implemented in TASK 009.3:

- Authenticated dashboard shell at `/dashboard`
- Navigation links for Dashboard, Workflows, Create Workflow, and Runtime Events
- Placeholder routes for `/workflows`, `/workflows/new`, and `/events`
- Login-required dashboard state when no local access token exists
- Local logout action that clears the MVP session
- Component smoke tests for dashboard shell, navigation, and logout behavior

Implemented in TASK 009.4:

- Workflow API client helpers for list, detail, and persisted event reads
- Backend-aligned workflow DTO refinements
- `/workflows` list page backed by `GET /api/v1/workflows`
- `/workflows/[workflowId]` detail page backed by
  `GET /api/v1/workflows/{workflow_id}`
- Read-only recent persisted events loaded from
  `GET /api/v1/workflows/{workflow_id}/events`
- Loading, empty, login-required, 403, 404, and generic error states
- Unit/component tests for workflow client paths, bearer token attachment,
  list rendering, detail rendering, empty states, and bounded API errors

Implemented in TASK 009.5:

- Workflow API client helpers for `POST /api/v1/workflows` and
  `POST /api/v1/workflows/{workflow_id}/run`
- `/workflows/new` procurement quotation create form
- Backend-compatible workflow creation payload construction from manual request
  text, items JSON, and metadata JSON
- Runtime run action on workflow detail pages
- Runtime result display for waiting-for-approval behavior
- Loading, validation, success, 401, 403, 409, and generic error states for
  create/run flows
- Unit/component tests for create payload shape, bearer-token attachment,
  create form validation, create success/error states, run success, and run
  conflict errors

Implemented in TASK 009.6:

- WebSocket event stream client using `NEXT_PUBLIC_WS_BASE_URL`
- `access_token` query parameter authentication for
  `WS /api/v1/workflows/{workflow_id}/stream`
- Unified workflow event timeline that merges persisted REST event backlog and
  live stream messages
- Deduplication by `event_id`
- Connection states for connecting, connected, disconnected, and error
- Manual reconnect action
- Safe malformed-message handling and bounded payload previews
- Unit/component tests for URL construction, message parsing, deduplication,
  connection state rendering, no-token behavior, malformed messages, and socket
  cleanup

Implemented in TASK 012.5:

- Workflow API client helpers for
  `POST /api/v1/workflows/{workflow_id}/approval`,
  `GET /api/v1/workflows/{workflow_id}/approval/history`, and
  `POST /api/v1/workflows/{workflow_id}/resume`
- Backend-aligned approval decision, approval history, and resume DTO types
- Workflow detail approval panel for approve, reject, and request changes
- Explicit post-approval resume action that calls `/resume`, not `/run`
- Approval history rendering on workflow detail pages
- Refresh of workflow detail, persisted events, and approval history after
  approval or resume actions
- Loading, validation, 401, 403, 404, 409, and generic error states for
  approval/resume flows
- Unit/component tests for request shapes, bearer-token attachment, approval
  actions, comment validation, history rendering, resume behavior, and
  backend-authoritative error handling

Implemented in TASK 013.6:

- Knowledge API client helpers for `POST /api/v1/knowledge/search`,
  `GET /api/v1/knowledge/documents`, and
  `GET /api/v1/knowledge/documents/{document_id}`
- Backend-aligned knowledge document, retrieval result, and citation DTO types
- Workflow detail evidence/citations panel that reads bounded citation objects
  from `runtime_context.rag`, `outputs.evidence`, `stage_outputs`, and loaded
  grounding events when those events contain citation objects
- Lightweight knowledge search panel and demo document catalog display on the
  workflow detail page
- Empty, loading, 401, 403, 404, 422, 503, and generic error states for
  knowledge surfaces where applicable
- Unit/component tests for knowledge request shapes, bearer-token attachment,
  evidence extraction/rendering, sensitive raw-field suppression, search
  results, empty states, and catalog rendering

## Dashboard Shell

The dashboard shell is available at:

```text
/dashboard
```

It uses the MVP session token stored by `/login`. If no local access token is
present, the dashboard shows a login-required state with a link back to
`/login`.

Read-only workflow pages are available at:

```text
/workflows
/workflows/{workflow_id}
```

They call only existing backend read endpoints and attach the stored bearer
token. Workflow creation is available at `/workflows/new`, and workflow detail
pages include a run action that calls the existing backend `/run` endpoint and
a live event timeline that opens the existing workflow WebSocket stream.
Workflow detail pages also include human approval controls for
`WAITING_APPROVAL` workflows and an explicit post-approval resume action for
approved workflows. Approval and resume authorization is enforced by the
backend; frontend role hints are not treated as security decisions.
Workflow detail pages also include an evidence/citations panel and lightweight
knowledge search/catalog surfaces. Populated evidence requires backend RAG to
be explicitly enabled, demo knowledge to be ingested, and a workflow run to
attach citations. The frontend never fabricates evidence and does not expose
raw embeddings, raw vector payloads, prompts, or object-storage internals.

## Auth And API Client

The API client lives under:

```text
lib/api/
  client.ts
  auth.ts
  types.ts
```

The session helpers live in:

```text
lib/auth/session.ts
```

The MVP session stores access and refresh tokens in `localStorage` for local
development only. Production auth hardening, server-side cookies, route guards,
and refresh scheduling are deferred.

The workflow event stream uses the current access token as an `access_token`
query parameter because browser WebSocket clients cannot set arbitrary bearer
headers reliably.

The minimal login page is available at:

```text
/login
```

It calls the existing backend `POST /api/v1/auth/login` endpoint and stores the
returned token pair.

## Demo Runbook

The SPEC-010 local demo runbook and manual frontend smoke flow are documented
from the repository root:

```text
docs/demo/DEMO_RUNBOOK.md
docs/demo/FRONTEND_SMOKE_FLOW.md
```

They cover Docker startup, migrations, the explicit demo seed command, local
demo credentials, workflow list/detail/create/run checkpoints, live timeline
checks, optional knowledge ingestion, RAG evidence checks, approval/resume, and
troubleshooting.

For the production-demo package, use:

```text
docs/deployment/RUNBOOK.md
docs/deployment/DEMO_PACKAGE.md
docs/deployment/SMOKE_CHECKS.md
```

Those docs explain the production-demo Compose stack, public API/WS URL
alignment, no-key default mode, optional RAG evidence mode, and board-demo
smoke checklist.
