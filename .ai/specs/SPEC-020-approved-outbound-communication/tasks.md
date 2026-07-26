# SPEC-020 Tasks - Approved Outbound Communication

## Task List

### TASK 020.1 - Communication Contract / Spec

Status: Implemented in Sprint 1.

Goal: Define the approved outbound communication contract before adding any
draft, preview, file, or provider behavior.

Scope:

- Define draft/preview fields, approval references, evidence summary rules,
  redaction rules, and audit event requirements.
- Define RBAC expectations for draft creation, send preparation, and future
  send operations.
- Preserve no-real-email default.

Acceptance criteria:

- Contract distinguishes draft/preview from send.
- Manager/Admin approval remains required.
- No runtime, API, DB, or provider behavior changes in this planning task.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added `backend/app/outbound/schemas.py` with preview-only contracts:
  `OutboundCommunicationChannel`, `OutboundCommunicationProvider`,
  `OutboundRecipient`, and `OutboundCommunicationPreview`.
- The schema rejects `is_sent=true`, `is_sendable=true`, `gmail_future`
  provider use, naive timestamps, and sensitive markers such as API keys,
  Authorization headers, raw prompts, provider payloads, tokens, secrets, and
  chain-of-thought.
- Preview fields are bounded and explicitly labeled with
  `communication_label="approved_outbound_preview"`.

### TASK 020.2 - Approved Quote Preview / Draft Service Foundation

Status: Implemented in Sprint 1.

Goal: Add a service foundation that can create approved communication drafts
only after approval/resume conditions are satisfied.

Scope:

- Check workflow status and approval history before draft creation.
- Produce bounded preview content only.
- Do not send email.
- Do not call Gmail or provider APIs.
- Do not auto-trigger from Telegram.

Acceptance criteria:

- Draft creation is blocked before approval.
- Draft creation is blocked for rejected/failed/cancelled workflows.
- Draft content contains no raw prompts, provider payloads, secrets, or
  chain-of-thought.

Validation:

```bash
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
git diff --check
```

Implementation:

- Added `backend/app/outbound/policies.py` with pure policy helpers requiring:
  - workflow status `COMPLETED`;
  - explicit approve decision evidence for the same workflow; and
  - explicit resume completion evidence.
- Added `backend/app/outbound/service.py` with
  `OutboundCommunicationService.build_preview(...)`.
- The service is disabled by default, blocks send-enabled configuration, only
  accepts provider `preview`, refuses approval bypass, and only extracts from
  explicit workflow state preview fields such as `email_preview`,
  `generated_email`, `outbound_preview`, `communication_preview`, and
  `final_response_preview`.
- No LLM, Tavily, RAG, Telegram, workflow runtime, provider, database, or
  network call is made.
- `send_preview(...)` exists only as a hard-disabled placeholder that raises
  `OutboundSendDisabledError`.

### TASK 020.3 - Audit Events For Outbound Draft / Preview

Status: Deferred after Sprint 1.

Goal: Ensure outbound draft/preview actions are auditable.

Scope:

- Define event types for draft created and preview generated/viewed if
  applicable.
- Persist bounded event payloads.
- Do not include secrets, provider payloads, tokens, or raw customer-sensitive
  attachments.

Acceptance criteria:

- Events appear in workflow timeline.
- Viewer can observe events but cannot mutate communication state.
- Event payloads are bounded and redacted.

Sprint 1 note:

- No audit/event writes were added because Sprint 1 has no API endpoint and no
  mutation path. Future implementation should add persisted bounded
  `workflow.outbound.preview_created` style events only when a caller invokes
  preview generation through an approved backend use case.

Validation:

```bash
docker compose run --rm backend-test pytest -q
git diff --check
```

### TASK 020.4 - Optional Local File / Email-Preview Output Only

Status: Deferred after Sprint 1.

Goal: Provide a no-send local output mode for approved communication previews.

Scope:

- Optionally write preview artifacts to local demo-safe files or existing
  preview state.
- Keep output local and non-production.
- Do not send email or call providers.
- Do not include secrets or real customer data.

Acceptance criteria:

- Output is clearly labeled preview-only.
- No SMTP/Gmail/provider dependency.
- No auto-send path.

Sprint 1 note:

- File output was not implemented. The current foundation returns an in-memory
  typed preview only.

Validation:

```bash
docker compose run --rm backend-test pytest -q
git diff --check
```

