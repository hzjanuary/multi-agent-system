# SPEC-029 acceptance evidence

The original implementation and recorded non-live checks remain preserved.
Release readiness is **BLOCKED** by AC-08 and the real-model portion of AC-29.
Two separately authorized OpenRouter attempts failed on their first analyst
request with `provider_rate_limit`. The later explicitly initiated direct
Groq → Cloudflare campaign also failed on its first analyst request: HTTP 403,
`model_permission_blocked_project` / `permissions_error`. Cloudflare was correctly
not invoked for this fatal permission failure. **Three generation HTTP requests
consumed cumulatively: two OpenRouter + one Groq; Cloudflare zero.** No reviewer,
approval/resume or assembly was reached. The consumed campaign/attempt markers
must not be reset; unused allowance does not authorize another campaign. See
[direct campaign evidence](direct-campaign-attempt.json),
[original evidence](openrouter-live-attempt.json) and
[additional-attempt evidence](openrouter-additional-attempt.json). Fixture success
is never counted as genuine chained execution.

## Checked source and artifacts

- Local branch: `feat/spec-029-headless-oss`; no push, merge or publication.
- Reviewed historical baseline: `92e5f1cfb2b0144bdb39a48db99371974bd372a5`.
- Checked implementation: `98854a807643566b720bff8ffd7feda85fa23746`.
- Actual runtime image: `sha256:fa2e6d17b8a3a99c0abf4289cbcbe42f0740173d13d700c2a10de6c15153fb69`.
  Its OCI revision label names that implementation commit. All **91** shipped
  application/example/migration files match source hashes, excluding test code.
- [Image/content evidence](image-evidence.json),
  [actual-image installation/restart/Redis evidence](walkthrough-evidence.json),
  [actual-image CLI evidence](cli-evidence.json),
  [full backend gate log](backend-gate.log), and
  [locked dependency audit](dependency-audit.json).

The earlier documentation closeout did not change this checked
application image. The later OpenRouter preparation below has separate provenance. The implementation commit remains the reproducible source
identity. Artifact JSON contains commands, safe status metadata and hashes; no
operator password, bearer token, provider key or database backup is committed.

### Bounded provenance closeout

The pre-closeout handoff HEAD inspected was
`f05bf56dfbe4a29394443e9711e75a708fd8a905`. Its only commit after the tested
implementation is documentation/evidence-only. Git object identities are
unchanged for application code/tests, packaged examples, migrations, dependency
manifest/lock, Dockerfile/build exclusion rules, Compose files, configuration
templates, verification/operator scripts and CI workflows. All 91 recorded
shipped-file hashes still match; the retained image ID and OCI revision label
also match the tested identities above.

The README build command's added `--network=host` matches the recorded image
build, with the same target, tag and backend context; the evidence command also
sets a provenance label. The public clone command is explicitly a manual
distribution example, not a claim that the unpublished commits exist on GitHub.
Other runnable README commands did not change in the handoff commit.

This closeout changes only this report and the active execution plan. Its
containing documentation commit is a final handoff HEAD, not a new tested
implementation or image identity. Existing acceptance evidence and counts are
unchanged; no suite rerun, image rebuild, inference or retained-resource change
was needed for this provenance check.

### Isolated OpenRouter preparation (2026-10-27)

This is additional non-live preparation, authorized after the earlier closeout.
The prior source/image and their acceptance artifacts above remain historical.
The new runtime image was built from clean source
`f6317e25317c13c2da83c3e784b4d660f48fea45`, tag
`multi-agent-os:openrouter-free-smoke`, digest
`sha256:99078eeb57903c074973fdcbdb10d68e0b488e1e634f6e5999bc7c4401ad6527`.
Its OCI revision label matches that source; all **92** shipped application,
example, migration/configuration files match source hashes and the current tree.
The previous `multi-agent-os:local` image was not replaced.

Final helper/verification source is
`6287f1a2f7d9ecaad12cd4a02e4873fb4a880ac2`. Its changes after the image source
fix a test-only MyPy reference, host-side Compose `run` flag compatibility and
input-length prevalidation, plus optional guide commands. No shipped runtime,
example, migration, dependency, Docker, Compose or default configuration input
changed after the image build. Tests are removed from the runtime stage; no
image rebuild is needed for these host verifier/test/documentation fixes. The
containing final handoff commit records evidence and is a separate identity.

[Preparation evidence](openrouter-preparation.json) records **228 backend tests
passed**, no failures/skips, lock/Ruff/Black/strict MyPy passed (121 Black files,
119 MyPy files), **29 ops unit tests** (17 new helper tests), scripts lint/format,
base/optional Compose gates and strict source secret scan. The initial gate's
MyPy errors were solely in the new test; its references were corrected and all
10 OpenRouter tests plus the affected static checks rerun successfully. Two
existing dependency deprecation warnings remain. Actual image checks prove
private/test/fake exclusion; actual Compose API and worker oneoffs prove the
same model/routing/limits, with a blank key refusing generation. An unauthenticated
public-metadata GET also succeeds from that image on the isolated network.

