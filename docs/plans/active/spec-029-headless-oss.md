# SPEC-029 headless OSS implementation

Started: 2026-10-26. Updated: 2026-10-27.

## Status

Engineering complete. Release verification BLOCKED at the maintainer-selected
live-model gate (AC-08 and the dependent real-model portion of AC-29). Keep this
one plan active until that gate is resolved; do not archive as fully verified.

Branch: `feat/spec-029-headless-oss`. Historical baseline:
`92e5f1cfb2b0144bdb39a48db99371974bd372a5`. Checked implementation:
`98854a807643566b720bff8ffd7feda85fa23746`. Later evidence/prose commits do not
change the checked backend. No remote push, merge, deployment or publication.

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
  maintainer choice; no configured installed local model or remote enablement.

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
downloaded and no paid/remote call was attempted.

To resume release verification, explicitly configure an already installed local
model/reachable endpoint and authorize the documented bounded two-call smoke
with operator-supplied text. Hosted providers additionally require explicit
remote enablement. Then update AC-08/AC-29 with actual outputs/provider metadata,
verify the model-dependent README commands and only then archive this plan.
