# SPEC-012 - Human Approval and Workflow Resume

## Status

Draft

## Context

Enterprise Multi-Agent OS currently has a deterministic workflow foundation:

- SPEC-005 defines workflow state, lifecycle transitions, persisted workflow
  events, and audit behavior.
- SPEC-006 runs the LangGraph runtime from `CREATED` to `WAITING_APPROVAL` and
  deliberately defers `/resume`.
- SPEC-007 exposes authenticated workflow REST APIs and direct Pydantic
  responses.
- SPEC-008 streams persisted workflow events over WebSocket.
- SPEC-009 provides the workflow dashboard, detail page, run action, and live
  event timeline.
- SPEC-010 provides deterministic demo users, workflows, event history, and a
  board-ready runbook.
- SPEC-011 adds feature-flagged LLM support while keeping deterministic runtime
  behavior as the default.

SPEC-012 plans the first human approval and resume slice. It completes the
`WAITING_APPROVAL` lifecycle path without adding configurable BPMN, email
sending, document upload, RAG, production notifications, or provider-management
features.

## Product Goal

- Let authorized human users review a workflow that reached
  `WAITING_APPROVAL`.
- Support approval decisions:
  - approve
  - reject
  - request changes / needs revision only if it can fit existing lifecycle
    rules without a new status
- Persist approval decision history.
- Emit persisted workflow events for approval and resume actions.
- Deliver approval/resume events to connected clients through the existing
  SPEC-008 WebSocket path.
- Resume runtime execution after approval where the existing runtime design
  supports it.
- Keep deterministic demo behavior stable.
- Keep LLM runtime behavior behind the existing `LLM_RUNTIME_ENABLED` flag.

## Non-goals

- Full enterprise BPMN.
- Multi-step configurable approval chains.
- Email sending.
- Digital signatures.
- File or document upload.
- RAG or document grounding.
- Admin approval-policy builder UI.
- Production notification integrations.
- Provider-management UI.
- Billing or deployment behavior.
- New LLM provider behavior.
- Token streaming or agent thought streaming.

## Approval Lifecycle

Workflows enter `WAITING_APPROVAL` through the existing runtime path:

```text
CREATED -> PLANNING -> RETRIEVING -> CALCULATING
  -> CHECKING_COMPLIANCE -> VALIDATING -> WAITING_APPROVAL
```

The existing lifecycle already allows:

```text
WAITING_APPROVAL -> APPROVED
WAITING_APPROVAL -> REJECTED
WAITING_APPROVAL -> CANCELLED
APPROVED -> GENERATING_EMAIL
GENERATING_EMAIL -> COMPLETED
```

SPEC-012 should not change these rules unless implementation finds a small
blocking gap and a later task explicitly scopes it.

### Approve

When an Admin or Manager approves a workflow:

- workflow must exist
- workflow must currently be `WAITING_APPROVAL`
- workflow must not already have a final approval decision
- approval decision is persisted
- workflow status transitions through `WorkflowService` to `APPROVED`
- a persisted `WorkflowEvent` is appended, for example
  `workflow.approval.approved`
- service-level audit behavior records the decision
- caller owns the transaction boundary through the API route

After approval, resume may be explicit through a separate endpoint or combined
only if a task provides a clear reason. The planning default is separate
approval and resume endpoints.

### Reject

When an Admin or Manager rejects a workflow:

- workflow must exist
- workflow must currently be `WAITING_APPROVAL`
- workflow must not already have a final approval decision
- rejection comment/reason is required
- approval decision is persisted
- workflow status transitions through `WorkflowService` to `REJECTED`
- a persisted `WorkflowEvent` is appended, for example
  `workflow.approval.rejected`
- resume is not allowed
- no email preview is generated

`REJECTED` remains terminal.

### Request Changes

Request changes is useful product behavior but does not currently have a
dedicated lifecycle status. SPEC-012 should treat it conservatively:

- Plan a request-changes decision contract only if it can be represented as
  bounded approval metadata and a workflow event while leaving status at
  `WAITING_APPROVAL`.
- Do not invent a new `NEEDS_REVISION` status in this spec unless a later
  implementation task explicitly adds lifecycle tests and, if needed, a
  migration/model review.
- Do not resume after request changes.
- Frontend should present it only if backend scope implements it; otherwise
  document it as deferred.

### Duplicate And Terminal Protection

Approval service logic should prevent:

- duplicate final approval decisions for the same workflow
- approving/rejecting a workflow outside `WAITING_APPROVAL`
- approving/rejecting terminal workflows
- resuming rejected, failed, cancelled, or completed workflows
- direct ORM status mutation outside `WorkflowService`

## RBAC Policy

SPEC-012 uses existing roles and dependencies. It must not add roles or change
the role model.

| Role | Approval decision | Resume | Read approval history |
| --- | --- | --- | --- |
| Admin | Approve/reject | Allowed | Allowed |
| Manager | Approve/reject | Allowed | Allowed |
| Sales | Not allowed | Not allowed | Allowed through workflow read |
| Legal | Review/comment deferred | Not allowed | Allowed through workflow read |
| Finance | Review/comment deferred | Not allowed | Allowed through workflow read |
| Viewer | Read-only | Not allowed | Allowed through workflow read |