The exact free model and provider are `google/gemma-4-31b-it:free` /
`google-ai-studio`, canonical `google/gemma-4-31b-it-20260402`. Public metadata
was retrieved at **2026-10-27T05:25:18.852007+00:00**. Prompt/completion are
explicitly zero; request fee is omitted, not fabricated as a metadata zero.
Official free-variant documentation and the enforced zero request-price cap
bound the request. The exact endpoint advertises JSON-object mode, max_tokens
and temperature; reasoning is optional and disabled by default. No search,
media, paid plugin, server tool or cache operation is requested. Metadata is
rechecked immediately before the single later attempt; route drift fails closed.

The private profile is prepared under `.maos/openrouter-free-smoke/` with a new
Compose/database/volume identity and separate CLI session, 0700 directory and
0600 files. At preparation closeout the key and operator text were empty, no attempt was
reserved, and a credential-requiring preflight stopped before any inference. The permissive
collection/training policy exists only in this operator-selected profile; unset
OpenRouter preferences explicitly deny collection and require ZDR. Profile
identity now includes routing policy, so existing runs cannot be silently
rerouted. Account/organization ZDR restrictions remain authoritative.

**No inference was executed during preparation. Its acceptance result was
30 PASS / 2 BLOCKED:** AC-08
and the real-model part of AC-29 still require the genuine journey below. No
prior clean-clone/live-release claim is expanded by these offline checks. Only
the fresh gate containers were stopped, retaining their data; profile services
await the operator procedure and no old volumes/configuration were deleted.

### Authorized bounded live attempt (2026-10-27)

Starting clean handoff: `feat/spec-029-headless-oss` at
`fad43831a92dfe9831cd77216b04ee379b2d65ba`. The actual API/worker used the existing
image digest `sha256:99078eeb57903c074973fdcbdb10d68e0b488e1e634f6e5999bc7c4401ad6527`,
source label `f6317e25317c13c2da83c3e784b4d660f48fea45`. No image was rebuilt;
prior implementation/image evidence and preparation artifacts remain unchanged.

The maintainer entered the key/text locally. Configuration and fresh metadata
preflight passed for the exact free model/route. Both running services had the
same pinned image/profile, `MAX_PROVIDER_CALLS=2`, retries 0, output cap 1024,
60-second timeout, zero price ceilings and the isolated allow/non-ZDR policy.
No default privacy/account setting was changed. The dedicated database had zero
public tables before migration and zero users/runs after migration. The operator
explicitly bootstrapped one administrator and logged in locally. Doctor reported
ready with an available worker; a separate CLI container reused the private 0600
session and discovered `text_review`.

Executed exactly once:
`python3 scripts/ops/openrouter_free_smoke.py run --approve`.
The helper's final preflight passed, reserved its permanent attempt marker and
created workflow `text_review@1.0.0`, run
`75039b34-2bf1-4e89-a1c1-704dd2f0be28`. The run finished **FAILED**, error
`provider_rate_limit`, durable call count **1**. Its only node was `analyze`,
execution `592a0849-2b61-44bf-87b2-6d2e31d0d485`, attempt 1, FAILED with one
pre-dispatch reservation and no output. The production OpenRouter adapter maps
only HTTP 429 to this error category; the durable record retains the category,
not the raw HTTP response/status/body.

The request was configured for OpenRouter, `google/gemma-4-31b-it:free`, pinned
`google-ai-studio`. There was no successful generation response confirming an
actual upstream model/provider. Provider request IDs, usage and reported cost
are **unknown**, not zero. Client evidence supports one attempted generation
request, zero successful generations, zero reviewer requests and no retries.
Upstream internal work is not observable. Reviewer chaining, validated outputs,
WAITING_APPROVAL, approval, explicit resume and final assembly were **not reached**;
none are claimed verified by this attempt.

All six ordered events (created, queued, started, node started, node failed, run
failed) and the failure persist. After stopping the worker, independent CLI
containers read show/nodes/events/approvals, and a new PostgreSQL session confirmed
FAILED / call count 1 / six events / one node / zero approvals. Raw evidence stays
private under `.maos/openrouter-free-smoke/`: `attempt.json`, `outcome.json`,
`live.stdout.json`, `live.stderr.json`, `api-evidence.json` and
`live-session-20261027/`. The linked public JSON contains only safe identifiers,
settings, status and integrity hashes, without the key, session tokens, account
credentials, test text, prompts or raw provider body.

The **live attempt FAIL** is distinct from acceptance status: **30 PASS,
2 BLOCKED, 0 FAIL, 0 NOT_RUN** at the acceptance-item level. AC-08 and AC-29
remain blocked by the provider rate limit and the uncompleted genuine journey.
All four isolated services were stopped; database volume, configuration, CLI
session, input and evidence remain retained. No retry, warm-up, repair, provider
probe, model/route switch, budget reset, publication, push, merge, remote deployment
or deletion of retained resources occurred. This closeout changes documentation
and evidence only; existing backend gates are not rerun and the image is not rebuilt.

### Non-inference 429 diagnosis (2026-10-27)

[Sanitized Vietnamese diagnostic note](openrouter-429-diagnosis.md): exactly one
GET `/api/v1/key` returned HTTP 200, with no additional generation. Current credit/
usage fields do not identify the earlier limit; the original error body/headers
are unavailable. Classification remains **unresolved HTTP 429**, not confirmed
platform/account or upstream capacity. The note discloses fields not collected
by the one-shot lookup and one metadata-only alternative; no pin was changed.
Original attempt/evidence, stopped services and 30 PASS / 2 BLOCKED remain intact.

