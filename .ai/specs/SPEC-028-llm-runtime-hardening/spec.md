# SPEC-028 - LLM Runtime Hardening

## Status

Approved / Closed. TASK 028.2 through TASK 028.5 are implemented and validated
by the committed backend test suite; TASK 028.6 closeout validation passed and
closeout review is complete. The implementation changed LLM-assisted runtime
behavior only within the approved boundaries: G1 cancellation handling, G2
deterministic Fake stage outputs, and G3 fallback transparency. G4 was tests
only. No stable default or safety boundary changed.

## Product Objective

Harden the LLM-assisted runtime path introduced by SPEC-011 beyond the
deterministic defense path, without changing any stable default or safety
boundary. SPEC-028 covers the four concrete gaps identified in the TASK 011.7
follow-up audit:

- G1 cancellation propagation and dangling runtime state;
- G2 deterministic schema-valid Fake LLM end-to-end path;
- G3 fallback transparency in safe stage outputs and events;
- G4 approval and resume boundary invariant.

SPEC-028 preserves every SPEC-011 boundary: `LLM_RUNTIME_ENABLED=false` by
default, `LLM_PROVIDER=fake` by default, the deterministic defense path is
unchanged, no real provider keys are required for tests, no token/thought
streaming, no raw prompts/provider payloads/secrets in state or events, and
tests remain deterministic and offline.

## Context

SPEC-011 (closed) delivered the provider abstraction, LLM service boundary,
safe settings, structured-output strategy, and the feature-flagged runtime
integration. TASK 011.7 added two hardening fixes under its "tiny blocking
fixes" window:

- bounded exponential retry backoff with jitter in
  `backend/app/llm/service.py`;
- fake-fallback masking guard in `backend/app/runtime/service.py`.

A read-only audit of the remaining roadmap item "LLM runtime hardening beyond
the deterministic defense path" (`README.md` roadmap item 2) identified the four
gaps above. Each gap below records the audited current state with exact source
references, the required hardening, and its acceptance criteria.

## Stable Defaults And Boundaries To Preserve