Legal/Finance review comments are a future extension unless a later SPEC-012
task scopes a read-only/comment-only event that does not alter approval
decision state.

## Backend Contracts

Planned schemas should live near existing workflow API schemas and use
Pydantic v2.

Suggested approval decision request:

```json
{
  "decision": "approve",
  "comment": "Looks good for customer response.",
  "request_changes": null
}
```

Suggested decision values:

```text
approve
reject
request_changes
```

Suggested response:

```json
{
  "workflow": {},
  "approval": {
    "decision_id": "uuid-or-event-id",
    "workflow_id": "uuid",
    "decision": "approve",
    "comment": "bounded string",
    "decided_by_id": "uuid",
    "decided_at": "datetime"
  }
}
```

Resume response should reuse or mirror the existing `WorkflowRunResponse` style
and remain a direct Pydantic response. SPEC-012 must not introduce a global
response envelope.

Expected error behavior:

| Condition | Expected behavior |
| --- | --- |
| Missing workflow | `404` |
| Not authenticated | `401` |
| Authenticated but forbidden | `403` |
| Workflow not `WAITING_APPROVAL` for decision | safe `409` |
| Duplicate final decision | safe `409` |
| Invalid lifecycle transition | existing safe `409` mapping |
| Terminal workflow | safe `409` |
| Invalid request payload | FastAPI/Pydantic `422` |

Error details must not expose ORM internals, raw state payloads, secrets, raw
LLM provider payloads, or unbounded comments.

## Persistence Strategy

Preferred MVP persistence uses existing durable foundations:

- `Workflow.state_payload` for a current approval summary and bounded
  approval history.
- `WorkflowEvent` for append-only approval/resume decision events.
- `AuditLog` through existing workflow service/audit patterns for decision and
  lifecycle evidence.

This keeps SPEC-012 small and avoids migrations unless queryability proves
insufficient.

Implementation tasks should assess whether a new table is necessary. A new
table is justified only if:

- approval decisions need independent query/filter behavior beyond workflow
  detail/history,
- workflow state payload plus workflow events cannot support duplicate
  prevention or audit needs safely,
- or future approval chains require relational constraints.

If a new table is introduced in a later task, it must be planned with a
migration, repository/service tests, and rollback-safe behavior. Planning
default: no model or migration changes.

## Runtime Resume Strategy

Existing `/run` remains unchanged and continues to start only from `CREATED`.

Planned new endpoint:

```text
POST /api/v1/workflows/{workflow_id}/resume
```

Resume behavior should be bounded:

- require workflow status `APPROVED`
- require an approval decision record/event
- transition `APPROVED -> GENERATING_EMAIL` through `WorkflowService`
- execute only the post-approval continuation supported by the existing
  runtime design, initially `email_preparation`
- persist updated workflow state through `WorkflowService`
- append safe runtime/node/resume events through `WorkflowEventService`
- transition `GENERATING_EMAIL -> COMPLETED` when the deterministic
  email-preparation placeholder completes
- keep email sending out of scope
- preserve `LLM_RUNTIME_ENABLED` behavior for any LLM-assisted runtime path
  without requiring real provider keys

Resume should not redesign LangGraph or introduce arbitrary graph jumping.
Implementation should prefer a narrow runtime method such as
`RuntimeService.resume_workflow_after_approval()` with an explicit
post-approval stage list rather than modifying `/run`.

If email preparation cannot be safely resumed without larger runtime changes,
SPEC-012 tasks should implement approval decisions first and keep resume
explicitly blocked with a safe error until the runtime continuation task
finishes.

## Event Streaming

Approval and resume actions should append persisted `WorkflowEvent` records
such as:

```text
workflow.approval.requested
workflow.approval.approved
workflow.approval.rejected
workflow.approval.changes_requested
workflow.runtime.resumed
workflow.node.started       agent_name=email_preparation
workflow.node.completed     agent_name=email_preparation
workflow.runtime.completed
```

Because `WorkflowEventService` already publishes stream messages after
persistence, no second streaming mechanism is needed. WebSocket clients should
receive approval/resume events through the existing workflow stream.

Payload rules:

- include workflow id, decision, actor id/type, status, stage when relevant,
  and bounded comment summary
- do not include raw state payloads, raw request dumps, secrets, tokens, raw
  LLM payloads, full prompts, or hidden reasoning
- preserve deterministic event ordering

## Frontend UX

The workflow detail page should add approval/resume UI without replacing the
existing run panel or timeline.

Planned components:

- approval panel visible when workflow status is `WAITING_APPROVAL`
- approve/reject buttons for users who appear eligible, with backend 403
  handling as the source of truth
- bounded comment field
- optional request-changes control only if backend supports it
- approval history/readback section using workflow detail/events
- resume action visible after approved status if resume is separate
- timeline rendering for approval and resume events

Frontend behavior:

