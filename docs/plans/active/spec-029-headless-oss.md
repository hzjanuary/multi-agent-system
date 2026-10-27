# SPEC-029 headless OSS implementation

Started: 2026-10-26. Updated: 2026-10-27.

## Status

Original engineering and isolated OpenRouter preparation are complete. The
two separately authorized live attempts each failed on their first request with
`provider_rate_limit`; two client generation requests consumed cumulatively.
No retry or third attempt followed. Release verification remains BLOCKED at AC-08
and the real-model portion of AC-29. Keep this
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
  provider rate limit: the authorized analyst request failed; reviewer/approval
  and final real-model journey were not reached.

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

Engineering result: headless runtime/API/CLI and self-host packaging implemented,
with the recorded non-live evidence preserved. Acceptance remains **30 PASS,
2 BLOCKED, 0 FAIL, 0 NOT_RUN**. The bounded live attempt itself **FAIL**: run
`75039b34-2bf1-4e89-a1c1-704dd2f0be28`, analyst failed with `provider_rate_limit`,
call count 1. No reviewer generation or validated model output was obtained.

The maintainer supplied a dedicated key and non-sensitive text locally and
explicitly authorized at most two generation requests. The isolated collection/
training and non-ZDR exception did not change project defaults or account policy.
The helper ran once with `--approve`; no retry, repair, probe, model/route switch
or fresh-run budget reset occurred. Provider request IDs, usage, cost and actual
upstream model/provider stay unknown after the failed response.

Do not delete the permanent attempt marker or retry this failed run. Investigate
free-route quota/availability without inference or weakening account policy; any
later generation requires a new explicit maintainer budget decision. AC-08 still
needs successful genuine chained calls. AC-29 still needs the completed real-model
image/CLI journey; original clean-clone evidence keeps its historical image
provenance. Approval/resume/pure assembly were not reached in this attempt.
Preserve those original release obligations and keep the plan active.

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
  PASS; missing-key preflight BLOCKED before generation. No live attempt was
  reserved during preparation.
  The final containing handoff commit updates evidence only; no image rebuild.
  [Scoped proof](../../release/openrouter-preparation.json) retains limits and
  separates original evidence from this preparation. AC counts unchanged.
- [ ] Genuine live model evidence and dependent first-run acceptance: BLOCKED.

## Authorized bounded live attempt (2026-10-27)

The maintainer supplied the isolated OpenRouter key and non-sensitive text locally
and explicitly authorized at most two generation HTTP requests using the existing
helper with `--approve`. No extra provider probe, warm-up, retry, repair, model
switch or fresh-run budget reset is permitted. Starting handoff HEAD is
`fad43831a92dfe9831cd77216b04ee379b2d65ba`; runtime image/source remain the pinned
preparation identities above. Private values/text are not copied into this plan.

- [x] Inspect clean branch/HEAD and existing profile before initialization:
  no profile containers, CLI auth session or attempt marker. Key/text present.
- [x] Metadata/config preflight PASS for the exact free model/route; no generation.
  Preserve a private snapshot under `.maos/openrouter-free-smoke/live-session-20261027/`.
- [x] Start only the dedicated PostgreSQL/Redis; pre-migration public tables = 0.
- [x] Migrate an empty dedicated database; maintainer explicitly bootstrapped one
  administrator and logged in locally. Doctor ready; separate CLI discovery PASS.
- [x] Invoke the helper exactly once with `--approve`. First analyst request
  failed with `provider_rate_limit`; one reservation/request attempt, no retries,
  no reviewer or later nodes. Permanent attempt and partial evidence retained.
- [x] Review durable failure via separate CLI containers after worker stop and
  a new PostgreSQL session: FAILED, call count 1, six ordered events, one node,
  zero approvals. Unknown provider response IDs/usage/cost remain unknown.
  [Safe live evidence](../../release/openrouter-live-attempt.json) records exact
  source/image, profile and IDs; raw private evidence remains under
  `.maos/openrouter-free-smoke/`. All four services stopped; volume/config/auth/
  input/evidence retained. No implementation or default privacy change.

AC-08 and AC-29 remain BLOCKED by the live rate limit and uncompleted journey.
The attempted workflow is FAILED; no claim of successful chaining, approval,
resume or final assembly is made. No push/merge/publication/remote deployment
or deletion of retained resources occurred. No new generation is authorized.

## Bounded non-inference diagnosis (2026-10-27)

