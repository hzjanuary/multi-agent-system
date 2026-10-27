# SPEC-029 headless OSS implementation

Started: 2026-10-26. Updated: 2026-10-27.

## Status

SPEC-029 implementation and local release verification are complete: **32 PASS /
0 BLOCKED**. The separately authorized `groq-permissions-20261027` campaign
completed on Groq, run `dd922648-beb2-4afb-94e5-8bea36a2070f`, with two genuine
chained calls, explicit approval/resume and pure assembly. The same current image
passed an independent fresh clean-local-clone installation/CLI walkthrough.
Three prior failed requests remain historical; total consumed is five. No further
campaign is authorized. Plan archived only after validation; all isolated
services stopped, volumes/configuration/credentials/input/history retained.

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
- [x] M6 genuine live text_review and current-image clean-install/CLI journey:
  Groq analyst/reviewer, WAITING_APPROVAL, decision/resume/pure assembly PASS;
  [final proof](../../release/direct-campaign-completed.json), 32 PASS / 0 BLOCKED.

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
- [x] Originally BLOCKED during OpenRouter preparation; later resolved by the
  separately authorized completed Groq campaign and current-image clean install.

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
- [x] Source `44a8c42373af1320986ad78d922aa79595775dbe`, image
  `sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`;
  release-content check PASS, all 93 shipped hashes match. Both private profiles
  prepared with blank credentials/account ID, 0700/0600 permissions. All 43
  historical artifact hashes, existing DB/admin/secrets/volume/CLI/input retained.
- [x] Real resolved Compose checks for both profiles and canonical/override gate
  PASS. Four actual-image API/worker one-offs verify profile delivery and limits
  without starting dependencies or inference; missing-key preflight BLOCKED
  before HTTP. All four persistent isolated services remain stopped.
- [x] [Guide](../../direct-smoke-campaign.md), [report](../../release/verification.md)
  and [source/image/content preparation evidence](../../release/direct-smoke-preparation.json)
  updated. Zero new generation; no campaign/phase markers reserved. AC-08/AC-29
  stay BLOCKED (30 PASS / 2 BLOCKED). Final handoff is documentation/evidence only.
- [x] Maintainer entered Groq key, Cloudflare Account ID/token through hidden local
  helper and confirmed native Free plans. Initial `metadata_HTTP_403` required
  the bounded non-inference diagnosis below; authenticated preflight now PASS.
- [x] Explicitly initiated once with `run --approve`; direct Groq analyst failed
  HTTP 403 `model_permission_blocked_project`. One new call/three cumulative;
  no Cloudflare fallback for fatal permission failure. All records retained,
  isolated services stopped. Genuine success is still required for AC-08/live AC-29.

Groq Free organization and Cloudflare Workers Free account must be checked locally
while entering credentials. Native free-plan quota enforcement, not portable
max_price fields, protects the free-use objective. No billing, paid plan, shared
data-sharing change, remote deployment, push or retained-resource deletion.

## Direct metadata preflight 403 diagnosis (2026-10-27)

Authority: maintainer requested diagnosis and the smallest demonstrated fix,
metadata GETs only; no inference/campaign/service start. Preserve credential
values, plan bindings, records, profile pins, budget and default privacy.

- [x] Original helper retained only generic HTTP status, so prior request identity,
  body and headers cannot be reconstructed. Both private configurations/plan
  bindings validated without exposing values; endpoints match official Groq
  models and Cloudflare account-scoped model search/schema, not billing/admin APIs.
- [x] Add closed sanitized diagnostics and strict metadata URL allowlist before
  reproduction. Groq `GET /openai/v1/models` reproduced HTTP 403, JSON, no returned
  code/type or separate request ID; header cf-ray recorded without attributing
  the request to Cloudflare Workers AI. Bearer header present; no raw body saved.
- [x] Only request change: explicit application User-Agent instead of urllib
  default. Same key and URL then Groq 200, Cloudflare search 200, schema 200;
  full preflight PASS. Four metadata GETs total, no auto retry/redirect or
  generation. Exact server-side blocking rule remains undisclosed.
- [x] Ops 53 PASS (16 direct-campaign test methods), script Black/Ruff and
  canonical/override Compose PASS. Required backend gate 242 PASS, zero skips/
  failures; lock/Ruff/Black/strict MyPy PASS, two dependency deprecation warnings.
  Strict tracked-file secret scan (199 files) and Git diff check PASS.
  [Sanitized diagnosis](../../release/direct-preflight-diagnosis.json) retained.
  Host helper/tests/docs only, no image-input changes;
  reuse source `44a8c42` / image `sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`.

At the metadata-diagnosis closeout, the campaign remained unreserved and all
isolated operator services remained stopped. Historical requests = 2; new generation = 0; cap remains 2/provider, 4 new,
6 cumulative. AC-08 and live AC-29 stay BLOCKED, acceptance 30 PASS / 2 BLOCKED.

## Authorized direct campaign execution (2026-10-27)

The maintainer explicitly initiates the existing single Groq → Cloudflare
campaign, conditional on offline verification of the actual inference transport.
No new campaign, third provider, generation probe or retry is authorized.