### Separately authorized additional attempt (2026-10-27)

The maintainer explicitly authorized one new attempt with up to two additional
generation requests, model `google/gemma-4-26b-a4b-it:free` / `google-ai-studio`,
and a cumulative ceiling of three including the old run's one request. Original
run `75039b34-2bf1-4e89-a1c1-704dd2f0be28`, root marker and all 20 historical
artifact hashes are unchanged; the exact old API record matches before/after.

**Corrected quota:** exactly one additional authenticated GET `/api/v1/key`, at
`2026-10-27T06:39:40.127326+00:00`, returned HTTP 200 and
`free_model_daily_requests={used:0, limit:50, remaining:50}`, `budgets=[]`,
`effective_budget=null`. Key credit limits/reset are null; aggregate monetary
usage fields are zero. All relevant fields were present, and missing/null/zero
were preserved distinctly. This observation was sufficient for two calls then;
it is not this run's usage/cost, a post-run quota observation or an explanation
of the original 429. No second quota poll was made in this authorization.

**Narrow implementation change:** a typed, bounded OpenRouter error hook retains
actual HTTP status, selected error code/type, explicit provider/upstream codes,
source-labeled response IDs versus application IDs, and received whitelisted
Retry-After/rate/reset headers. Provider messages and arbitrary headers are
omitted. Raw upstream JSON is parsed transiently only for code/status; raw
body/metadata, prompts and completions are never stored in diagnostics. Invalid,
overlong, credential-bearing or request-content strings are dropped. Diagnostics
persist in the failed node's execution metadata through the existing worker's
fresh failure transaction; failure semantics and output schemas are unchanged.

The helper adds one fixed, explicitly authorized continuation slot
`gemma26-20261027`, preserving the original permanent marker instead of resetting
it. Separate manifests/overlay/authorization/attempt/evidence live under
`.maos/openrouter-free-smoke/attempts/gemma26-20261027/`. A private active pointer
selects them. Only the isolated env's model changes; project, database volume,
auth secrets, administrator and input are reused. Duplicate preparation/run and
unknown third identities are rejected. No generic retry loop or fallback was added.

**Source/image:** implementation `ae11ef0c804c3a84b3d45d70e843511ede3ec135`,
image `sha256:91a258415d7f1851b4ddc1c4dde6da959efa53fc6c8e98eed0c58427e09fdb4b`,
tag `multi-agent-os:openrouter-free-smoke-v2`. OCI source label and all **93**
shipped file hashes match; runtime excludes tests/fakes/private config. Backend
**237 PASS**, zero failures/skips, two existing dependency deprecation warnings;
lock/Ruff/Black (123 files)/strict MyPy (121 files) PASS. Ops **37 PASS**, including
quota missing/null/zero, secret exclusion, one-shot lookup, continuation history/
budget/guard checks; scripts lint/format, Compose base/optional gates and secret
scan PASS. PostgreSQL integration confirms safe diagnostic persistence. Prior
image/source artifacts are retained, not relabeled as verifying this new behavior.

The retained CLI access token had expired; the maintainer logged in locally with
the existing account. Doctor and independent CLI discovery passed. No migration,
bootstrap, account replacement or data reset occurred: one administrator and one
historical FAILED run were present before the new attempt. API and worker agreed
on the new image/profile with MAX_PROVIDER_CALLS=2, retries 0, output cap 1024,
zero prompt/completion/request price ceilings, no fallback, no paid add-ons and
only the explicit test allow/non-ZDR policy. Default privacy remains restrictive.

The final exact-variant/endpoint metadata preflight passed before reservation;
request price is **unknown/omitted**, not fabricated as a metadata zero, while
the outbound cap remains zero. Executed the helper once with `--approve`.
New `text_review@1.0.0` run **`ea28e301-a82b-48d1-9be8-5fa34e215601` FAILED**;
only analyst `analyze`, execution **`4bc8a039-efad-4027-b26e-5c1716f5871d`**, attempt 1,
one reservation/client generation request. Sanitized response: **HTTP 429**,
`error_code=429`, explicit `provider_name="Google AI Studio"`; local application
request ID `4461573d-a8ba-4621-9fda-29882b27c20a`. No provider response ID, upstream
error code or retry/reset header is available in the saved diagnostic fields.
Actual model execution, usage and provider-reported cost remain **unknown**.
The requested model/profile is known; an error provider name is not proof of
successful upstream generation or a diagnosis/fix of the original failed request.

After the first failure the worker was stopped. Separate CLI show/nodes/events/
approvals and a new PostgreSQL session confirmed FAILED, one failed node, six
ordered events and zero approvals. The database contains the same one user and
two runs with call counts 1+1=2. No reviewer, WAITING_APPROVAL, decision, resume or
assembly occurred; no retry, repair or replacement run was attempted.

