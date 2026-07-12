# Context Handoff

## Current Project Status

Closed specs:

- SPEC-001 Bootstrap Backend - Approved / Closed
- SPEC-002 Database Foundation - Approved / Closed
- SPEC-003 Authentication and RBAC - Approved / Closed
- SPEC-004 Storage Infrastructure - Approved / Closed
- SPEC-005 Workflow State - Approved / Closed
- SPEC-006 LangGraph Runtime - Approved / Closed
- SPEC-007 Workflow API Endpoints - Approved / Closed
- SPEC-008 Event Streaming - Approved / Closed

Current active spec:

- SPEC-009 Frontend Dashboard

## Current SPEC-009 Planning State

Planning files:

- `.ai/specs/SPEC-009-frontend-dashboard/spec.md`
- `.ai/specs/SPEC-009-frontend-dashboard/tasks.md`

Planned tasks:

- `TASK 009.1 - Frontend Project Bootstrap` - Approved
- `TASK 009.2 - Frontend API Client and Auth Session` - Implemented, awaiting review
- `TASK 009.3 - Dashboard Layout and Navigation`
- `TASK 009.4 - Workflow List and Detail Pages`
- `TASK 009.5 - Workflow Create and Run Actions`
- `TASK 009.6 - WebSocket Event Timeline`
- `TASK 009.7 - Frontend UX Hardening and SPEC-009 Final Review`

## TASK 009.1 Implementation State

Deliverables:

- `frontend/package.json`
- `frontend/next.config.mjs`
- `frontend/tsconfig.json`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/globals.css`
- `frontend/components.json`
- `frontend/components/ui/`
- `frontend/lib/utils.ts`
- `frontend/.env.example`
- `frontend/README.md`

Behavior:

- Adds a minimal Next.js App Router application.
- Uses TypeScript and Tailwind CSS.
- Prepares shadcn/ui-compatible aliases and folder structure.
- Adds a static branded placeholder dashboard page only.
- Documents local environment variables for the existing backend API and
  WebSocket base URLs.
- Does not call backend APIs, implement auth/session behavior, create workflow
  UI, run workflows, or open WebSocket connections.

## TASK 009.2 Implementation State

Deliverables:

- `frontend/lib/config.ts`
- `frontend/lib/api/client.ts`
- `frontend/lib/api/auth.ts`
- `frontend/lib/api/types.ts`
- `frontend/lib/auth/session.ts`
- `frontend/app/login/page.tsx`
- `frontend/tests/api-client.test.ts`
- `frontend/tests/session.test.ts`
- `frontend/vitest.config.ts`
- `frontend/README.md`

Behavior:

- Adds runtime config helpers for `NEXT_PUBLIC_API_BASE_URL` and
  `NEXT_PUBLIC_WS_BASE_URL`.
- Adds a fetch-based typed API client with bearer-token attachment,
  query-parameter support, and typed safe non-2xx errors.
- Adds auth helpers for existing backend endpoints:
  `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, and
  `GET /auth/me`.
- Adds local-development MVP token storage helpers backed by `localStorage`.
- Adds a minimal `/login` page that submits backend credentials, stores the
  returned token pair, and shows bounded success/error states.
- Adds focused Vitest coverage for API URL construction, token attachment,
  error handling, auth endpoint usage, and session helper behavior.
- Does not implement dashboard navigation, workflow list/detail/create/run UI,
  WebSocket client/timeline behavior, backend changes, migrations, models,
  Agents, LLM UI, RAG UI, or approval/resume UI.

## SPEC-009 Scope

- Next.js frontend application.
- TypeScript, Tailwind CSS, and shadcn/ui.
- API client layer for existing backend auth and workflow REST endpoints.
- WebSocket client layer for `WS /api/v1/workflows/{workflow_id}/stream`.
- Login, workflow list, workflow detail, create workflow, run workflow, and
  live event timeline flows.
- Procurement quotation demo focus using existing deterministic backend runtime
  behavior.

## SPEC-009 Deferrals

- Backend API changes or new backend endpoints.
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

## Next Task

- Review SPEC-009 planning files.
- Then implement `TASK 009.1 - Frontend Project Bootstrap` only after planning
  is approved.

## Expected SPEC-009 Planning Quality Gate

- `git status --short`
- `docker-compose config`
- `git diff --check`

Implementation tasks should add frontend lint, typecheck, test, build, and
browser smoke checks after the frontend project exists.

## Known Warnings

- Existing FastAPI/TestClient StarletteDeprecationWarning is non-blocking.
- LF/CRLF warnings from `git diff --check` are non-blocking when no whitespace
  errors are reported.

## Harness State

- SPEC-005 final review recorded and approved.
- SPEC-006 final review recorded and approved.
- SPEC-007 final review recorded and approved.
- SPEC-008 final validation approved with Harness intake #64 and trace #75.
- SPEC-009 planning recorded with Harness intake #65.
- TASK 009.1 implementation recorded with Harness intake #66.
- TASK 009.2 implementation recorded with Harness intake #67.
