# SPEC-029 headless OSS implementation

Started: 2026-10-26. Updated: 2026-10-27.

## Status

Original engineering complete. Isolated OpenRouter preparation is authorized;
live execution is deferred until local key entry. Release verification BLOCKED at the
live-model gate (AC-08 and the dependent real-model portion of AC-29). Keep this
one plan active until that gate is resolved; do not archive as fully verified.

Branch: `feat/spec-029-headless-oss`. Historical baseline:
`92e5f1cfb2b0144bdb39a48db99371974bd372a5`. Checked implementation:
`98854a807643566b720bff8ffd7feda85fa23746`. The previous evidence/prose closeout did not
change that checked backend; the new preparation changes require separate proof. No remote push, merge, deployment or publication.

Provenance closeout inspected pre-closeout handoff HEAD
`f05bf56dfbe4a29394443e9711e75a708fd8a905`. The diff from the tested source
contains documentation/evidence only: application/tests, examples, migrations,
dependencies, Docker inputs, Compose, configuration templates, verification
scripts and CI workflows have identical Git object identities. The 91 shipped
file hashes and retained image ID/revision label still match. The changed README
build flag `--network=host` matches the recorded clean-local-clone build; public
cloning remains explicitly manual until publication. This closeout edits only
the report and this plan, so its documentation commit is a handoff identity,
not a replacement tested source SHA. No suite rerun or image rebuild is needed.

## Outcome and authority

The supplied attachment activates SPEC-029 and selects MIT for appropriately
owned project material. It supersedes the old graduation frontend/procurement/
RAG contract while preserving security, data protection, authorization and
validation obligations. No mandatory historical Harness control-plane writes
were used. Parallel agents used the selected inherited model/effort for
independent definitions/providers, runtime/persistence and packaging work.

## Inventory and extraction

- Retained/generalized Python/FastAPI/LangGraph, real Ollama/OpenAI-compatible/
  Groq/OpenRouter/Gemini transports, PostgreSQL, Redis notifications,
  Argon2/JWT, generic roles, human approvals, events and audit boundaries.
- Replaced fixed procurement stages/state with registered typed agents/tools/
  workflows and immutable definition/artifact/provider identities.
- Added durable jobs, DB-time claims/leases/fencing, call reservations, per-node
  commits, explicit recovery/cancellation, approval content identities and
  committed cursor replay. One LangGraph path executes agent/tool steps.
- Removed frontend/datasets/demo/knowledge/vectorstore/object storage/pricing/
  outbound/Telegram modules, services, prompts, configuration, dependencies and
  exclusive tests. Removed placeholder/fake/fallback production paths.
- Inventory found no retained runtime/CI dependency on `.harness-*`, obsolete
  `.ai`/`.agents`/`.codex` handoffs/intake/template/semantic-changeset tooling,
  old governance, defense or frontend security reports; removed them from the
  active distribution. Git baseline remains the archive.
- Rewrote retained auth, provider, state/approval/event/recovery tests for the
  generic product; no global test exclusions or weakened runtime limits.
- MIT/NOTICE review found no concrete conflicting retained-source ownership
  notice. Dependency/base-image/model notices and terms remain separate.

## Progress

- [x] M0 baseline/instructions/import/scaffold/license inventory; feature branch.
- [x] M1 typed registry, source fingerprints, opt-in packaged text_review and
  unrelated workflow extension proof.
- [x] M2 durable PostgreSQL runtime, recovery/concurrency/fencing/approval/event
  and separate-database restore proof.
- [x] M3 retired product/services/fakes/scaffolding extracted; imports/image clean.
- [x] M4 API/CLI/admin/config/migration/Compose/image/bootstrap/private session
  and worker availability validated in an isolated installation.
- [x] M5 English README/operator/developer docs, MIT/NOTICE/security/contribution
  files and backend-only CI updated; links and secret/dependency checks passed.
- [x] M6 all non-live checks and acceptance evidence matrix completed.
- [ ] M6 live text_review and full README model journey: BLOCKED by explicit
  maintainer boundary: OpenRouter preparation is complete, key/live execution pending.

## Verification and decisions

Authoritative matrix and artifacts: [release verification](../../release/verification.md).
The checked actual image is
`sha256:fa2e6d17b8a3a99c0abf4289cbcbe42f0740173d13d700c2a10de6c15153fb69`.
Its revision label matches the checked source, and all 91 shipped code/example/
migration file hashes match. The runtime excludes tests, fake providers and
retired application/infrastructure packages.

- Final backend gate: 218 passed, zero skipped/failed; Ruff/Black/strict MyPy/
  lockfile passed. Black checked 119 files, MyPy 117. Test-client dependencies
  emit two deprecation warnings. Ops unittest 12 passed.
- Actual clean local clone/image: generated private config, fresh zero records,
  one explicit administrator, repeat bootstrap refusal and original-password
  login; separate CLI containers share a 0600 session file in a 0700 directory.
- Actual independent API restart/client disconnect preserves one accepted job;
  worker executes deterministic tool result 42. A premature disconnect rejected
  with 400 is not treated as accepted. Real Redis stop preserves result 14 and
  all six events/five events after cursor1; doctor reports degradation and
  aggregate health is degraded, then recovers after Redis restart.