- use existing token/session helpers
- add typed API client functions for approval and resume endpoints
- handle loading, success, 401, 403, 404, 409, and generic error states
- refresh workflow detail/events after approval or resume
- do not fake approval success
- do not implement admin policy builder UI
- do not implement email sending UI

## Demo And Runbook

SPEC-012 should update the local demo after implementation:

1. Log in as Manager or Admin.
2. Open a seeded `WAITING_APPROVAL` workflow.
3. Review workflow status, approval package/state, persisted event backlog, and
   timeline connection state.
4. Approve the workflow with a bounded comment.
5. Resume the workflow if the endpoint is implemented separately.
6. Observe `GENERATING_EMAIL` and `COMPLETED` state transitions where the
   deterministic continuation is implemented.
7. Observe approval/resume events in the timeline.
8. Optionally show Sales or Viewer receiving 403 for approval/resume actions.

Seed updates should remain deterministic and local-demo safe. Existing seeded
workflows should remain compatible with the current list/detail/run demo.

## Testing Strategy

Backend tests:

- approval contract/schema validation
- lifecycle helpers for approval decision rules
- approval service approve/reject/request-changes behavior
- duplicate decision prevention
- terminal workflow protection
- workflow event append behavior
- audit evidence behavior
- transaction boundaries and no service-level commit
- API success paths and error mapping
- Admin/Manager allowed; Sales/Legal/Finance/Viewer denied for decisions
- resume success path from `APPROVED`
- resume rejection for non-approved, rejected, terminal, or missing workflows
- runtime continuation event/state behavior
- no email sending
- no LLM live provider calls

Frontend tests:

- approval API client request shapes
- approval panel rendering by workflow status
- approve/reject loading/success/error states
- 401/403/409 handling
- resume action behavior
- timeline rendering of approval/resume events
- no fake successful approval/resume data

Validation should not require live LLM keys, live provider network access, or
external services beyond existing Docker test services.

## Risks And Decisions

- Persistence may need a new approval table later. Default to existing
  `Workflow.state_payload`, `WorkflowEvent`, and `AuditLog`; require explicit
  evidence before adding migrations.
- Request changes lacks a dedicated lifecycle status. Keep it as a bounded
  non-final decision/event or defer it.
- Resume could become a generic graph jumping problem. Keep it to
  post-approval `email_preparation` continuation only.
- Frontend role awareness is not authoritative. The backend remains source of
  truth for 403 decisions.
- Real email generation/sending is out of scope; completed state should reflect
  placeholder email-preparation only until email agent specs implement content.

## User Stories

### US-014 - Manager Approves Workflow

As a Manager, I want to approve a workflow waiting for approval so that it can
continue to the post-approval runtime path.

### US-015 - Manager Rejects Workflow

As a Manager, I want to reject a workflow with a comment so that the requester
understands why it will not proceed.

### Approval Auditability

As an Admin, I want approval and resume decisions recorded in workflow events
and audit logs so that human decisions are explainable.

### Approval Timeline

As a workflow reader, I want approval and resume events to appear in the
workflow timeline so that the full lifecycle is visible.

## Acceptance Criteria

```gherkin
Given a workflow is WAITING_APPROVAL
When an Admin or Manager approves it
Then the decision is persisted
And the workflow transitions to APPROVED through WorkflowService
And approval events and audit evidence are recorded
```

```gherkin
Given a workflow is WAITING_APPROVAL
When an Admin or Manager rejects it with a comment
Then the decision is persisted
And the workflow transitions to REJECTED through WorkflowService
And no resume or email preparation occurs
```

```gherkin
Given a workflow is not WAITING_APPROVAL
When an approval decision is submitted
Then the API returns a safe conflict error
And no invalid decision is persisted
```

```gherkin
Given a workflow is APPROVED
When an Admin or Manager resumes it
Then the runtime continues the bounded post-approval path
And workflow events are appended
And the workflow reaches COMPLETED if the continuation succeeds
```

```gherkin
Given a rejected or terminal workflow
When resume is requested
Then the API returns a safe conflict error
And no runtime continuation starts
```

```gherkin
Given approval or resume events are persisted
When the workflow WebSocket stream is connected
Then the frontend timeline receives safe stream messages through SPEC-008
```

## Validation Strategy

Planning-only validation for SPEC-012:

```bash
git status --short
docker-compose config
git diff --check
```

Implementation tasks should use backend and frontend quality gates as
appropriate:

```bash
git status --short
docker-compose config
docker-compose up -d postgres redis
docker-compose run --rm backend-test alembic upgrade head
docker-compose build backend-test
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

No automated validation should require real LLM credentials or external
provider network access.

## Out-of-scope List

- Full BPMN or configurable approval chains.
- Email sending.
- Digital signatures.
- File/document upload.
- RAG or document grounding.
- Admin approval-policy builder UI.
- Production notification integrations.
- Provider-management UI.
- Billing/deployment behavior.
- New LLM provider behavior.
- Token streaming.
- Agent thought streaming or hidden reasoning exposure.
- Arbitrary LangGraph jump/resume mechanics.
- Public approval policy management APIs.
