# SPEC-029 acceptance evidence

The original implementation and its recorded non-live acceptance checks are complete.
Fully verified release readiness remains **BLOCKED** by AC-08 and the real-model
portion of AC-29. The maintainer authorized one bounded OpenRouter live attempt
following preparation. It **failed on the analyst's first request** with durable
`provider_rate_limit`, before any reviewer or approval. No retry or new run was
made. [Live attempt evidence](openrouter-live-attempt.json) records the result;
fixture responses are never counted as real model evidence. No model weights
were downloaded.

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
| AC-08 | BLOCKED | Authorized genuine OpenRouter attempt failed on analyst request with `provider_rate_limit`; run `75039b34-2bf1-4e89-a1c1-704dd2f0be28`, call count 1. No reviewer or successful chained outputs. See live-attempt evidence. |
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
| AC-29 | BLOCKED | I/C verify clean local clone, final-image installation/bootstrap/private persistent login and CLI/tool journey. The full README real-model text_review/probe journey remains blocked by AC-08; public clone is a manual example until publication, which was not authorized. |
| AC-30 | PASS | B 218 passed, zero skipped; Ruff/Black/strict MyPy/lock checks pass. Canonical+dev Compose checks and image/CLI/content CI commands pass. Backend-only CI updated; no remote CI run claimed. |
| AC-31 | PASS | S current 58-package main audit has zero known findings; strict source secret checks pass. No broader host/OS/model or exhaustive history-cleanliness assertion. |
| AC-32 | PASS | S current English README/docs/AGENTS/WORKFLOW, reconciled authority/links, MIT/NOTICE review and verified existing issue channel. Manual/unverified model/publication commands explicitly labeled. |

Result: **30 PASS, 2 BLOCKED, 0 FAIL, 0 NOT_RUN** at the acceptance-item level.
The authorized live smoke ran and failed at the first request; the two acceptance items remain externally BLOCKED. This
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

Keep AC-08 and the real-model portion of AC-29 BLOCKED. The authorized attempt
has ended after `provider_rate_limit`; do not invoke the helper again, remove
`attempt.json`, resume the failed run or use the unused call allowance for a retry.
Investigate free-route quota/availability through non-inference account/support
information without weakening global policy. A later live attempt needs a new
explicit maintainer budget decision; no model/route switch is authorized.

The original release obligations remain: successful real analyst then reviewer,
persisted validated outputs/metadata/events, WAITING_APPROVAL, normal content-bound
approval and explicit resume, pure assembly without a third generation, and the
documented real-model image/CLI journey. The isolated [guide](../openrouter-free-smoke.md)
describes the flow but does not authorize replay of this failed attempt. Separate
README provider probing remains outside this attempt's budget. Do not archive the
active plan or promote AC-08/AC-29 without the actual missing evidence.

Prior [cleanup evidence](cleanup-evidence.json) and source/image provenance remain
historical. The new isolated services are stopped with volumes/configuration and
all private evidence retained. No publication, remote deployment, push or merge
was performed.
