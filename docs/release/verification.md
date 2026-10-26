# SPEC-029 acceptance evidence

Status: verification in progress; this is not a release-readiness declaration.
The maintainer explicitly chose to leave AC-08 BLOCKED: no real installed,
configured local model is available, and no live or remote inference is authorized
for this verification pass. Fixture inference is never counted as live evidence.

Source under inspection: branch `feat/spec-029-headless-oss`, based on
`92e5f1cfb2b0144bdb39a48db99371974bd372a5`, plus the current implementation
worktree. Final checked source commit and final image ID are pending; the parent
verification pass must replace this provisional identity before delivery.
Intermediate images are not proof of the final release artifact.

PASS means the named observed check covers that criterion. NOT_RUN identifies
remaining proof, even when narrower tests already pass. BLOCKED names an external
capability or explicit operator decision. No skipped test is counted as PASS.

## Observed checks

- **D1 — Definitions/provider contracts:** from `backend/`,
  `.venv/bin/python -m pytest app/tests/test_definitions.py app/tests/test_llm_generic.py app/tests/test_llm_provider_clients.py app/tests/test_llm_provider_error_mapping.py app/tests/test_llm_contracts.py -q`:
  **57 passed**. Strict MyPy of definitions/LLM/examples/live smoke: **20 files
  clean**. Provider responses in these tests are injected fixtures.
- **D2 — PostgreSQL runtime/API/migration integration:**
  `MAOS_TEST_DATABASE_URL=<isolated PostgreSQL DSN> .venv/bin/pytest app/tests/test_runtime_durable.py app/tests/test_alembic_headless.py app/tests/test_api_headless.py -q --tb=short`:
  **20 passed, 38.50 s** in the observed intermediate worktree. A broader final
  run, including restore and subsequently added cases, is pending.
- **S1 — Locked main Python dependency audit:**
  `uv tool run pip-audit --requirement /tmp/maos-spec029-requirements.txt --no-deps --disable-pip --format json --output /tmp/maos-spec029-dependency-audit-patched.json`:
  **58 dependencies, zero known vulnerabilities**, exit 0. The durable
  [audit artifact](dependency-audit.json) records versions/lock identity. This is the exported
  main graph after remediation; it does not audit host/container OS, custom
  extensions or model artifacts.
- **S2 — Source secrets:**
  `python3 scripts/ops/scan_secrets.py --strict --allow-test-placeholders --json`:
  **147 retained tracked files, zero findings**. The same scanner API supplied
  `git ls-files --cached --others --exclude-standard` also checked **186 current
  tracked/untracked files, zero findings**. `python3 -m unittest
  scripts.ops.test_scan_secrets -q`: **11 passed**. Test fixtures and ignored local
  secrets are outside the committed-source scan. Arbitrary shell substitutions
  remain findings; the reviewed random-secret generator is recognized as code.
- **S3 — Removed dependencies/imports:** bounded `rg` over `backend/app`,
  `backend/maos_examples`, manifest/lock/Dockerfile, canonical Compose, CI and
  `.env.example` found **zero** imports/references to removed application modules,
  fake provider selection, retired runtime/fallback settings, Qdrant or MinIO
  packages. Historical migration/security prose is not an active runtime import.
- **S4 — Existing security reporting channel:** read-only
  `gh api repos/hzjanuary/multi-agent-system --jq '{html_url,has_issues,private}'`
  confirmed the existing repository URL and `has_issues=true`. SECURITY.md uses
  that non-sensitive coordination channel and advertises no invented private
  mailbox or response SLA.
- **E1 — Environment:** Linux `7.0.0-38-generic` x86_64; Docker Engine `29.9.2`;
  Compose `5.6.1`. `command -v ollama` found no installed CLI, no installation
  `.maos/` model configuration existed, and observed host listeners did not
  include the usual local model port 11434. No model was downloaded or called.

## Acceptance matrix