The following must remain unchanged unless a future approved implementation
task explicitly changes them:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
LLM_MAX_RETRIES=2
LLM_TIMEOUT_SECONDS=30
LLM_FALLBACK_ENABLED=false
```

Safety boundaries preserved:

- the deterministic defense path (flag off) is unchanged;
- no real provider keys are required for tests or the local demo;
- no token or thought streaming;
- no raw prompts, provider payloads, secrets, tokens, or chain-of-thought in
  state, events, or logs;
- provider errors fail closed with bounded, redacted events;
- approval remains a mandatory human boundary before resume.

## Audit Findings

### G1 - Cancellation Propagation And Dangling Runtime State

Current state (verified read-only):

- `asyncio.CancelledError` is a `BaseException` in Python 3.8+, so it
  propagates through `LLMService.complete()` (`backend/app/llm/service.py`
  catches `LLMProviderError` then `Exception`) and through
  `RuntimeService.run_workflow()` (`backend/app/runtime/service.py` catches
  `Exception`). Cancellation is therefore never mislabeled as a provider
  failure today.
- `LLMErrorCategory.CANCELLATION` exists (`contracts.py`) and is classified
  non-retryable (`retry.py`), but no client ever raises it and no test
  exercises cancellation.
- Cancellation during `await self._sleep(backoff_delay_seconds(...))` in the
  retry loop propagates cleanly.
- `asyncio.to_thread` in `UrllibAsyncJSONHTTPTransport` (`clients/http.py`)
  does not stop the underlying urllib thread when the awaiting task is
  cancelled; the thread keeps running until its own `urlopen` timeout. No
  persisted state is produced by that thread, but the behavior is untested.
- Partial-state hazard: `run_workflow()` transitions workflow status per stage
  before executing the stage. Cancellation between a status transition and
  stage completion leaves the workflow in an intermediate status (for example
  `PLANNING`) with no terminal event and no safe cancellation record.
- `ALLOWED_WORKFLOW_TRANSITIONS` (`workflows/lifecycle.py`) permits every
  intermediate runtime status to transition to `CANCELLED` and `FAILED`, so a
  safe terminal transition is available.

Hardening required:

- prove cancellation propagates out of the LLM service and the runtime;
- persist a safe `CANCELLED` terminal state plus a bounded cancellation event
  when cancellation interrupts the runtime loop, then re-raise so cancellation
  semantics are preserved;
- prove cancelled in-flight HTTP work leaves no persisted effect. This
  sub-item was NOT implemented by SPEC-028: the `asyncio.to_thread` urllib
  thread behavior remains untested and is out of scope (see Non-Goals).

### G2 - Deterministic Schema-Valid Fake LLM End-To-End Path

Current state (verified read-only):

- `FakeLLMClient._content_for_request` (`clients/fake.py`) returns a generic
  payload (`provider`, `status`, `message_count`, `last_user_message`) for
  structured JSON requests.
- The five runtime stage schemas in `llm/structured_outputs.py` use
  `extra="forbid"` and require stage-specific fields (`summary`,
  `confidence`, `requires_human_review`, and per-stage fields).
- The generic Fake payload can never validate against any stage schema, so
  `LLM_RUNTIME_ENABLED=true` with `LLM_PROVIDER=fake` deterministically fails
  at the planner stage with `INVALID_RESPONSE` and the workflow ends `FAILED`.
- The runtime LLM integration tests currently inject a `ScriptedLLMService`
  double (`tests/test_runtime_llm_integration.py`) to avoid this; the real
  `LLMService` plus real `FakeLLMClient` is never exercised end-to-end through
  `run_workflow()`.
- SPEC-011 spec.md states the fake provider "should produce deterministic,
  typed outputs for unit tests, runtime integration tests, and local
  development"; the current fake output does not satisfy this for the runtime
  schemas.
- Runtime prompt builders already attach `stage` and `expected_schema` to
  request metadata (`llm/prompts/base.py`), giving the Fake client the
  information needed to render stage-shaped output without new contracts.

Hardening required:

- make the Fake client emit deterministic, schema-valid, minimal payloads for
  the five runtime stage schemas when request metadata carries a known stage;
- preserve the existing generic Fake behavior for requests without runtime
  stage metadata so existing fake-client tests remain valid;
- add an end-to-end integration test with the real `LLMService` +
  `FakeLLMClient` driving `run_workflow()` to `WAITING_APPROVAL`.

### G3 - Fallback Transparency In Safe Stage Outputs And Events

Current state (verified read-only):

- `_complete_with_fallback` (`llm/service.py`) records `fallback_used`,
  `fallback_from_provider`, and `fallback_error_category` in the response
  metadata.
- `_complete_llm_stage` (`runtime/llm_adapter.py`) copies only provider,
  model, request id, finish reason, and usage into the persisted stage output;
  response metadata (including fallback flags) is dropped.
- `_safe_stage_output` (`runtime/service.py`) uses an allowlist that does not
  include any fallback key.
- A stage completed via fallback is therefore indistinguishable from a normal
  provider call in persisted state and in `workflow.node.completed` events.

Hardening required:

- surface fallback usage in the persisted stage output and in the safe event
  payload using bounded keys;
- confirm fallback transparency is absent when fallback is disabled (default)
  and present only when a fallback actually occurred.

### G4 - Approval And Resume Boundary Invariant

Current state (verified read-only):

- the runtime always stops at `WAITING_APPROVAL`; `ApprovalPackageOutput`
  carries `decision_draft` and `requires_human_review` fields that the runtime
  does not consult for control flow;
- resume requires `validate_resume_allowed` with explicit approval records
  (`runtime/service.py`);
- existing tests cover rejection of resume without approval and after
  rejection, but no test asserts that favorable LLM output cannot skip
  approval or auto-resume.

Hardening required:

- prove that an approval package claiming `requires_human_review=false` and
  `decision_draft="ready_for_review"` still ends at `WAITING_APPROVAL`;
- prove that explicit human approval and explicit resume remain mandatory even
  with a favorable `decision_draft`.

## In-Scope Hardening

### G1 - Cancellation

- Runtime failure handling was extended so `asyncio.CancelledError` interrupting
  `run_workflow()` and `resume_workflow_after_approval()` is recorded as a
  safe `CANCELLED` terminal transition with a bounded event payload, and the
  original `CancelledError` is re-raised.
- Tests were added for cancellation propagation from `LLMService.complete()`
  and from the retry sleep.
- A test proves cancellation leaves no dangling intermediate status and no raw
  payload in state or events.

### G2 - Deterministic Fake End-To-End

- `FakeLLMClient` was extended to render deterministic minimal schema-valid
  payloads for the five runtime stage schemas when request metadata declares a
  known `stage` and `expected_schema`.
- The generic Fake payload is preserved for requests without runtime stage
  metadata.
- An end-to-end runtime integration test drives the real `LLMService` with
  `LLM_PROVIDER=fake` and `LLM_RUNTIME_ENABLED=true`.

### G3 - Fallback Transparency

- Bounded fallback flags were copied from response metadata into the persisted
  stage output and the `_safe_stage_output` allowlist was extended with the
  same bounded keys.
- Runtime tests were added for fallback-visible and fallback-absent cases.

### G4 - Approval And Resume Boundary

- Tests were added only; no control-flow change was made because the approval
  boundary is structurally intact.

## Out Of Scope / Non-Goals

- No change to `LLM_RUNTIME_ENABLED`, `LLM_PROVIDER`, or any stable default.
- No change to the deterministic defense path.
- No change to the fake-fallback masking guard or retry backoff added in
  TASK 011.7.
- No token or thought streaming.
- No structured logging layer (audit gap G5) in this SPEC.
- No raw-provider-body hardening (audit gap G6) in this SPEC.
- No reasoning-field payload tests (audit gap G7) in this SPEC.
- No proof that cancelled in-flight HTTP work via `asyncio.to_thread` leaves no
  persisted effect; the urllib thread behavior remains untested (audit gap G1
  sub-item).
- No per-run deadline setting.
- No retry-on-fallback behavior.
- No new settings, environment variables, database models, or migrations.
- No public API contract changes.
- No frontend changes.
- No real provider keys or live network calls in tests.
- No docs/plans, harness CLI, OpenCode skill, MCP, or plugin changes.

## Required Files

Implemented source changes:

- `backend/app/runtime/service.py` (G1 cancellation handling, G3 allowlist)
- `backend/app/runtime/llm_adapter.py` (G3 fallback transparency)
- `backend/app/llm/clients/fake.py` (G2 stage-shaped fake output)

Implemented test changes:

- `backend/app/tests/test_llm_service.py` (G1 cancellation propagation)
- `backend/app/tests/test_runtime_service.py` (G1 runtime cancellation,
  G3 fallback transparency if placed here)
- `backend/app/tests/test_runtime_resume.py` (G1 resume cancellation)
- `backend/app/tests/test_llm_fake_client.py` (G2 stage-shaped fake output)
- `backend/app/tests/test_runtime_llm_integration.py` (G2 end-to-end,
  G3 fallback visibility, G4 boundary invariants)

Documentation:

- `docs/llm/PROVIDER_SETUP.md` if fallback transparency or Fake stage output
  changes operator-visible behavior
- this SPEC and `tasks.md`

## Implementation Notes

- G1: catch `asyncio.CancelledError` in the same runtime try blocks that
  currently handle `Exception`, transition to `CANCELLED` when the status map
  permits (falling back to the existing status otherwise), append a safe
  cancellation event with no raw data, then re-raise.
- G1: the `LLMErrorCategory.CANCELLATION` category is documentation-only for
  now; it is not required to be raised by any client.
- G2: Fake stage payloads must be produced deterministically and validated
  through the existing `parse_structured_output` path; they must not bypass
  schema validation.
- G3: bounded keys are `llm_fallback_used`, `llm_fallback_from_provider`, and
  `llm_fallback_error_category`; they must be included in both the persisted
  stage output and the safe event payload allowlist.
- G4: tests must use the existing scripted-service double or the G2 real fake
  path, never a live provider.

## Acceptance Criteria

```gherkin
Given LLM runtime mode is disabled
When a workflow is run through the existing run endpoint
Then the current deterministic runtime behavior remains unchanged
```

```gherkin
Given a runtime stage completes through the LLM adapter
When an asyncio cancellation interrupts the runtime loop
Then the workflow ends in a safe CANCELLED terminal state
And a bounded cancellation event is persisted
And the original CancelledError is re-raised to the caller
And no raw prompt, provider payload, or secret appears in state or events
```

```gherkin
Given LLM runtime mode is enabled with LLM_PROVIDER=fake
When a workflow is run end-to-end through the real LLM service and fake client
Then the workflow reaches WAITING_APPROVAL deterministically offline
And every LLM stage output validates against its stage schema
And the quotation stage is marked as deterministic and LLM-skipped
And the email preparation stage never calls the LLM
```

```gherkin
Given a provider failure triggers the configured fallback
When the stage output and events are persisted
Then the safe stage output and node events expose bounded fallback flags
And no fallback flags appear when fallback is disabled or unused
```

```gherkin
Given the LLM returns an approval package with requires_human_review=false
  and decision_draft="ready_for_review"