### TASK 020.5 - Future Gmail / Provider Integration Planning

Status: Deferred after Sprint 1.

Goal: Plan any future provider send integration before implementation.

Scope:

- Document OAuth/secret handling, RBAC, audit, retry, failure, and redaction
  requirements.
- Keep `OUTBOUND_SEND_ENABLED=false`.
- Do not implement Gmail/provider calls in this task.

Acceptance criteria:

- Provider integration remains future-scoped.
- No provider key is required in CI.
- Docs explicitly forbid auto-send by default.

Sprint 1 note:

- Gmail/provider sending remains future-scoped. `gmail_future` is present only
  as a reserved enum value and is rejected by the Sprint 1 preview schema.

Validation:

```bash
git diff --check
git status --short
```

### TASK 020.6 - Frontend Approved Communication Preview

Status: Deferred after Sprint 1.

Goal: Display approved communication preview/draft state after approval/resume
without adding send behavior.

Scope:

- Show preview-only labels.
- Keep approval/resume controls visible.
- Add send controls only if a later task explicitly enables them behind
  `OUTBOUND_SEND_ENABLED`.
- Do not fabricate draft content.

Acceptance criteria:

- Frontend makes draft vs sent status clear.
- No "email sent" or final-send claim is shown unless future backend evidence
  explicitly supports it.
- Viewer cannot mutate outbound communication.

Sprint 1 note:

- No frontend changes were made.

Validation:

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

### TASK 020.7 - Final Validation And Docs

Status: Pending after Sprint 1 review.

Goal: Close SPEC-020 with docs, validation, and handoff updates.

Scope:

- Update runbooks/operator docs for approved communication preview behavior.
- Confirm default demo still sends no real email.
- Run backend/frontend/full gates as applicable.

Acceptance criteria:

- SPEC-020 is ready for review/closure.
- No real email, auto-send, auto-approval, auto-resume, or pre-approval final
  quote behavior is introduced.
- Audit and RBAC expectations are documented.

Validation:

```bash
git status --short
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

## Sprint 1 Validation Evidence

Focused validation passed:

```bash
docker compose build backend-test
docker compose run --rm backend-test pytest app/tests/test_outbound_communication_schemas.py app/tests/test_outbound_communication_service.py app/tests/test_settings.py -q
docker compose run --rm backend-test ruff check app/outbound app/tests/test_outbound_communication_schemas.py app/tests/test_outbound_communication_service.py app/tests/test_settings.py
docker compose run --rm backend-test black --check app/outbound app/tests/test_outbound_communication_schemas.py app/tests/test_outbound_communication_service.py app/tests/test_settings.py
docker compose run --rm backend-test mypy app
```

Results:

- 28 focused tests passed.
- Ruff passed.
- Black check passed.
- MyPy passed with no issues in 222 source files.

Full validation passed:

```bash
docker compose config
docker compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
bash scripts/ci/backend-gate.sh
bash scripts/ci/all-gates.sh
git diff --check
git status --short
```

Results:

- Local Compose config passed.
- Production-demo Compose config passed.
- Focused outbound tests passed: 24 passed.
- Full backend pytest passed: 776 passed, 1 skipped.
- Ruff passed.
- Black check passed.
- MyPy passed with no issues in 222 source files.
- `bash scripts/ci/backend-gate.sh` passed.
- `bash scripts/ci/all-gates.sh` passed, including frontend gate,
  production-demo image build, and whitespace check.
- `git diff --check` passed.

## Sprint 1 Closeout Checklist

- [x] Backend outbound communication package exists.
- [x] Defaults keep outbound communication disabled.
- [x] `OUTBOUND_SEND_ENABLED=false` remains the default.
- [x] Real sending is impossible in Sprint 1.
- [x] Preview requires completed workflow status.
- [x] Preview requires explicit approval evidence for the same workflow.
- [x] Preview requires explicit resume completion evidence.
- [x] Preview uses explicit workflow state preview fields only.
- [x] No API endpoints were added.
- [x] No frontend changes were added.
- [x] No Telegram changes were added.
- [x] No workflow runtime changes were added.
- [x] No database models or migrations were added.
- [x] No LLM, Tavily, RAG, Gmail, SMTP, provider, or network calls were added.
- [x] No auto-send, auto-approval, auto-resume, or real email behavior was
  introduced.
