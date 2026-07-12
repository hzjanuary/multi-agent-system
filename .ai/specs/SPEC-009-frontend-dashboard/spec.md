# SPEC-009 - Frontend Dashboard

## Status

Draft

## Context

Enterprise Multi-Agent OS now has the backend foundation needed for a first
operator-facing dashboard:

- SPEC-005 provides durable workflow state, lifecycle, events, and audit
  integration.
- SPEC-006 provides deterministic LangGraph runtime execution and
  `POST /api/v1/workflows/{workflow_id}/run`.
- SPEC-007 provides authenticated workflow REST APIs.
- SPEC-008 provides a WebSocket event stream for live workflow progress.

SPEC-009 plans the first Next.js frontend dashboard that demonstrates workflow
creation, runtime execution, persisted workflow/event reads, and live event
streaming. The frontend should be demo-friendly, but bounded: it must consume
existing backend APIs instead of inventing new backend behavior.

## Goals

- Create a Next.js dashboard application using TypeScript, Tailwind CSS, and
  shadcn/ui.
- Implement a frontend API client layer for existing backend auth and workflow
  REST endpoints.
- Implement a WebSocket client layer for workflow event streaming.
- Support token-based login against the existing backend auth API.
- Show a workflow list and workflow detail view.
- Create a procurement quotation workflow from a simple request form.
- Run a workflow through the existing deterministic runtime endpoint.
- Display workflow status, stage progress, persisted events, and live streamed
  events in a timeline.
- Keep UI, API clients, auth/session helpers, routes, and domain types clearly
  separated.
- Keep the frontend generic enough for future workflow domains while using a
  procurement quotation demo as the MVP experience.

## Non-goals

- Backend API changes.
- New backend endpoints.
- Database migrations or model changes.
- Real LLM provider UI or configuration screens.
- RAG document upload or indexing UI.
- Human approval or `/resume` UI.
- Admin user or role management UI.
- Multi-tenant organization management.
- Advanced analytics.
- Production deployment.
- Payment or billing behavior.
- Mobile-native application.
- Complex design system beyond shadcn/ui basics.
- Procurement-specific runtime policy, approval decisioning, or agent logic.

## Frontend Architecture

SPEC-009 should add a `frontend/` application that follows the project
architecture contract:

```text
frontend/
  app/             Next.js routes and layouts
  components/      shared UI components
  features/        workflow/auth feature components
  lib/             API client, WebSocket client, auth/session helpers
  hooks/           client-side data and stream hooks
  services/        frontend orchestration helpers
  types/           TypeScript DTOs aligned with backend schemas
  styles/          global styles and Tailwind setup
  tests/           frontend tests
```

The frontend should use:

- Next.js with the App Router.
- React and TypeScript.
- Tailwind CSS.
- shadcn/ui components.
- A small typed API client for backend REST calls.
- A small WebSocket client/hook for workflow event streams.
- Local development configuration for backend HTTP and WS base URLs.

The implementation should avoid direct coupling between route components and
raw `fetch` calls. Backend DTOs should be represented by explicit TypeScript
types. UI components should receive typed props and should not know database or
backend ORM internals.

## Initial User Flows

SPEC-009 should cover these first user flows:

1. Login with email and password using the existing backend auth endpoint.
2. Persist an access token for the local development MVP session.
3. View a workflow list.
4. View workflow detail.
5. Create a procurement quotation workflow from manual request text.
6. Run a workflow with `POST /api/v1/workflows/{workflow_id}/run`.
7. Watch live workflow events through
   `WS /api/v1/workflows/{workflow_id}/stream`.
8. See workflow status and stage progress.
9. See persisted/backlog events after opening or reconnecting to a workflow
   stream.

## Backend Integration

SPEC-009 must use the existing backend endpoints:

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me