- Actual image CLI: create/start/show/list/nodes/events/follow, idempotency,
  content-bound approve/reject, explicit resume, cancel, logout/denial/relogin.
  Follow was deliberately stopped after observing an event (exit 137 recorded).
- Real pg_dump/pg_restore into a separate disposable database preserves completed
  results, pending approvals, ordered event identities, users/roles and refresh
  state; restored resume does not mutate the paused source database.
- Current 58-package locked main audit: zero known vulnerabilities. No OS/host/
  model audit or live inference is claimed. Strict source secret scan passed.
- Docker bridge DNS blocked package downloads on this host; verified Linux build
  uses --network=host. Runtime Compose networking/loopback port policy remains.
- Exact-image checks found and fixed empty Bearer header before CLI login and
  the mounted verifier's Python import path. Aggregate /health was reconciled
  with SPEC-029; /live remains process-only. No assertions were skipped to pass.
- Cold package fingerprint validation takes about 4 seconds on this host.
  Subprocess observation checks the real handle for up to 20 seconds; runtime
  lease/call/token/output limits were not changed for tests.

## Risks and recovery

Only uniquely named task-owned databases/schemas/Compose projects were used.
Operator databases, volumes, secrets, Git history and unrelated services were
not reset or deleted. All task-created maos-spec029 verification containers were
stopped after proof; their volumes and private configs were retained. Verification configs/sessions remain private under ignored
.maos directories in /tmp checkouts; no backup/credential is committed. Preserve
these files if inspecting the test installation; do not use its records as a
production seed. Normal installation uses a new project/database and explicitly
provisions its own administrator.

The initial unrelated untracked GOAL-029.txt was later observed absent. No root
or subagent deletion targeted it; no substitute content was guessed. The original
attachment remains available as the task authority. This observation does not
authorize changing unrelated files.

Recovery is explicit: restore matching definitions/provider profile for paused
or interrupted runs; resume only permitted work. Uncertain non-idempotent work
requires independent reconciliation and cannot be publicly marked completed.
Back up before upgrades; restore into a separate compatible database. Never
run down -v against an operator project or attach a legacy procurement DB.

## Remaining action and result

Engineering result: headless generic runtime/API/CLI and self-host packaging
implemented and verified within the recorded non-live scope. Acceptance:
30 PASS, 2 BLOCKED, 0 FAIL, 0 NOT_RUN. Fully verified release readiness remains
unproven. The maintainer explicitly chose to keep AC-08 blocked; no model was
downloaded and no model-generation request was attempted.

AC-08 and the model-dependent portion of AC-29 remain BLOCKED. The maintainer
selected OpenRouter free inference rather than installing a local model, and
explicitly permits collection/training and non-ZDR routing only for the isolated
`openrouter-free-smoke` configuration. This turn prepares only; the dedicated key
will be entered locally later. No inference is authorized during preparation.

Follow [the optional guide](../../openrouter-free-smoke.md) for the remaining
bounded live attempt through the release image, API/worker and fresh CLI session:
real analyst then reviewer, persisted outputs/events, WAITING_APPROVAL, normal
explicit approval and resume, pure assembly, at most two generation HTTP attempts,
no retries. Preserve partial evidence and never reset the budget automatically.
Metadata and fixture tests cannot convert AC-08/AC-29 to PASS. The original
release-verification requirements remain unresolved; archive only after genuine
validation. No push, publication, merge, deployment or retained-resource deletion.

## OpenRouter preparation closeout (2026-10-27)

- [x] Inspect current clean handoff `4e4242ffd318da198ef7c9438401147946450dca`,
  actual provider/runtime/workflow, secret/configuration and release evidence.
- [x] Verify exact public free model and eligible endpoint; pin
  `google/gemma-4-31b-it:free` / `google-ai-studio` and fail-closed GET-only preflight.
- [x] Add typed host-controlled request routing, strict unset privacy defaults,
  routing identity, explicit no transport retry, safe request/provider/cost evidence.
- [x] Prepare helper/guide with private key slot, separate CLI/DB/Compose identities,
  immutable image pin, normal approval/resume and permanent once-only attempt lock.
- [x] Run required backend/Compose and focused offline checks; build/inspect new
  source-labeled release image and prepare the blank-key private configuration.
- [x] Record source/image identities and exact results in the release report.
  Runtime source `f6317e25317c13c2da83c3e784b4d660f48fea45`; image
  `sha256:99078eeb57903c074973fdcbdb10d68e0b488e1e634f6e5999bc7c4401ad6527`.
  Final host helper/test source `6287f1a2f7d9ecaad12cd4a02e4873fb4a880ac2`;
  92 shipped file hashes still match. Backend 228 PASS, ops 29 PASS,
  lock/lint/format/strict types/Compose/image checks PASS. Metadata-only preflight
  PASS; missing-key preflight BLOCKED before generation. No live attempt reserved.
  The final containing handoff commit updates evidence only; no image rebuild.
  [Scoped proof](../../release/openrouter-preparation.json) retains limits and
  separates original evidence from this preparation. AC counts unchanged.
- [ ] Genuine live model evidence and dependent first-run acceptance: BLOCKED.