When the runtime finishes
Then the workflow still stops at WAITING_APPROVAL
And explicit human approval and explicit resume remain mandatory
```

```gherkin
Given no real provider keys are configured
When the backend test suite runs
Then all SPEC-028 tests pass offline and deterministically
```

## Test Requirements / Test Plan

All tests remain deterministic and offline. No test may require a real API
key or a live provider.

G1 tests:

- `test_llm_service.py`: cancellation during `complete()` propagates
  `CancelledError`; cancellation during the retry backoff sleep propagates.
- `test_runtime_service.py`: cancelling `run_workflow()` after a status
  transition persists a safe `CANCELLED` state and event, and re-raises
  `CancelledError`.
- `test_runtime_resume.py`: cancelling the resume continuation behaves the
  same way.

G2 tests:

- `test_llm_fake_client.py`: Fake client returns deterministic schema-valid
  JSON for each of the five runtime stage schemas when stage metadata is
  present; generic output is unchanged without stage metadata.
- `test_runtime_llm_integration.py`: real `LLMService` + `FakeLLMClient`
  through `run_workflow()` reaches `WAITING_APPROVAL`, all five stage outputs
  validate, quotation is `llm_skipped`, and email preparation does not call the
  LLM.

G3 tests:

- service-level: existing `test_enabled_fallback_handles_transient_failure`
  already asserts fallback metadata on the response.
- runtime-level: a fallback-producing service double yields
  `llm_fallback_used=true` in the stage output and in the safe
  `workflow.node.completed` payload; the default disabled path exposes no
  fallback keys.

G4 tests:

- integration: favorable `decision_draft` and `requires_human_review=false`
  still end at `WAITING_APPROVAL`;
- integration: approval plus explicit resume remain required regardless of
  `decision_draft`; resume without approval records is still rejected.

## Documentation Requirements

- Keep `docs/llm/PROVIDER_SETUP.md` consistent with any operator-visible
  change (Fake stage output, fallback transparency).
- Confirm `README.md` roadmap item 2 maps to SPEC-028.
- Confirm SPEC index references SPEC-028 without number conflict.

## User Stories

### Runtime Operator - Deterministic LLM-On Demo

As an operator, I want `LLM_RUNTIME_ENABLED=true` with `LLM_PROVIDER=fake` to
run end-to-end deterministically so that LLM-assisted stages can be demoed and
tested offline without provider keys.

### Developer - Confidence In Cancellation And Failure Semantics

As a backend developer, I want cancellation to leave a safe terminal workflow
state so that interrupted runs never dangle in an intermediate status.

### Reviewer - Transparent Fallback

As a reviewer, I want fallback usage visible in safe stage outputs and events
so that a stage that completed via fallback is distinguishable from a normal
provider call.

### Reviewer - Mandatory Approval

As a reviewer, I want tests proving favorable LLM output cannot bypass human
approval or resume so that the approval boundary remains the single authority.

## Task Sequence

1. TASK 028.1 - SPEC-028 Planning Intake And G1-G4 Audit
2. TASK 028.2 - G1 Cancellation Propagation Hardening
3. TASK 028.3 - G2 Deterministic Schema-Valid Fake LLM End-To-End
4. TASK 028.4 - G3 Fallback Transparency In Stage Outputs And Events
5. TASK 028.5 - G4 Approval And Resume Boundary Invariant Tests
6. TASK 028.6 - Final Validation And Closeout

Each implementation task must remain within the boundaries listed under
"Stable Defaults And Boundaries To Preserve".

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
docker compose config
```

Implementation tasks use the backend quality gate:

```bash
docker compose up -d postgres redis
docker compose run --rm backend-test pytest
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
git diff --check
```