Completed one authenticated key-information GET and read existing evidence/stopped
logs only. No additional generation or service startup. Cause remains unresolved:
original provider error body/headers were not retained; current monetary quota
cannot identify the earlier limit. The one-shot capture's missing free-request/
budget fields are disclosed, with no second lookup. One alternative's metadata
was prepared without applying it. See the [Vietnamese note](../../release/openrouter-429-diagnosis.md).
All 20 historical artifact hashes match; attempt/budget/pin/privacy remain intact.
AC-08/AC-29 stay BLOCKED; any future attempt needs a separate explicit decision
for up to two additional generation requests, preserving the one already consumed.

## Explicit additional two-call authorization (2026-10-27)

The maintainer authorizes one new attempt for `google/gemma-4-26b-a4b-it:free`
through `google-ai-studio`: at most two additional generation requests and at
most three cumulatively, including the original failed run's one request.
Original run `75039b34-2bf1-4e89-a1c1-704dd2f0be28` and its marker/evidence must
remain untouched. One new key-info GET corrects the earlier field omission.

- [x] One-shot corrected quota: used 0 / limit 50 / remaining 50; budgets [],
  effective_budget null. Current observation only, no inference about old 429.
- [x] Current exact endpoint metadata PASS immediately before generation;
  stop if an applicable two-call quota or route/capability/price blocker exists.
- [x] Narrow typed safe error diagnostics; 237 backend tests, 37 ops tests,
  lock/Ruff/Black/strict MyPy PASS. Error-body/message retention remains forbidden.
- [x] Source `ae11ef0c804c3a84b3d45d70e843511ede3ec135`, runtime image
  `sha256:91a258415d7f1851b4ddc1c4dde6da959efa53fc6c8e98eed0c58427e09fdb4b`;
  93 shipped hashes match. Separate linked attempt `gemma26-20261027`; old marker/
  all 20 historical artifact hashes preserved, same DB/volume/admin/CLI/input.
- [x] Existing token expired; maintainer logged in locally using the same account.
  Doctor/CLI discovery PASS. Helper ran once with `--approve`; new run
  `ea28e301-a82b-48d1-9be8-5fa34e215601` FAILED at analyst with actual HTTP 429,
  code 429 and explicit error provider Google AI Studio. New call count 1;
  cumulative historical count 2/3. No reviewer or subsequent approval/assembly.
  Unknown provider IDs, upstream code, usage and cost remain unknown.
- [x] Stop all four isolated services after separate CLI/new DB readback.
  One user, two runs, six events for each failure; old run unchanged. Both markers,
  volume/config/credentials/CLI/input/evidence retained. [Additional evidence](../../release/openrouter-additional-attempt.json).
  Acceptance 30 PASS / 2 BLOCKED unchanged; live attempt FAIL is separate.
  No implementation defect is established by the 429, no third attempt authorized.

No retry, old-run resume, warm-up, repair, third attempt, pin fallback, schema
weakening, default privacy change, push/publication/deployment or retained-data
deletion is authorized. AC-08/AC-29 remain BLOCKED pending genuine evidence.

The original 429 is not diagnosed or fixed by the new model selection. Corrected
quota is only a pre-attempt current observation, not workflow cost or a post-run
free-request count. The unused cumulative allowance does not authorize retry or
another attempt; preserve the one original plus one additional consumed request.
Final handoff edits are documentation/evidence only; no rebuild or suite rerun.

## Direct Groq → Cloudflare campaign preparation (2026-10-27)

The maintainer authorizes preparation only now. Later explicit campaign initiation
authorizes at most two Groq plus two Cloudflare calls, four new/six cumulative,
including two preserved OpenRouter requests. Fallback exists only in this opt-in
runner after eligible terminal Groq availability failure; never inside production
runtime or within a provider-pinned run. No inference during preparation.

- [x] Inspect adapters/configuration/ledgers/evidence and current official model,
  JSON, reasoning, pricing/free-plan and metadata documentation.
- [x] Narrow Groq token/reasoning mapping and shared safe diagnostics; two private
  profiles, hidden credential/plan entry, GET-only model/schema preflight and
  persistent campaign/per-provider guards implemented.
- [x] Frozen backend gate 242 PASS; lock/Ruff/Black/strict MyPy PASS. Ops 50 PASS
  (13 direct-campaign tests), plus focused provider wire/identity/CF error-shape
  tests PASS. An earlier fingerprint fixture failed while source was being
  edited; the full frozen rerun passed without weakening the fingerprint guard.
- [ ] Build/inspect affected source-labeled image; prepare blank-credential files
  against existing DB/admin/volume/CLI/input, preserving all historical evidence.
- [ ] Guide/report/provenance handoff; AC-08/AC-29 stay BLOCKED.

Groq Free organization and Cloudflare Workers Free account must be checked locally
while entering credentials. Native free-plan quota enforcement, not portable
max_price fields, protects the free-use objective. No billing, paid plan, shared
data-sharing change, remote deployment, push or retained-resource deletion.
