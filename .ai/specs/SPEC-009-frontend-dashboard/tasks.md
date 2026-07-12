# SPEC-009 - Frontend Dashboard Tasks

## TASK 009.1 - Frontend Project Bootstrap

### Objective

Create the initial Next.js frontend project foundation without implementing
workflow-specific screens yet.

### Scope

- Add `frontend/` project using Next.js, React, TypeScript, Tailwind CSS, and
  shadcn/ui.
- Add package scripts for lint, typecheck, test, build, and dev server.
- Configure frontend environment variables for backend HTTP and WebSocket base
  URLs.
- Add basic app layout shell and global styling.
- Add initial test tooling if the selected frontend stack requires it.

### Deliverables

- `frontend/` project scaffold.
- Tailwind and shadcn/ui setup.
- TypeScript configuration.
- Package scripts and local environment example.
- Minimal smoke tests or build checks.
- README notes if needed.

### Acceptance Criteria

- Frontend project installs and builds.
- Next.js app starts locally.
- Tailwind CSS and shadcn/ui are usable.
- No workflow business screens are implemented yet.
- No backend code, migrations, or model changes are made.

### Out-of-scope

- Workflow API client.
- Auth/session implementation.
- Dashboard pages.
- WebSocket event streaming.
- Backend changes.
- Real LLM/Agent/RAG/frontend approval behavior.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
git diff --check
```

## TASK 009.2 - Frontend API Client and Auth Session

### Objective

Implement typed frontend client utilities for backend auth/workflow APIs and
local MVP token session handling.

### Scope

- Define TypeScript DTOs aligned with existing backend auth and workflow
  response shapes.
- Add an API client layer for REST calls.
- Add login/logout/current-user helpers.
- Store access and refresh tokens for local development MVP.
- Attach bearer tokens to authenticated REST requests.
- Add error handling for 401, 403, 404, and validation failures.

### Deliverables

- Frontend API client module.
- Auth/session helper module.
- TypeScript DTOs for existing backend responses.
- Unit tests for API client/session behavior.
- README notes if needed.

### Acceptance Criteria

- Login client calls `POST /api/v1/auth/login`.
- Authenticated REST calls include `Authorization: Bearer <token>`.
- Workflow clients exist for create, list, get, run, and event-list endpoints.
- Error responses produce bounded UI-safe errors.
- No backend endpoints are invented.

### Out-of-scope

- Login UI screen.
- Dashboard rendering.
- WebSocket client.
- Backend auth changes.
- User/role management UI.
- Global response envelope migration.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

## TASK 009.3 - Dashboard Layout and Navigation

### Objective

Create the authenticated dashboard shell and navigation structure.

### Scope

- Implement login route/screen using TASK 009.2 auth helpers.
- Implement authenticated dashboard layout.
- Add navigation for workflows and workflow creation.
- Add current-user display and logout action.
- Add loading, empty, and error state primitives.
- Keep the layout responsive and desktop-first.

### Deliverables

- Login page.
- Dashboard layout and navigation components.
- Authenticated route guard/session handling.
- Shared UI state components.
- Component and route smoke tests.

### Acceptance Criteria

- Unauthenticated users see the login experience.
- Successful login creates a frontend MVP session.
- Authenticated users can access the dashboard shell.
- Logout clears the MVP session.
- UI uses Tailwind and shadcn/ui consistently.

### Out-of-scope

- Workflow list/detail implementation.
- Workflow creation/run actions.
- WebSocket event timeline.
- Backend changes.
- Production auth hardening beyond MVP session behavior.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

## TASK 009.4 - Workflow List and Detail Pages

### Objective

Implement workflow browsing views backed by existing workflow REST APIs.

### Scope

- Add workflow list page using `GET /api/v1/workflows`.
- Add workflow detail page using `GET /api/v1/workflows/{workflow_id}`.
- Add persisted event list loading through
  `GET /api/v1/workflows/{workflow_id}/events`.
- Display workflow status, request summary, current step/stage, and event
  history.
- Add loading, empty, 401/403/404, and generic error states.

### Deliverables

- Workflow list page/components.
- Workflow detail page/components.
- Event history component using persisted events.
- Tests for render states and client integration boundaries.

### Acceptance Criteria

- Workflow list loads from the backend client layer.
- Workflow detail loads one workflow by id.
- Persisted events display in deterministic order provided by the backend.
- 401/403/404 states are handled without raw internal payload exposure.
- No run/create behavior is implemented in this task.

### Out-of-scope

- Workflow create form.
- Run workflow action.
- WebSocket live streaming.
- Approval or resume UI.
- Backend changes.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

## TASK 009.5 - Workflow Create and Run Actions

### Objective

Implement procurement quotation workflow creation and runtime run actions using
existing backend endpoints.

### Scope

- Add workflow creation form for manual procurement request text.
- Build a backend-compatible `WorkflowCreateRequest` payload.
- Call `POST /api/v1/workflows`.
- Add run action on workflow detail for users who attempt runtime execution.
- Call `POST /api/v1/workflows/{workflow_id}/run`.
- Display returned runtime result, status, and waiting-for-approval state.
- Handle backend RBAC failures cleanly.

### Deliverables

- Workflow creation page/form.
- Create workflow client integration.
- Run workflow button/action.
- Runtime result display.
- Tests for create/run success and error states.

### Acceptance Criteria

- The frontend can create a procurement quotation workflow using the existing
  backend workflow create endpoint.
- The frontend can run a workflow using the existing `/run` endpoint.
- Admin/Manager run success and RBAC failure states are represented according
  to backend responses.
- The UI does not imply real Agent, LLM, RAG, approval, or email behavior.
- No backend code is changed.

### Out-of-scope

- `/resume`.
- Approval/rejection UI.
- Document uploads.
- Real pricing/compliance/retrieval behavior.
- WebSocket live timeline.
- Backend changes.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

## TASK 009.6 - WebSocket Event Timeline

### Objective

Implement live workflow event delivery in the workflow detail view using the
existing SPEC-008 WebSocket stream endpoint.

### Scope

- Add WebSocket client/hook for
  `WS /api/v1/workflows/{workflow_id}/stream`.
- Authenticate the stream with the access token using the supported SPEC-008
  mechanism.
- Merge persisted/backlog events and live stream messages into a timeline.
- Display stage progress for planning, retrieval, quotation, compliance,
  validation, and waiting approval.
- Add reconnect-safe behavior that can reload persisted events when the stream
  reconnects.
- Add safe error/disconnected states.

### Deliverables

- WebSocket client/hook.
- Runtime progress/timeline component.
- Event stream viewer.
- Tests for message handling, reconnect/backlog behavior, and safe rendering.

### Acceptance Criteria

- Workflow detail can subscribe to the existing WebSocket stream.
- Backlog/persisted events and live events display through one timeline.
- Stream errors and disconnects are visible but bounded.
- Messages are treated as safe DTOs, not backend internals.
- No SSE endpoint or backend stream changes are introduced.

### Out-of-scope

- Server-sent events.
- Multi-workflow fanout dashboard.
- Real LLM token streaming.
- Agent thought streaming.
- `/resume` or approval continuation.
- Backend changes.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```

