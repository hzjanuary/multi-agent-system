# SPEC-020 Tasks - Approved Outbound Communication

## Task List

### TASK 020.1 - Communication Contract / Spec

Status: Planned.

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

### TASK 020.2 - Approved Quote Preview / Draft Service Foundation

Status: Planned.

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

### TASK 020.3 - Audit Events For Outbound Draft / Preview

Status: Planned.

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

Validation:

```bash
docker compose run --rm backend-test pytest -q
git diff --check
```

### TASK 020.4 - Optional Local File / Email-Preview Output Only

Status: Planned.

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

Validation:

```bash
docker compose run --rm backend-test pytest -q
git diff --check
```

### TASK 020.5 - Future Gmail / Provider Integration Planning

Status: Planned.

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

Validation:

```bash
git diff --check
git status --short
```

### TASK 020.6 - Frontend Approved Communication Preview

Status: Planned.

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

Validation:

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

### TASK 020.7 - Final Validation And Docs

Status: Planned.

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