The **additional live attempt FAIL**, while acceptance remains **30 PASS,
2 BLOCKED, 0 FAIL, 0 NOT_RUN** at the item level. No successful real-model journey
or implementation defect causing the provider 429 is demonstrated. All four
isolated services are stopped; volume, credential/CLI/input state and both attempt
records/evidence are retained. No third attempt, publication/push/merge/remote
deployment or retained-volume/configuration deletion occurred. Final handoff
changes after the tested source are documentation/evidence only, so no rebuild
or suite rerun is needed for that SHA difference.

Environment: Linux `7.0.0-38-generic` x86_64, Docker Engine `29.9.2`, Compose
`5.6.1`, local test Python `3.12.9`. The clean-image build used:

```bash
docker build --network=host --target runtime \
  --label org.opencontainers.image.revision=98854a807643566b720bff8ffd7feda85fa23746 \
  -t multi-agent-os:local ./backend
```

The default Docker bridge failed to resolve the package index on this host.
Host-network build succeeded; runtime services use their private Compose network.
No Docker Desktop or other operating-system verification is claimed.

## Observed proof

**B — Complete backend gate.** On the checked implementation commit:

```bash
PATH="$PWD/backend/.venv/bin:$PATH" \
MAOS_TEST_DATABASE_URL=postgresql+asyncpg://maos_test:maos-isolated-test-only@127.0.0.1:55429/maos_test \
MAOS_TEST_POSTGRES_CONTAINER=maos-spec029-postgres-20261026 \
REDIS_URL=redis://127.0.0.1:56329/0 \
bash scripts/ci/backend-gate.sh
```

Result: **218 passed**, zero skipped/failed; Ruff passed; Black checked **119**
files; strict MyPy checked **117** source files; `poetry check --lock` passed.
Two dependency deprecation warnings remain in the test-client stack. The DSN
above is an explicitly disposable test fixture, never an installation default.
`python -m unittest scripts.ops.test_scan_secrets
scripts.ops.test_validate_environment -q` also passed **12** tests.

The suite uses actual isolated PostgreSQL schemas/databases for persistence,
locking, restart, transaction and restore claims. LLM transport responses are
injected test fixtures. `test_composition_integration.py` runs those responses
through the production provider parser, LangGraph and PostgreSQL, including
chained analyst/reviewer outputs, persisted malformed-output failure and paused
human approval. It is not live inference.

**I — Actual image and clean local clone.** The checked commit was cloned locally
into `/tmp/maos-spec029-clean-clone-final`, independently of the implementation
worktree. The image was built from that clone. The README config-init, migration,
bootstrap, API/worker, doctor and separate-container CLI login/discovery procedure
ran under uniquely named project `maos-spec029-release-final-20261027-v2`.
`.env` and auth file modes were 0600; CLI directory mode was 0700. Migration
created zero users/runs/events/node records/approvals/jobs; explicit bootstrap
created exactly one requested account and zero business activity. Repetition
failed and the original password still authenticated. Example discovery used
exact packaged path `maos_examples.text_review`; it created no run records.

`docker run --rm ... multi-agent-os:local python /verify.py`, using
`scripts/ci/check-release-image.py`, passed content/import checks: unprivileged
user, migrations/CLI/template/example present, default registry empty, and
removed modules, tests, fake client, Qdrant/MinIO, pytest and Poetry absent.
An actual-image negative Settings check rejected `llm_provider="fake"`.

The image walkthrough explicitly mounted a **test-only deterministic extension**
outside the image for arithmetic/approval execution. It did not add fake
providers to the release. The model name used for configuration checks was a
verification-only string; readiness validated configuration without claiming
that model exists or performing inference.

**N — Accepted submission and real Redis outage.** A submitting HTTP client sent
start but never read an acceptance response. An independent connection observed
the durable QUEUED state, then the submitting socket closed. With the worker
stopped, API restart preserved exactly one queued job; starting the independent
worker produced the real deterministic result **42** and six ordered events.
A separate early-close attempt was rejected with HTTP 400 before request-body
acceptance and created no job; acceptance is not promised for undelivered or
rejected requests. That negative observation is preserved in the artifact.

With the unique project's Redis service actually stopped, a second real tool
run completed with result **14**, six contiguous events, and all five later
events replayed after cursor 1. Doctor reported optional notification degradation
while the database/worker remained available. `/health` returned `degraded`.
Redis was restarted and doctor recovered. No model calls were made.

**C — Actual CLI operation.** Separate containers exercised workflow validation
and discovery; idempotent run creation; start/show/list/nodes/events; approval
history; approve; explicit resume; rejection; forbidden resume after rejection;
cancellation; logout; unauthenticated denial; and fresh login. Approval left the
run APPROVED with no downstream node until explicit resume. The pure tool then
produced `VERIFICATION INPUT!` from supplied test text. `events --follow` emitted
sequence 1 and was deliberately stopped (container exit 137); this is a verified
stream observation, not a claim that a deliberately terminated command exited
successfully.

**R — Recovery and restore.** B includes independent worker subprocess
termination/restart, fenced stale-result refusal, preserved committed checkpoints,
explicit recovery and unsafe-resume refusal. Cold package fingerprint validation
took about four seconds on the host; the subprocess observation waits up to 20
seconds while checking the actual process. Runtime lease/call/token limits were
not relaxed. `test_backup_restore.py` used real `pg_dump`/`pg_restore` from the
explicit PostgreSQL test container into a different disposable database. It
verified completed outputs, pending approval content, event IDs/order, users/roles
and refresh rotation, then resumed the restored run while the source stayed
paused. Existing operator databases/volumes were not used or deleted.