## TASK 009.7 - Frontend UX Hardening and SPEC-009 Final Review

### Objective

Harden the first frontend dashboard and verify SPEC-009 is complete, bounded,
and ready to close.

### Scope

- Review all SPEC-009 acceptance criteria.
- Add or strengthen tests for login, route guard behavior, API client errors,
  workflow list/detail, create/run actions, and WebSocket timeline behavior.
- Verify responsive desktop-first layout and basic mobile behavior.
- Verify loading, empty, error, disconnected, and RBAC-denied states.
- Verify no unimplemented backend endpoint is called.
- Verify no frontend claims unsupported real Agent/LLM/RAG/approval/email
  behavior.
- Update docs and handoff for the next spec.

### Deliverables

- Hardened frontend tests.
- README or frontend docs updates where useful.
- SPEC-009 final review evidence.
- Harness durable trace.

### Acceptance Criteria

- SPEC-009 frontend flows work against the existing backend contract.
- Frontend lint, typecheck, tests, and build pass.
- Browser smoke verification passes for login/dashboard/workflow detail where
  practical.
- No backend code, migrations, or model changes are introduced.
- No out-of-scope frontend features are added.

### Out-of-scope

- Real Agents, LLM providers, RAG, document indexing, approval continuation,
  `/resume`, admin role management, production deployment, analytics, billing,
  and mobile-native app behavior.

### Validation Commands

```bash
git status --short
docker-compose config
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
git diff --check
```
