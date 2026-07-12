# Enterprise Multi-Agent OS Frontend

Next.js dashboard foundation for Enterprise Multi-Agent OS.

This frontend currently provides the SPEC-009 foundation: project structure,
TypeScript, Tailwind CSS, shadcn/ui-compatible conventions, typed backend API
client helpers, and a local-development token session layer. Workflow business
pages and WebSocket event UI are deferred to later tasks.

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
npm run lint
npm run typecheck
npm test
npm run build
```

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

Deferred to later SPEC-009 tasks:

- Workflow list/detail/create/run UI
- WebSocket event timeline
- Full dashboard navigation

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

The minimal login page is available at:

```text
/login
```

It calls the existing backend `POST /api/v1/auth/login` endpoint and stores the
returned token pair. It does not navigate to or render workflow dashboard pages
yet.