**S — Security, removal and documentation.** The current exported main dependency
graph contains **58** pinned packages and **zero known vulnerabilities** in the
recorded pip-audit run. Scope excludes OS/host/model audits. Strict committed
source scanning with `--allow-test-placeholders` passed without findings; that
mode excludes test-fixture files under the scanner policy. Reviewed fixture
credentials are test-only, not operator credentials.
Bounded removed-import/config/dependency inspection passed. Local Markdown links
were checked. The existing repository issue channel was verified read-only with
`gh api repos/hzjanuary/multi-agent-system` (`has_issues=true`); no messages or
settings changes were made. MIT was selected by the maintainer; retained source
headers and Git authorship were reviewed with no concrete conflicting ownership
notice identified. [NOTICE](../../NOTICE) records the review's scope and preserves
dependency/base-image/model licensing boundaries.

## Acceptance matrix

PASS names observed evidence at the checked source/image. BLOCKED identifies
remaining model capability/operator authorization; it is not fixture success.

| ID | State | Authoritative evidence / remaining scope |
| --- | --- | --- |
| AC-01 | PASS | I: clean release image built, migrated and started with API/worker/PostgreSQL/Redis; no frontend, Node, Qdrant or MinIO. |
| AC-02 | PASS | I: real fresh counts all zero; explicit administrator gives one user and zero runs/events/nodes/approvals/jobs. B also asserts every non-metadata migration table empty. |
| AC-03 | PASS | I/C: image bootstrap and repeat refusal, original-password login; B explicit user creation/role and last-admin protection. |
| AC-04 | PASS | B negative provider/bypass/fallback contracts; I actual-image fake-provider rejection and missing fake module/content. |
| AC-05 | PASS | S bounded retained-import/dependency inventory; B import tests; I release package inspection. |
| AC-06 | PASS | B `test_two_unrelated_workflows_one_graph`: distinct typed text/arithmetic definitions without core modifications; I external test extension uses the same image. |
| AC-07 | PASS | B production parser→LangGraph→PostgreSQL composition covers agent/tool steps through one orchestration path; I/C exercise actual deterministic tools. Live inference is AC-08. |
| AC-08 | BLOCKED | Two historical OpenRouter analyst requests failed with `provider_rate_limit`; the direct Groq analyst request failed HTTP 403 `model_permission_blocked_project`. Counts 1+1+1=3, no successful output/reviewer/chaining. Each attempt retains separate provenance; Cloudflare was not invoked. |
| AC-09 | PASS | B missing model/key/endpoint, auth rejection, timeout, exhausted transient retries, invalid output and budget refusal fail without fake success. Provider-specific tests use fixtures. |
| AC-10 | PASS | B `test_parser_failure_is_durable_and_stops_downstream`: production parser failure persists through worker transaction end, read from a new DB session; later nodes absent. |
| AC-11 | PASS | N accepted client disconnect without consuming response, API restart, one durable job and independent worker completion; B independent process/recovery tests. Rejected/unreceived requests are not accepted submissions. |
| AC-12 | PASS | R subprocess loss/restart preserves committed node output and one completed attempt; no recomputation, stale generation refused. |
| AC-13 | PASS | R interrupted declared non-idempotent handler at an observable executing boundary refuses explicit resume with `unsafe_resume_requires_reconciliation`; no automatic retry. No exactly-once external-effect claim. |
| AC-14 | PASS | B concurrent keyed/unkeyed starts, concurrent resumes and competing real DB claims yield one active owner. |
| AC-15 | PASS | B/C concurrent creation/replay, changed input/target conflicts for operation families, body extras rejected, atomic idempotency/job persistence. Configuration loss does not break saved replay. |
| AC-16 | PASS | B restart/new-session, role and stale content/state checks; C content-bound CLI decision and explicit resume. |
| AC-17 | PASS | B conflicting concurrent decisions leave one committed approval outcome. |
| AC-18 | PASS | B sequential distinct approvals and C image-level APPROVED pause without downstream execution until explicit resume. |
| AC-19 | PASS | B in-flight cancellation rejects late output/current-claim writes; node attempt closes CANCELLED. C immediate created-run cancellation. |
| AC-20 | PASS | B failure state/error/events remain visible in an independent DB session after the failing transaction/session. |
| AC-21 | PASS | B rollback emits no notification; committed identity publication, authenticated WS reconnect/catch-up and DB polling preserve ordered history. N actual replay preserves all committed sequences. |
| AC-22 | PASS | N actual stopped Redis, independent worker completion, contiguous replay and explicit degraded notification/aggregate-health status. |
| AC-23 | PASS | B enumerates HTTP controls/details and WS auth/RBAC; viewer mutations denied, query-token WS denied, no arbitrary PATCH/state bypass. C anonymous CLI read denied. |
| AC-24 | PASS | B persisted reservation/input/output/event/config bounds, nonfinite input rejection, request/log/error redaction; I/C private CLI files and safe failure output. |
| AC-25 | PASS | I doctor before schema and before worker returns nonzero/not_ready; running worker reports available. B missing configuration/schema/unavailable dependency and timeout tests; N degraded Redis/health. No hidden model calls. |
| AC-26 | PASS | I image command/content checks and 91 matching shipped file hashes; same image supplies CLI/migrations/example and excludes tests/fakes/demo/UI/removed services. |
| AC-27 | PASS | B disposable legacy/unknown/unmarked relation/schema/view/type/function cases refused before DDL; marker/revision and existing data preserved on repeat migration. Old operator volumes untouched. |
| AC-28 | PASS | R real separate-database pg_dump/pg_restore rehearsal preserves outputs/events/pending approval/auth and independent restored resume. |
| AC-29 | BLOCKED | I/C preserve historical clean-clone/image installation/bootstrap/login and CLI/tool evidence under its original provenance. Current direct image doctor and separate CLI discovery/login PASS, but real-model approval/resume/completion journey stopped at Groq analyst permission failure. No independent completed real-model journey is claimed. |
| AC-30 | PASS | B 218 passed, zero skipped; Ruff/Black/strict MyPy/lock checks pass. Canonical+dev Compose checks and image/CLI/content CI commands pass. Backend-only CI updated; no remote CI run claimed. |
| AC-31 | PASS | S current 58-package main audit has zero known findings; strict source secret checks pass. No broader host/OS/model or exhaustive history-cleanliness assertion. |
| AC-32 | PASS | S current English README/docs/AGENTS/WORKFLOW, reconciled authority/links, MIT/NOTICE review and verified existing issue channel. Manual/unverified model/publication commands explicitly labeled. |

