# SPEC-028 Tasks - LLM Runtime Hardening

## Task List

### TASK 028.1 - SPEC-028 Planning Intake And G1-G4 Audit

Status: Implemented.

Goal: Turn the roadmap item "LLM runtime hardening beyond the deterministic
defense path" into a bounded SPEC with an audited, evidence-backed gap list.

Scope:

- Confirm stable defaults and safety boundaries are unchanged.
- Audit the four gaps G1-G4 against the current source (see spec.md).
- Define acceptance criteria and a deterministic offline test plan.
- Confirm the SPEC-028 index placeholder is retired or reassigned.
- Update `.codex/HANDOFF.md`.

Acceptance criteria:

- SPEC-028 spec exists with audited G1-G4 findings.
- SPEC-028 tasks doc exists.
- SPEC index references SPEC-028 without number conflict.
- No production behavior changes are implemented in this task.

Validation:

```bash
git diff --check
git status --short
docker compose config
```

### TASK 028.2 - G1 Cancellation Propagation Hardening

Status: Implemented. Commit: `5a3e055`.

Goal: Prove cancellation propagates cleanly through the LLM service and
runtime, and persist a safe terminal state plus a bounded cancellation event
when the runtime loop is interrupted, without swallowing cancellation
semantics.

Scope:

- Extend runtime failure handling so `asyncio.CancelledError` interrupting
  `run_workflow()` or `resume_workflow_after_approval()` is recorded as a safe
  `CANCELLED` terminal transition (when the transition map permits) with a
  bounded cancellation event, then re-raised.
- Keep `LLMErrorCategory.CANCELLATION` documentation-only unless a future task
  changes it.
- Add tests for cancellation propagation from `LLMService.complete()` and from
  the retry backoff sleep.
- Add tests proving cancellation leaves no dangling intermediate status and no
  raw prompt, provider payload, or secret in state or events.
- Keep the deterministic defense path unchanged.

Acceptance criteria:

- Cancelled workflows end in a safe `CANCELLED` state with a bounded event.
- `CancelledError` is re-raised, never converted to `FAILED` or `ERROR`.
- No raw data is persisted for a cancelled run.
- All existing tests still pass.

Validation:

```bash
docker compose run --rm backend-test pytest backend/app/tests/test_llm_service.py backend/app/tests/test_runtime_service.py backend/app/tests/test_runtime_resume.py
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
git diff --check
```

### TASK 028.3 - G2 Deterministic Schema-Valid Fake LLM End-To-End

Status: Implemented. Commit: `26d6e5c`.

Goal: Make the Fake LLM client emit deterministic, schema-valid payloads for
the five runtime stage schemas so that `LLM_RUNTIME_ENABLED=true` with
`LLM_PROVIDER=fake` runs end-to-end offline, and prove it with a real
`LLMService` + `FakeLLMClient` integration test.

Scope:

- Extend `FakeLLMClient` to render deterministic minimal payloads for the five
  runtime stage schemas when request metadata carries a known stage and
  expected schema.
- Preserve generic Fake behavior for requests without runtime stage metadata.
- Route Fake stage payloads through the existing `parse_structured_output`
  validation path; do not bypass schema validation.
- Add an end-to-end integration test driving `run_workflow()` to
  `WAITING_APPROVAL` with `LLM_PROVIDER=fake`.
- Assert quotation is marked LLM-skipped and email preparation never calls the
  LLM.

Acceptance criteria:

- The five runtime stage outputs validate against their schemas.
- The workflow reaches `WAITING_APPROVAL` deterministically offline.
- Generic Fake-client tests remain valid.
- No real provider key or live network call is used.

Validation:

```bash
docker compose run --rm backend-test pytest backend/app/tests/test_llm_fake_client.py backend/app/tests/test_runtime_llm_integration.py
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
git diff --check
```

### TASK 028.4 - G3 Fallback Transparency In Stage Outputs And Events

Status: Implemented. Commit: `5483596`.

Goal: Surface fallback usage in the persisted stage output and in the safe
event payload with bounded keys, while remaining absent when fallback is
disabled or unused.

Scope:

- Copy bounded fallback flags (`llm_fallback_used`,
  `llm_fallback_from_provider`, `llm_fallback_error_category`) from response
  metadata into the persisted stage output in `_complete_llm_stage`.