- [x] Actual pinned release image, network disabled, HTTPX serialized request
  capture: explicit `User-Agent: multi-agent-os/0.2.0`, Bearer auth, request ID,
  timeout and JSON/token/reasoning parameters preserved; transport/application
  retry 0 and redirects disabled. Existing focused provider tests 8 PASS.
  Runtime already has an appropriate User-Agent, so no source/image change or
  rebuild. Source remains `44a8c42373af1320986ad78d922aa79595775dbe`, image
  `sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`.
- [x] Current GET-only preflight PASS; start only the existing isolated project
  without bootstrap/migration/secret regeneration. Original input hash matches
  and describes a fictional company requesting ten business laptops.
- [x] Doctor PASS. Existing CLI token expired; maintainer logged in locally to
  the same administrator. Separate CLI workflow discovery then PASS; both
  historical runs compare exactly before/after the new attempt.
- [x] Exactly one `run --approve` invocation. Campaign record identity (SHA256,
  not an application-assigned UUID)
  `1e51ed922000dd7fabbc421234fd02985ebd89a2c302d4dac07122e5cae06cfc`;
  Groq run `8573b056-b869-416b-87e6-e03569dbfb5f` FAILED on analyst, HTTP 403
  `model_permission_blocked_project` / `permissions_error`. One durably reserved
  generation request; 1 new/3 cumulative, no Cloudflare attempt. Request IDs and
  six contiguous events persisted; no output/reviewer/approval/resume/assembly.
  Usage/cost unknown, not zero. No new campaign/retry authorized.
- [x] AC-08 BLOCKED: no successful genuine chained calls. AC-29 independently
  BLOCKED: current image doctor/CLI works, but real-model operator journey did
  not complete; historical clean-install evidence keeps its own provenance.
  Acceptance 30 PASS / 2 BLOCKED; live campaign FAIL is a separate result.
  [Evidence](../../release/direct-campaign-attempt.json), report and guide updated;
  all four isolated services stopped, 43 historical artifact hashes intact,
  volume/configuration/credentials/input/CLI and new markers retained.

The provider's explicit error identifies a Groq project model permission, not a
confirmed transport defect or availability error. No permission, Free-plan,
shared privacy or billing policy was changed. A maintainer may review only the
intended isolated project's model restrictions; later live execution requires a
separate explicit decision. Do not reset/rerun the consumed campaign. No push,
merge, publication, remote deployment or retained-resource deletion occurred.

## One new explicit campaign authorization (2026-10-27)

Maintainer reports the intended Groq project's model permission updated and
authorizes exactly one separate Groq → Cloudflare campaign, at most 4 new calls
above 3 historically consumed, cumulative maximum 7. The previous campaigns
remain closed. No retries/probes/model switching or fatal-error fallback.

- [x] Inspect branch/HEAD, existing sealed ledger, runner and guide. Add bounded
  `new-campaign <id>` plus explicit `--campaign <id>` selection: one exclusive
  authorization slot across IDs, separate directory/markers/budget, all prior
  artifact hashes and three run records linked. Reuse credential/plan/DB/volume/
  CLI/input/image identities; no runtime/image change or rebuild.
- [x] Focused ops 58 PASS (21 direct-campaign methods), including preservation,
  unsafe-parent refusal, explicit selection, old-run verification, 4+3=7 limits
  and reinvocation guards. Script Black/Ruff PASS.
- [x] Required backend gate 242 PASS, zero skips/failures; lock/Ruff/Black/strict
  MyPy PASS, two dependency deprecation warnings. No image inputs changed.
- [x] Host source `d688138d3c270a21670d115f8b2f46524562d9d6`, single allocation
  `groq-permissions-20261027`, preflight/doctor/CLI PASS; retained login reused,
  no campaign bootstrap. Image source `44a8c42` / digest `sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959` unchanged.
- [x] Exactly one selected `run --approve` PASS: run
  `dd922648-beb2-4afb-94e5-8bea36a2070f`, Groq `openai/gpt-oss-20b`, both agents
  attempt 1, two durable reservations, 16 events, approval/resume/pure assembly
  and COMPLETED. Independent READ ONLY DB proof validates actual analyst output
  mapping, immutable definition, approval and final assembly. Usage 1638 prompt /
  635 completion / 2273 total; cost/currency unknown. Cloudflare unused. Two new /
  five cumulative requests; no additional campaign authorized.
- [x] AC-08 PASS from genuine chaining; AC-29 PASS from independent fresh
  clean-local-clone actual-image install/CLI plus same-image live journey.
  Zero records before explicit isolated verification bootstrap, no campaign
  administrator replaced. Initial wrong-tag verification assertion retained as
  FAIL; corrected fresh namespace pins exact digest and passes. Both walkthroughs
  make zero generation calls and retain their data. All campaign/verification
  services stopped; 83 linked historical artifact hashes intact. All 32 acceptance
  items PASS, no BLOCKED. Archive this plan and close original release-verification
  goal after final docs/evidence/secret checks. No push/publication/deletion.

## Final closeout

[Completed campaign and current-image proof](../../release/direct-campaign-completed.json)
records separate host/runtime/image identities, full private output/evidence paths
and safe public metadata. Prior failed run/campaign artifacts are unmodified.
Final handoff changes are docs/evidence and validated plan archival only. No
runtime/image rebuild or generation followed successful completion. The old
OpenRouter 429s remain undiagnosed; Cloudflare is not live-verified. Local SPEC-029
acceptance is complete without a remote CI, publication or enterprise-readiness claim.