Result: **30 PASS, 2 BLOCKED, 0 FAIL, 0 NOT_RUN** at the acceptance-item level.
Both historical OpenRouter smokes and the direct campaign failed at their first
request; the two acceptance items remain externally BLOCKED. This
supports engineering completion; it does not support fully verified release
readiness or a production-ready claim.

## Removal / retained-obligation mapping

Git baseline history remains the archive. No history rewriting occurred.

| Removed active surface | Replacement / preserved obligation |
| --- | --- |
| Web frontend, datasets, demo seed/accounts, procurement prompts/state, pricing/outbound/Telegram | Generic typed runs; empty install; opt-in packaged text_review; RBAC and human approval retained |
| Knowledge/embedding/RAG/vector/object modules and Qdrant/MinIO settings/services | Bounded PostgreSQL JSON/text; no alternative vector/object stack |
| Selectable fake provider, placeholder-completed nodes, fake fallback/bypass | Real configured adapters and persisted typed failure; provider doubles excluded from image |
| Historical Harness/template/backup/semantic-changeset assets, stale .ai/.codex handoffs, obsolete intake/story guidance | Concise current contributor/agent workflow and one resumable plan; no mandatory control-plane writes |
| Catalog/procurement/outbound governance and old frontend security/defense reports | Generic content-bound approvals, current dependency/security guidance, data/secret protection and historical Git access |

Retired tests map to deliberately removed features. Retained auth, redaction,
provider normalization/errors/retries, lifecycle/approval, events, persistence and
recovery invariants have current executable coverage in B; they were not globally
skipped or replaced with production fakes.

## Remaining release action

Keep AC-08 and the real-model portion of AC-29 BLOCKED. Both OpenRouter attempts
ended with provider_rate_limit, and the direct Groq campaign ended with a fatal
project model-permission failure. Total consumed is **three** (2 OpenRouter,
1 Groq, 0 Cloudflare). Do not delete any marker, rerun/resume failed work, probe,
or reset a budget. No further campaign is authorized. The direct-provider record
does not reuse or extend either historical run's allowance.

The missing release proof remains genuine successful analyst/reviewer chaining,
validated persisted outputs/events, WAITING_APPROVAL, content-bound approval and
explicit resume, pure assembly without a third call, and the documented real-model
image/CLI journey. Existing metadata/quota and fixture checks do not satisfy it.
The original 429 remains unresolved; the new model's failure does not diagnose it.
Keep the plan active and preserve all previous source/image evidence. Any future
live work needs a separate explicit decision, without erasing consumed requests
or changing shared privacy/account policy automatically. Reviewing the intended
isolated Groq project's model permission is the smallest supported next action;
no policy or billing change was made automatically.

Both attempt records, credentials/CLI state, input, database volume and private
raw API evidence remain retained; only the isolated verification services were
stopped. No push, merge, publication or remote deployment was performed.

## Direct Groq → Cloudflare preparation (2026-10-27)

Preparation is complete; **zero new generation requests** were made. The
maintainer will enter new credentials locally. The optional
[operator guide](../direct-smoke-campaign.md) implements one future command,
`python3 scripts/ops/direct_smoke_campaign.py run --approve`, after its documented
credential/plan checks, GET-only preflight, service start, doctor and existing
CLI session/login prerequisites. No bootstrap or new database is needed.

- Tested source: `44a8c42373af1320986ad78d922aa79595775dbe`.
- Prepared release image: `sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`;
  OCI revision matches that source. All **93** shipped file hashes match, and
  image inspection confirms non-root execution, packaged workflow/CLI/migrations
  and exclusion of tests, fake providers and private configuration.
