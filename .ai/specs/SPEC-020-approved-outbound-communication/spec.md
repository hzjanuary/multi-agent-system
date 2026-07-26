# SPEC-020 - Approved Outbound Communication

## Status

Planned / ready for review before implementation

## Product Objective

Prepare safe outbound communication generation after Manager/Admin approval and
explicit resume, without sending real email by default.

SPEC-020 separates approved communication drafts/previews from any future send
operation. It preserves the existing workflow rule: no customer-ready final
quote or outbound communication before human approval.

## Current Dependencies

- SPEC-003 auth and RBAC.
- SPEC-005 workflow state.
- SPEC-007 workflow APIs.
- SPEC-008 workflow events and timeline.
- SPEC-011 LLM provider abstraction, disabled runtime default.
- SPEC-012 human approval and explicit resume.
- SPEC-016 conversational sales and reference evidence safety boundaries.
- SPEC-017 workflow detail, Agent Monitor, approval/resume, and email preview
  UI surfaces.

## Target Architecture

```text
Workflow reaches WAITING_APPROVAL
  -> Manager/Admin approval
  -> explicit /resume
  -> Email Preview / Approved Communication Draft
  -> audit event for draft/preview
  -> optional future send command behind OUTBOUND_SEND_ENABLED
  -> audit event for send attempt/result
```

### Approval Boundary

Outbound communication must only be generated as customer-ready content after a
Manager/Admin approval decision and explicit resume. Rejected, failed,
cancelled, or unapproved workflows must not produce final customer
communication.

### Draft / Preview Vs Send Separation

Draft/preview generation and actual sending must be separate operations:

- Preview/draft: safe local artifact for review.
- Send: future explicit action behind its own feature flag and RBAC checks.

The default implementation should produce preview/file output only.

### Communication Payload Contract

A communication draft should include bounded fields such as:

- workflow id
- customer display name or local-demo placeholder
- subject
- body preview
- normalized items/add-ons
- approval decision reference
- reference evidence summary if explicitly available
- generated timestamp
- created by / role
- safety warnings

It must not include raw prompts, raw provider payloads, secrets, tokens,
cookies, raw embeddings, vector payloads, or chain-of-thought.

### Audit / Event Requirements

Any future draft/preview or send operation must emit persisted workflow events
with bounded payloads:

- draft created
- preview viewed or exported if implemented
- send requested if future sending exists
- send succeeded/failed if future sending exists

Audit events must not include secrets, provider payloads, SMTP/Gmail tokens, or
raw customer-sensitive attachments.

### Role / RBAC Requirements

Only authorized roles should create or send approved outbound communication.
Minimum future policy:

- Manager/Admin can approve.
- Manager/Admin can create/send final communication if sending is enabled.
- Sales may view or prepare draft only if explicitly authorized.
- Viewer cannot mutate drafts or sends.

### Telegram Customer Reply Boundary

Telegram sales replies remain intake/status messages unless a later approved
task explicitly connects approved communication. Telegram must not auto-send
final quotes after workflow completion by default.

### Email / Gmail / Provider Integration Boundary

Any provider integration must be future-scoped and opt-in:

- no real email by default
- no Gmail token in CI
- no committed secrets
- explicit provider documentation
- redacted logs
- retry and failure handling
- audit events

### Outbox / Service Design Options

Future implementation can choose one of:

- preview-only service in workflow state
- local file outbox for demo artifacts
- database outbox table with explicit migration
- provider-backed send service after approval

The first implementation should prefer preview/file behavior unless a later
task explicitly scopes persistence or provider sending.

### No Auto-Send Default

`OUTBOUND_SEND_ENABLED=false` must remain the default. Workflow runtime,
Telegram bridge, and frontend must not send real email automatically.

### Safety And Redaction

Outbound content must be bounded and redacted. Reference evidence may be cited
only as review support and must not be mislabeled as a guaranteed final price
unless a future approved quote contract defines that behavior.

## User Stories

### Manager Approves Before Communication

As a Manager, I want outbound customer communication to be blocked until I
approve the workflow so the system cannot issue autonomous final quotes.

### Operator Reviews A Draft

As a Sales operator, I want to review an approved communication preview after
resume so I can manually send or copy it according to demo policy.

### Viewer Observes Audit Trail

As a Viewer, I want to see that a draft was produced only after approval and
resume, without being able to send it.

### Future Gmail Provider Is Explicit

As an administrator, I want any Gmail/provider send capability to require
explicit configuration, secrets handling, RBAC, and audit events.

## Acceptance Criteria

- No outbound send before Manager/Admin approval.
- No auto-send from Telegram.
- No auto-send from workflow runtime.
- No real email by default.
- Draft/preview and send are separate operations.
- Any future send operation requires explicit feature flag, RBAC, and audit.
- No final quote before approval.
- No raw provider payload, prompt, token, cookie, secret, embedding, vector
  payload, or chain-of-thought is stored or displayed.
- Existing email preview behavior remains stable until explicitly changed.
- Stable demo remains deterministic and no-key.

## Safety Boundaries

- No outbound send before Manager/Admin approval.
- No auto-send from Telegram.
- No auto-send from workflow runtime.
- No real email by default.
- No customer data beyond local demo fixtures.
- No final quote before approval.
- No raw provider payload/prompt/secret leakage.
- Explicit audit event required for any future send/draft.
- No Gmail/provider key in CI.
- No committed email credentials or OAuth tokens.

## Feature Flags And Configuration

- `OUTBOUND_COMMUNICATION_ENABLED=false`
- `OUTBOUND_SEND_ENABLED=false`
- `OUTBOUND_PROVIDER=preview|file|gmail_future`
- `OUTBOUND_REQUIRE_APPROVAL=true`
- Optional future provider variables must be local-only and absent from CI
  unless tests use placeholders.

## Non-Goals

- Real email sending in the first implementation.
- Gmail OAuth integration unless a later task explicitly scopes it.
- Automatic Telegram final quote delivery.
- Automatic send after resume.
- Billing/payment integration.
- Digital signature.
- Customer identity management.
- Production notification service.
- Storing real customer data.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Draft is mistaken for sent email | Use explicit preview/draft labels and no-send defaults. |
| Workflow runtime sends accidentally | Keep send path outside runtime default and behind feature flags. |
| Telegram sends final quote automatically | Keep Telegram as intake/status channel until a future approved integration. |
| Secrets leak through provider integration | Redaction, local env only, no CI keys, and tests for sensitive markers. |
| Audit trail misses outbound actions | Require persisted events for draft/preview and any future send attempts. |

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
```

Implementation validation should include focused approval/resume/outbound tests,
then:

```bash
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/ci/all-gates.sh
git diff --check
```

## Suggested Task Order

1. TASK 020.1 - Communication Contract / Spec
2. TASK 020.2 - Approved Quote Preview / Draft Service Foundation
3. TASK 020.3 - Audit Events For Outbound Draft / Preview
4. TASK 020.4 - Optional Local File / Email-Preview Output Only
5. TASK 020.5 - Future Gmail / Provider Integration Planning
6. TASK 020.6 - Frontend Approved Communication Preview
7. TASK 020.7 - Final Validation And Docs