| ID | State | Evidence / exact remaining scope |
| --- | --- | --- |
| AC-01 | NOT_RUN | Intermediate runtime image built; final-image clean isolated Compose migration/start remains in progress. No frontend/Node/vector/object dependency remains in source (S3). |
| AC-02 | NOT_RUN | D2 fresh migration asserts zero application records. Final-image pre/post explicit administrator bootstrap inspection remains in progress. |
| AC-03 | NOT_RUN | Bootstrap tests and CLI implementation exist; final observed bootstrap/repetition proof pending. |
| AC-04 | NOT_RUN | D1 negative fake/fallback/disabled settings pass; source fake implementation removed. Final release-image negative configuration/content inspection pending. |
| AC-05 | PASS | S3 zero retired-module imports; D1 imports retained real provider clients. Final image import/content is separately AC-26. |
| AC-06 | PASS | D2 `test_two_unrelated_workflows_one_graph` executes unrelated typed definitions through installed test extension code with real PostgreSQL. |
| AC-07 | PASS | D1 real provider adapters and D2 runtime integration use the same agent/tool dispatch inside `build_workflow_graph`; production has one LangGraph path. Live inference remains AC-08. |
| AC-08 | BLOCKED | Maintainer explicitly chose no live inference in this pass. No installed/configured local model; no remote provider authorization. Bounded executable `scripts/ops/live_text_review.py` is provided but not run live. |
| AC-09 | PASS | D1 missing model/key/unsafe endpoint, rejected authentication, transport timeout, exhausted transient retries and budget refusal fail; no fake/fallback route exists. |
| AC-10 | NOT_RUN | D1 production JSON/schema parser fails invalid output; D2 persisted validation failure stops later nodes and is read from another session. A single production-parser→worker→PostgreSQL composition check remains to establish full integration scope. |
| AC-11 | NOT_RUN | D2 durable HTTP submission and independent worker process are covered separately. Explicit API process restart/client-disconnect proof remains. |
| AC-12 | PASS | D2 controlled worker subprocess loss/restart preserves committed checkpoint output; old generation cannot commit and completed work is not recomputed. |
| AC-13 | PASS | D2 interrupted non-idempotent observable test handler refuses recovery with `unsafe_resume_requires_reconciliation`; pure/idempotent explicit recovery differs. |
| AC-14 | NOT_RUN | D2 keyed/unkeyed concurrent starts and transactional claims yield one active owner. Explicit concurrent-resume proof is being added before full criterion PASS. |
| AC-15 | NOT_RUN | D2 concurrent create, identical create/start/resume replay, changed creation input and changed start target pass. Explicit changed-resume-target and unsupported body rejection checks are being added. |
| AC-16 | PASS | D2 approval state is read through new service/session, stale revisions/content conflict; D2 API role checks protect decisions and explicit resume. Final CLI surface proof is included in pending AC-29. |
| AC-17 | PASS | D2 conflicting concurrent approval decisions produce one committed outcome; row serialization plus unique persisted request identity protects it. |
| AC-18 | PASS | D2 waits at approval, records APPROVED without downstream execution, then requires explicit resume. Sequential independent approvals are exercised. |
| AC-19 | PASS | D2 in-flight cancellation rejects late results; stale fenced ownership cannot overwrite current terminal state. |
| AC-20 | PASS | D2 failed-node state/error/events are read from an independent new database session after the failing operation; later nodes remain unexecuted. |
| AC-21 | PASS | D2 transaction rollback does not publish an event; ordered PostgreSQL replay and authenticated WS backlog/reconnect/live polling cover missed notifications. |
| AC-22 | NOT_RUN | D2 failed-notifier injection leaves committed state/replay intact; stopping a real Redis service and observing degradation plus durable replay still needs direct evidence. |
| AC-23 | PASS | D2 enumerates every current HTTP read/control route against unauthorized/viewer/operator roles, checks WS bearer header and rejects query-token auth; no public PATCH/state-replacement route exists. |
| AC-24 | NOT_RUN | D1 provider budget/limit/redaction and D2 input/event/call limits pass. Final combined log/CLI/malformed-input checks and global quality pass pending. |
| AC-25 | NOT_RUN | Unit readiness/settings and D2 schema refusal checks exist; final actual-image doctor/schema/worker/degraded-notification observations pending. No hidden inference is implemented. |
| AC-26 | NOT_RUN | Intermediate image includes CLI/migrations/examples and excludes tests/fakes/retired services; final source/image rebuild and inspection pending. |
| AC-27 | PASS | D2 new-lineage migration tests refuse legacy, unknown and nonempty-unmarked databases without mutation and preserve populated current data on repeated upgrade. Disposable separately named databases only. |
| AC-28 | NOT_RUN | Separate-database `pg_dump`/`pg_restore` rehearsal is being executed; completed output, pending approval, event identity/order and authentication/refresh assertions await observed result. |
| AC-29 | NOT_RUN | Actual final-image README walkthrough, including separate CLI login and authenticated command containers, remains in progress. |
| AC-30 | NOT_RUN | Focused D1/D2 pass, but full test/Ruff/Black/MyPy/lock/Compose/final-image gates must finish after all source edits. |
| AC-31 | PASS | S1 current main graph: zero known findings after patches. S2 redacted strict current-source scan: zero findings. Scope excludes OS/host/model audits and exhaustive Git-history secret analysis; no broader claim. |
| AC-32 | NOT_RUN | English product docs, current authority and selected MIT/NOTICE exist; source/header provenance review and final local-link/content review are pending completion. Existing issue reporting verified (S4). |

## Removal and retained-obligation inventory

The baseline revision is the historical archive; no Git history or operator data
was deleted. Runtime imports and CI references were reviewed before extraction.

| Removed surface | Replacement / preserved obligation |
| --- | --- |
| `frontend/`, datasets, demo seed/accounts, fixed procurement schemas/prompts, pricing/outbound/Telegram | Generic typed runs, empty new install, opt-in real `maos_examples.text_review`; human approval and explicit resume retained |
| Knowledge/embeddings/RAG/vectorstore/object storage and associated infrastructure/settings | Bounded JSON/text in PostgreSQL; no replacement object/vector subsystem |
| Production fake client, placeholder success, fake fallback and runtime bypass switch | Real configured providers, typed failure, test doubles confined to tests |
| `.harness-*`, obsolete `.ai`/handoff/template/semantic-changeset tooling, `TOOL_REGISTRY.md`, `GLOSSARY.md`, story/intake/high-risk templates | Concise AGENTS/WORKFLOW and one resumable plan; no mandatory intake/control-plane writes |
| `docs/governance/` catalog, procurement/provider-evidence and outbound policies | Current generic RBAC, content-bound approvals, no outbound tools; security/data protection still required |
| Uppercase placeholder architecture, historical SPEC-025 triage/remediation reports and frontend dependency instructions | Current backend dependency/security maintenance guidance; historical evidence remains at baseline |

Retained test contracts were rewritten where their public behavior changed.
Removed LLM fake/procurement/prompt/fallback tests map to deliberately retired
features; typed invocation, validation, transport normalization/error mapping,
retries, resource limits and secret redaction remain covered by D1.

## Remaining release gates

The final proof pass must record its exact source commit/image, completed global
checks and installation/restore evidence, then update every NOT_RUN cell. The
maintainer-selected AC-08 blocker remains explicit. Engineering completion and
fully verified release readiness must be reported separately.