- The bounded shipped changes map Groq GPT-OSS completion/reasoning parameters
  and reuse sanitized error diagnostics for direct compatible providers. An
  overlarge response is invalid output, not an availability fallback trigger.
  Fallback is confined to the opt-in operator helper; normal runtime policy is
  unchanged, with no implicit consent or cross-provider fallback.
- Backend gate: **242 PASS, zero skips/failures**, lock/Ruff/Black/strict MyPy
  PASS; 2 existing dependency deprecation warnings. An earlier gate hit one
  configuration-fingerprint fixture error while source was being edited; the
  frozen full rerun passed without changing that guard. Focused wire/identity/
  Cloudflare diagnostic tests: 5 PASS. Ops: **50 PASS**, including 13 direct
  campaign test methods. Canonical + example-override Compose checks PASS.
- Both real Compose configurations were resolved privately. Four actual-image
  one-off checks (API and worker for each profile, no dependencies started)
  verify the effective model, blank isolated credentials, retry/output/call
  limits, reasoning and preserved restrictive default privacy. No generation
  path was called. Missing-credential preflight correctly blocks before HTTP.
- Private profiles are `.maos/direct-smoke/groq-smoke/private.env` and
  `.maos/direct-smoke/cloudflare-smoke/private.env`, with 0700 directories and
  0600 files. All provider credentials and Cloudflare Account ID remain blank;
  free-plan attestations and authenticated metadata/access checks are pending.
  Git ignores these files; they are outside the backend build context.
- Exact models: direct Groq `openai/gpt-oss-20b` (low reasoning, completion cap
  includes reasoning) and direct Cloudflare
  `@cf/meta/llama-3.3-70b-instruct-fp8-fast` (JSON object mode). Both are priced
  models with free-plan allowances, not zero-priced models. An eligible Groq
  **Free organization** and Cloudflare **Workers Free account** must be checked
  locally; Paid plans/credits are excluded. No portable max-price guarantee is
  asserted. GET-only preflight rechecks exact model availability and required
  Cloudflare schema capabilities before the later run.

The future campaign reserves at most **2 Groq + 2 Cloudflare = 4 new / 6
cumulative requests**, including the 2 historical OpenRouter requests. Retries
are zero at application and HTTP transport, output cap 1024. Successful Groq
approval/resume/assembly stops the campaign without Cloudflare generation.
Only an eligible terminal Groq availability failure permits one separate
Cloudflare run from the original input, after stopping API/worker and confirming
no work can continue. Fatal auth/config/billing/schema/state failures stop.
Campaign/provider markers are exclusive and persistent; reinvocation cannot
reset the budget. No campaign or provider-attempt marker has been created yet.

All **43 recorded historical artifact hashes** remain intact. The existing
database/admin/application secrets/volume/CLI/input are reused; all four isolated
services remain stopped. Source/image/content proof, checks and limitations are
recorded in [preparation evidence](direct-smoke-preparation.json). Earlier
evidence retains its original source/image provenance. Final documentation-only
handoff commits do not change this tested image or require a rebuild.

Acceptance remains **30 PASS / 2 BLOCKED**. Genuine chained analyst/reviewer
outputs and the documented image/CLI approval-resume journey are still missing.
No inference, push, merge, publication, remote deployment or deletion of retained
resources occurred during this preparation. A later successful direct provider
would not diagnose either earlier OpenRouter 429 or establish enterprise readiness.

### Bounded metadata preflight correction (2026-10-27)

After the maintainer entered both private credentials/account ID and confirmed
the native Free plans, the old helper reported only `metadata_HTTP_403`. Its
original response body/headers and request identity were not retained. Safe
diagnostics were added before reproduction: URL-derived target/operation,
GET/host/masked path, actual status/MIME, bounded error code/type, sourced
request IDs/cf-ray and auth scheme/header presence. No messages, raw response,
Authorization value, Account ID or resolved secret configuration are logged.

Four authenticated metadata GETs were performed, without automatic retry:

| Target / operation | Status | Request setup |
| --- | --- | --- |
| Groq `GET /openai/v1/models` | 403, JSON | Existing urllib default User-Agent |
| Groq `GET /openai/v1/models` | 200, JSON | Explicit application User-Agent |
| Cloudflare `GET /client/v4/accounts/{ACCOUNT_ID}/ai/models/search` | 200, JSON | Explicit application User-Agent |
| Cloudflare `GET /client/v4/accounts/{ACCOUNT_ID}/ai/models/schema` | 200, JSON | Explicit application User-Agent |

The narrow request fix sets
`User-Agent: Multi-Agent-OS/SPEC-029-metadata-preflight`; the Groq credential,
URL, method and Bearer auth remain identical. Full **PREFLIGHT_PASS** verifies
both exact selected models and required Cloudflare schema parameters. This
supports a client-header compatibility fix; the precise server-side blocking
rule was not returned. The reproduced 403 captured no error code/type or Groq
request identifier at the supported fields, but did return `header.cf-ray`.
That edge ID does not identify Workers AI as the target. No invalid-key,
paid-plan or unavailable-model conclusion follows from the 403 alone.

Official Groq model-list and Cloudflare account-scoped search/schema endpoints
and Bearer auth match the helper. Both Cloudflare metadata operations accept
Workers AI Read or Workers AI Write for the intended account. No billing,
administrative or token-management API was called; no broader token scope,
account setting, credential replacement or Free-plan relaxation was needed.
TLS verification and no-redirect/no-retry behavior remain intact.