POST /api/v1/workflows
GET  /api/v1/workflows
GET  /api/v1/workflows/{workflow_id}
POST /api/v1/workflows/{workflow_id}/run
GET  /api/v1/workflows/{workflow_id}/events
WS   /api/v1/workflows/{workflow_id}/stream
```

The frontend must not depend on unimplemented backend endpoints such as
`/resume`, approval APIs, document upload/indexing APIs, audit query APIs, or
agent-specific APIs.

The current backend workflow APIs use direct Pydantic response models. The
frontend should model the response shapes that exist today and should not
assume the future global response envelope from `.ai/project/API_CONTRACT.md`
until a later API consistency spec implements it.

## UI Scope

SPEC-009 should implement:

- Auth/login screen.
- Authenticated dashboard layout.
- Navigation suitable for workflow operations.
- Workflow table/list with loading, empty, and error states.
- Workflow creation form for procurement quotation demo input.
- Workflow detail page.
- Run workflow action.
- Runtime progress/timeline component.
- Event stream viewer combining persisted backlog and live events.
- Basic responsive desktop-first layout.

The UI should be board/demo friendly without becoming a marketing landing page.
It should prioritize operational clarity: status, current stage, event history,
and next obvious action.

## Demo Focus

The first dashboard experience should demonstrate a procurement quotation
workflow. Stage labels should match the backend runtime/event foundation:

```text
planning
retrieval
quotation
compliance
validation
waiting approval
```

The UI may visually represent future `email_preparation`, but it must make clear
that email generation, approval continuation, and `/resume` are deferred. The
dashboard must not claim real retrieval, real pricing, real compliance, or real
email generation quality until later specs implement those Agents/tools.

## Auth And Session Behavior

The frontend should:

- Authenticate through the existing backend auth API.
- Store access and refresh tokens safely enough for local development MVP.
- Attach `Authorization: Bearer <access_token>` to REST requests.
- Use the SPEC-008 supported WebSocket auth path:
  `access_token` query parameter or a supported bearer mechanism.
- Read the current user through `GET /api/v1/auth/me`.
- Respect backend RBAC responses instead of re-implementing authorization
  policy as the source of truth.

SPEC-009 should not implement a new authentication backend, user registration,
role management, or fine-grained frontend permission engine.

## User Stories

### US-001 - Login UI Foundation

As a registered user, I want to log in through the frontend so that I can access
the workflow dashboard.

### US-003 - Create Procurement Workflow UI

As a Sales user, I want to create a procurement quotation workflow from manual
request text so that the backend can persist and run it.

### US-018 - View Workflow Progress Dashboard

As an authenticated workflow reader, I want to see workflow status, stage
progress, and event history so that I can understand runtime progress.

### US-019 - View Runtime Errors

As an Admin or workflow reader, I want workflow failure events to appear in the
detail view so that failed runs are understandable.

## Acceptance Criteria

```gherkin
Given the frontend app is running
When an unauthenticated user opens the dashboard
Then the user is sent to the login experience
```

```gherkin
Given a user submits valid login credentials
When the backend returns tokens
Then the frontend stores the MVP session
And authenticated API requests include a bearer token
```

```gherkin
Given an authenticated user opens the dashboard
When workflows exist
Then the workflow list is loaded from `GET /api/v1/workflows`
```

```gherkin
Given a Sales, Admin, or Manager user enters a procurement request
When the user submits the create workflow form
Then the frontend calls `POST /api/v1/workflows`
And navigates to or displays the created workflow
```

```gherkin
Given a workflow detail page is open
When an Admin or Manager runs the workflow
Then the frontend calls `POST /api/v1/workflows/{workflow_id}/run`
And shows the returned runtime result
```

```gherkin
Given a workflow has persisted events
When the detail page opens the stream
Then backlog events are displayed in the timeline
```

```gherkin
Given a workflow stream emits a new event
When the WebSocket message arrives
Then the event timeline updates without polling
```

```gherkin
Given the backend returns 401, 403, 404, or validation errors
When the frontend receives the response
Then the UI shows a bounded user-facing error state
And does not expose raw internal payloads
```

## Validation Strategy

Frontend implementation tasks should use frontend-focused checks once the app
exists, such as:

```bash
git status --short
docker-compose config
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

If the selected package manager or scripts differ after bootstrap, each task
must document and use the actual project scripts. Browser verification with a
local dev server and Playwright or an equivalent tool should be added for UI
tasks that change rendered behavior.

Planning-only validation for SPEC-009 is:

```bash
git status --short
docker-compose config
git diff --check
```

## Out-of-scope List

- Backend code changes.
- New backend endpoints.
- Database migrations or model changes.
- Real LLM provider UI.
- RAG document upload/indexing UI.
- Human approval or `/resume` UI.
- Admin user/role management UI.
- Multi-tenant organization management.
- Advanced analytics.
- Production deployment.
- Payment or billing.
- Mobile-native app.
- Complex design system beyond shadcn/ui basics.
- Real procurement policy, calculation, retrieval, compliance, validation, or
  email Agent logic.