- Extend the `_safe_stage_output` allowlist with the same bounded keys.
- Add runtime-level tests for fallback-visible and fallback-absent cases.
- Confirm default disabled path exposes no fallback keys.

Acceptance criteria:

- A stage completed via fallback is distinguishable in persisted state and in
  `workflow.node.completed` events.
- No fallback flags appear when fallback is disabled or unused.
- No behavior change when fallback is disabled (default).

Validation:

```bash
docker compose run --rm backend-test pytest backend/app/tests/test_runtime_service.py backend/app/tests/test_runtime_llm_integration.py backend/app/tests/test_llm_service.py
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
git diff --check
```

### TASK 028.5 - G4 Approval And Resume Boundary Invariant Tests

Status: Implemented. Commit: `2dcce86`.

Goal: Prove the approval boundary remains the single authority over resume.

Scope:

- Add integration tests where the LLM returns an approval package with
  `requires_human_review=false` and `decision_draft="ready_for_review"` and
  assert the workflow still stops at `WAITING_APPROVAL`.
- Add tests asserting explicit human approval and explicit resume remain
  mandatory regardless of `decision_draft`.
- Add tests asserting resume without approval records is still rejected.
- Tests only; no control-flow change is required.

Acceptance criteria:

- Favorable LLM output cannot skip approval or auto-resume.
- All existing approval/resume tests still pass.

Validation:

```bash
docker compose run --rm backend-test pytest backend/app/tests/test_runtime_resume.py backend/app/tests/test_runtime_llm_integration.py
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
git diff --check
```

### TASK 028.6 - Final Validation And Closeout

Status: Implemented. Closeout validation passed and closeout review is
complete; SPEC-028 is Approved / Closed.

Goal: Verify SPEC-028 deliverables, confirm boundaries held, and recommend
approval or rejection.

Scope:

- Verify TASK 028.2 through TASK 028.5 deliverables.
- Confirm stable defaults and safety boundaries are unchanged.
- Confirm no dependency, Docker/CI, API, database, Telegram, provider, outbound
  email, or final-quote changes were introduced.
- Run full validation.
- Update `.codex/HANDOFF.md`.

Acceptance criteria:

- SPEC-028 implementation tasks are complete or clearly deferred.
- Cancellation, Fake end-to-end, fallback transparency, and approval boundary
  hardening are proven by tests.
- Validation commands pass or failures are reported honestly.

Validation results:

- `docker compose run --rm backend-test pytest -q` passed: 816 passed,
  1 skipped.
- `docker compose run --rm backend-test ruff check .` passed.
- `docker compose run --rm backend-test black --check .` passed: 225 files
  would be left unchanged.
- `docker compose run --rm backend-test mypy app` passed: no issues in 223
  source files.
- `docker compose config` passed.
- `git diff --check` passed.
- `git status --short` reported only the intended SPEC-028 docs/spec/index/
  handoff changes.
- Known limitation: cancelled in-flight HTTP work via `asyncio.to_thread`
  remains unproven by tests and out of scope.

Validation:

```bash
docker compose run --rm backend-test pytest
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
docker compose config
git diff --check
```

## SPEC-028 Planning Deliverables

Implemented in this planning task:

- `.ai/specs/SPEC-028-llm-runtime-hardening/spec.md`
- `.ai/specs/SPEC-028-llm-runtime-hardening/tasks.md`
- `.ai/specs/SPEC_INDEX.md` updated

No backend behavior, LLM service behavior, provider behavior, runtime
behavior, API behavior, database schema/migration, Docker/Compose behavior, CI
behavior, dependency change, outbound send, real email, or final quote behavior
is implemented by the SPEC-028 planning task.

## Closeout Checklist For Planning

- [x] SPEC-028 spec exists.
- [x] SPEC-028 tasks doc exists.
- [x] SPEC index references SPEC-028 without number conflict.
- [x] Older SPEC-028 Deployment Guide placeholder is retired or reassigned.
- [x] Stable defaults and safety boundaries are preserved.
- [x] G1-G4 audit is evidence-backed.
- [x] Acceptance criteria are exact and testable.
- [x] Test plan is deterministic and offline.
- [x] Non-goals are explicit.
- [x] No product behavior changes are present.