Only host helper/tests/documentation changed. The prepared runtime source
`44a8c42373af1320986ad78d922aa79595775dbe` and image
`sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`
are unchanged; no rebuild is warranted. Ops regression: **53 PASS** (16 direct
campaign methods); script Black/Ruff and canonical/override Compose PASS. Required
backend gate: **242 PASS, zero skips/failures**, lock/Ruff/Black/strict MyPy PASS
with two dependency deprecation warnings. See
[sanitized diagnostic evidence](direct-preflight-diagnosis.json) for response
IDs, limits, checks and preserved artifact identities.

New generation remains **0**, historical OpenRouter requests **2**; campaign cap
remains 2/provider, 4 new/6 cumulative. No campaign/attempt marker was created,
no operator service was started, and credentials/configuration/plan bindings,
input/CLI state and all 43 historical artifact hashes remain unchanged.
At that preflight closeout, the existing campaign was ready for explicit
initiation after local start/doctor/auth prerequisites. The later execution is
recorded below. **30 PASS / 2 BLOCKED** remained unchanged:
AC-08 and live AC-29 still require genuine workflow execution. No push, merge,
publication, remote deployment or deletion of retained resources occurred.

## Executed direct campaign: project permission failure (2026-10-27)

The maintainer explicitly initiated the prepared campaign after requiring a
final offline inference-transport check. The **actual pinned release image**,
with network disabled and HTTPX MockTransport capture, serialized an explicit
`User-Agent: multi-agent-os/0.2.0`, Bearer auth and application request ID. Token
cap 1024, Groq low reasoning, timeout, no redirects and zero application/transport
retries were verified. Eight focused provider tests passed. No shipped code or
image input changed; source `44a8c42373af1320986ad78d922aa79595775dbe` and image
`sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`
were reused. This was an offline transport proof, not a generation probe.

GET-only preflight passed again; the existing isolated services started, doctor
passed, and the maintainer refreshed an expired CLI token locally for the
existing administrator. A separate CLI invocation discovered `text_review`.
No bootstrap, replacement user, migration or application secret regeneration
was performed. Original input/credential/Free-plan/profile identities were kept.

Exactly one `run --approve` invocation created Groq run
`8573b056-b869-416b-87e6-e03569dbfb5f`, pinned to requested model
`openai/gpt-oss-20b`. The analyst's one generation HTTP request returned **403**,
code **`model_permission_blocked_project`**, type **`permissions_error`**;
application category `provider_authentication`. Provider response request ID
from `header_x_request_id` is `req_01m5ye2kxtex8rqe5ggyvb8neq`, distinct from
application request ID `cf596e10-a921-4004-a6cc-6cadf67cf833`.

[Groq's documented error](https://console.groq.com/docs/model-permissions)
identifies a project-level model restriction. It is not an eligible availability
failure: Cloudflare remained unused, with no attempt record or generation call.
No model change, permission/billing change, fallback override, repair or retry
was attempted. Metadata discovery success did not establish model execution
permission. No returned generation model, usage or cost was reported; these
remain unknown, without assuming zero cost or upstream execution.

The run is **FAILED**, ownership/lease cleared. Its one analyst execution and
six contiguous durable events (`run.created`, `run.queued`, `run.started`,
`node.started`, `node.failed`, `run.failed`) were read back through the API.
There is no validated analyst/reviewer output, WAITING_APPROVAL, decision,
resume, assembly or final output. Both historical OpenRouter runs compare
unchanged, and all 43 historical artifact hashes still match.

Campaign identity is the SHA256 of its unmodified `campaign.json`, since the
runner assigns no separate campaign UUID:
`1e51ed922000dd7fabbc421234fd02985ebd89a2c302d4dac07122e5cae06cfc`.
Consumed: **1 Groq / 0 Cloudflare / 1 new / 3 cumulative**, including two
OpenRouter requests. Limits remain 2/provider, 4 new/6 cumulative; unused
reservation does not authorize another attempt. Campaign/provider markers and
all evidence remain retained. The runner stopped all four isolated services
after collecting evidence; volumes, input, configuration, credentials and CLI
state remain. No new campaign is authorized.

**AC-08 remains BLOCKED** because genuine successful chained calls were not
observed. **AC-29 independently remains BLOCKED** because the real-model
operator journey did not reach approval/resume/completion; current image
doctor/CLI discovery success does not complete it. Historical clean-clone
evidence retains its original source/image identity. Acceptance stays
**30 PASS / 2 BLOCKED**; the live campaign itself is FAIL, without an established
implementation defect. [Sanitized campaign evidence](direct-campaign-attempt.json)
contains node/event identifiers, diagnostics and hashes/paths of retained private
artifacts. No raw text/provider body or credential is published.

The smallest next action is maintainer review of the intended isolated Groq
project's model restrictions in **Settings → Projects → Limits**, without
weakening shared production policy or changing billing. No settings were
changed automatically. Any later live attempt needs a separate explicit decision
while retaining this consumed campaign and all historical counts. No push,
merge, publication, remote deployment or retained-data deletion occurred.
