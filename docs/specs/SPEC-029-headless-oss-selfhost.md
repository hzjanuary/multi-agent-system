# SPEC-029 — Headless Multi-Agent OS: open-source self-host refactor

## 0. Document status and authority

| Field | Value |
| --- | --- |
| Repository | https://github.com/hzjanuary/multi-agent-system |
| Reviewed baseline | 92e5f1cfb2b0144bdb39a48db99371974bd372a5 |
| Prepared | 2026-10-26 |
| Canonical destination | docs/specs/SPEC-029-headless-oss-selfhost.md |
| Status | Proposed implementation contract; activated when the maintainer submits the accompanying /goal |
| Intended release | A breaking, pre-1.0 headless release; use 0.2.0 only if the actual repository version still permits it |
| Product name | Multi-Agent OS |
| Engineering target | A single-host multi-agent workflow runtime with REST API and CLI |
| Public documentation | English |
| Implementation reports | Vietnamese, unless the maintainer requests otherwise |
| Proposed license | MIT for material the maintainer has the right to license; selected explicitly by the accompanying /goal |

This document specifies future behavior. Its commands, paths and API examples are target contracts, not claims that those features already exist. The baseline assessment is a static source review; no application tests, container builds or live-provider calls were executed while preparing this specification.

The maintainer's request is to remove the current web application, demonstration data and obsolete semantic/demo features, preserve and generalize the multi-agent core, and prepare a usable open-source self-hosted project with a rewritten README.

Once adopted, this specification supersedes conflicting graduation-product requirements in the old SPEC.md, .ai/project/*, .ai/specs/* and related product documents: the mandatory Next.js interface, fixed procurement pipeline, seeded demo accounts, fake runtime, semantic/RAG services and defense-demo packaging. It does not waive security, data protection, validation, third-party licensing or external-action authorization.

The current AGENTS.md and docs/WORKFLOW.md already describe legacy Harness control-plane operations as optional. Use one durable execution plan. Do not run mandatory historical intake/story/trace commands just to authorize this explicitly requested refactor. Update product guidance that contradicts this specification; do not redesign the general Harness as a separate project.

Reinspect the actual checkout before changing it. If HEAD differs from the reviewed baseline, record the differences that affect this plan. Do not reset the checkout to this SHA, overwrite unrelated work or assume source observations prove a reproduced runtime defect.

## 1. Product outcome

Multi-Agent OS is a headless, self-hosted runtime for defining and executing typed multi-agent workflows. Operators run it on infrastructure they control, select a real model provider, submit their own input, inspect durable results/events, and approve or resume workflows through the CLI or API.

“OS” is branding for this application runtime. Do not claim an operating-system kernel, general-purpose autonomous computer control, distributed agent cluster, sandbox for untrusted code or enterprise platform.

A new operator must be able to:

1. Clone the repository and configure the supported stack without Node.js.
2. Build the release image, initialize a fresh database, and explicitly create their administrator.
3. Choose a real local model endpoint or supported remote provider.
4. Enable a documented example workflow, submit their own text and execute at least two distinct agent steps.
5. Observe persisted outputs and events, including across an API or worker restart.
6. Make an authorized approval decision and explicitly resume where the workflow requires it.
7. Add an unrelated workflow through the documented extension contract without editing the runtime engine.
8. Back up, restore and upgrade the new installation using documented procedures.

A clean installation contains no business records, demonstration accounts, fabricated run results or pre-created activity. System roles, migration metadata and explicitly installed static workflow definitions are configuration, not seeded business data.

## 2. What the baseline actually contains

Use these observations to guide discovery; verify them against the current checkout.

| Observation | Evidence at the reviewed SHA | Required response |
| --- | --- | --- |
| The only workflow type is procurement_quotation; state contains customer, items, quotation, compliance and email. | backend/app/workflows/schemas.py | Replace domain-specific contracts with generic workflow/run/node contracts. |
| RuntimeStage enumerates seven fixed procurement stages and graph.py builds their linear chain. | backend/app/runtime/schemas.py; backend/app/runtime/graph.py | Use registered definitions and stable node IDs instead of a fixed business-stage enum. |
| Default node handlers explicitly mark placeholder outputs completed. | backend/app/runtime/nodes.py | Remove placeholder-success execution from shipped code. |
| Real provider clients already exist, alongside fake configuration and client paths. | backend/app/llm/clients/*; backend/app/llm/factory.py; backend/app/config/settings.py | Reuse real adapters and error handling; make fakes test-only. |
| Prompts and structured outputs remain procurement-specific. | backend/app/llm/prompts/*; backend/app/llm/structured_outputs.py; backend/app/runtime/llm_adapter.py | Generalize the agent invocation boundary, not just the filenames. |
| Real LLM stages and deterministic graph execution use different paths. | backend/app/runtime/service.py | Establish one authoritative orchestration path. |
| Knowledge retrieval imports a demo document catalog; the embedding provider enum only supports fake. | backend/app/knowledge/retrieval.py; backend/app/knowledge/embeddings.py | Remove the old knowledge/RAG/vector feature, including read-time defaults. |
| Readiness always checks PostgreSQL, Redis, Qdrant and object storage. | backend/app/core/readiness.py | Remove deleted-service coupling from startup and readiness. |
| The runtime image omits migration files that the dev image contains. | backend/Dockerfile | Ship migrations and administrative commands in the real release image. |
| Initial user creation is coupled to demo seeding. | backend/app/demo/user_seed.py | Replace it with explicit operator bootstrap. |
| CI and gates still build/test frontend and run demo seed/ingest commands. | .github/workflows/ci.yml; scripts/ci/* | Validate the new product rather than skipping obsolete failing stages. |
| The environment validator treats fake/disabled LLM settings as the stable profile. | scripts/ops/validate_environment.py | Replace demo-specific validation with real self-host configuration checks. |
| Run execution is awaited in the HTTP request; checkpoint, event commit and concurrency behavior need stronger proof. | backend/app/api/v1/workflows.py; backend/app/runtime/service.py; backend/app/workflows/events.py | Introduce durable submission and explicit per-node persistence/recovery tests. |
| The README only states that this is an academic graduation project in its license section; the inspected tree has no LICENSE. | README.md; repository tree | Add an explicitly selected license and preserve third-party obligations. |
| Development Harness includes SQLite/semantic-changeset tooling distinct from the product runtime. | docs/WORKFLOW.md; docs/HARNESS.md; scripts/schema/* | Do not confuse development tooling with the LangGraph runtime. |

Existing fallback is disabled by default and includes metadata when used. Do not misdescribe all current fallback as silent. The new requirement is stricter: no production-selectable fake provider or fabricated success.

Source inspection also suggests risks around failure-state rollback, publish-before-commit and backlog/live event handoff. These are hypotheses to reproduce with integration tests, not already reproduced incident reports.

## 3. Scope decisions

### 3.1 Keep and generalize

- Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic and PostgreSQL.
- LangGraph as the workflow orchestration implementation.
- Existing real LLM transports/adapters, structured-output validation, bounded retries and sanitized error categories.
- Human approval, explicit resume, audit events and access control.
- PostgreSQL event history and Redis event notification.
- Relevant authentication, authorization, redaction, lifecycle and provider-error tests.
- Docker-based installation and local development.
- Generated OpenAPI/Swagger documentation. This is API documentation, not a replacement application frontend.

Keep the existing backend/app layout where practical. Do not combine this work with an unnecessary rewrite into another language, database, package manager or framework.

### 3.2 Remove from the active product and runtime image

| Surface | Concrete removal scope |
| --- | --- |
| Web application | frontend/, frontend env files, Node/Next/React dependencies and lockfile, frontend Docker service/build, browser-only tests, screenshots and frontend CI gates. |
| Demo data | datasets/, backend/app/demo/, seed commands, sample users/passwords, customer/product catalogs, RFQs, prices, contracts, expected quotes and synthetic workflow history. |
| Semantic/RAG feature | backend/app/knowledge/, backend/app/vectorstore/, runtime/rag_adapter.py, knowledge routes, embedding/RAG settings, ingestion commands and old knowledge tests. |
| Vector/object infrastructure | Qdrant and MinIO services, dependencies, readiness checks, settings and code used only by removed knowledge functionality. Inspection currently shows no independent runtime artifact requirement for MinIO. |
| Procurement application | backend/app/price_research/, procurement prompt/output models, fixed quotation/compliance/email state, catalog-specific policies and public outbound-preview routes. |
| Demo communication | backend/app/outbound/ preview-only feature, sales/quotation Telegram bridge, Tavily/quotation demo utilities and their obsolete evaluation datasets. |
| Academic packaging | Active defense/demo/report instructions, screenshot runbooks, fixed-count evaluation claims and production-demo release scripts. Preserve historical access through the baseline Git revision. |
| Fake production behavior | FakeLLMClient as a selectable runtime provider, fake embedding paths, fake fallback settings and placeholder-completed nodes. |

Removal includes imports, dependency injection, schema exports, lockfiles, package manifests, scripts, configuration validation, documentation links, health checks and CI references. Turning flags off is insufficient.

### 3.3 Interpretation of “semantic” and legacy Harness

For this release, application-level “semantic” removal means the existing demo knowledge, embedding, vector-search and RAG subsystem. No semantic-kernel dependency was found in the inspected Python manifest; do not invent one.

Separately inventory the development Harness assets, including .harness-core/, .harness-backup/, old onboarding/intake skills, scripts/schema/, README_STARTER_KIT.md, docs/HARNESS*, and obsolete .ai/.codex handoff material. Classify them by runtime imports, CI references and active contributor use.

Remove obsolete template/backups, semantic-changeset compatibility tooling and stale process instructions from the active distribution when the inventory confirms no retained dependency. Preserve only concise current contributor/agent guidance and required notices. Record removals in the plan; Git history is the historical archive.

Never delete by matching the word “semantic,” “agent,” “mock” or “state” across the repository. Language about API semantics, semantic versioning, application state and real deterministic processing is not a feature-removal target.

### 3.4 Explicitly outside this release

- A replacement web UI, dashboard, chat application or low-code workflow editor.
- RAG, vector memory, embeddings or an alternative vector database.
- CRM, sales, procurement, pricing, email delivery, Telegram bots or another business demo.
- Autonomous planner loops, recursive agent spawning, arbitrary DAGs, parallel fan-out, distributed scheduling or multi-host high availability.
- Remote plugin marketplaces, arbitrary code from API requests, shell/browser execution, MCP integrations or an untrusted-code sandbox.
- SaaS multi-tenancy, billing, SSO, Kubernetes, Terraform and managed cloud deployment.
- Automatic migration of existing procurement/business data into generic runs.
- Publishing packages/images/releases, pushing tags, changing repository visibility, sending messages or deploying to somebody else's server.

Sequential, typed multi-agent workflows with optional explicit approval nodes are the intended first-release capability. Do not silently expand that into a new general agent platform.

## 4. Target architecture

~~~mermaid
flowchart TD
  Client["CLI or API client"] --> API["FastAPI API"]
  API --> DB[("PostgreSQL: runs, jobs, events")]
  Worker["Worker: LangGraph execution"] <--> DB
  Worker --> Models["Configured model provider"]
  Worker --> Redis["Redis: event notifications"]
  Redis --> API
~~~

### 4.1 Services

| Service | Responsibility |
| --- | --- |
| api | Authentication, definition discovery, run submission/control, results and event retrieval/streaming. |
| worker | Claims durable jobs, executes real agent/tool nodes, persists progress and recovers interrupted ownership. |
| postgres | Authoritative runs, node executions, approvals, job claims, event history, users and refresh sessions. |
| redis | Low-latency event notification only; not the authoritative run state or a correctness-critical job queue. |
| migrate | One-shot command from the same application image; not a separate development/test image. |
| ollama | Optional explicitly enabled local-model Compose profile or an externally configured endpoint. No automatic model download. |

Use one application image for API, worker, migrations and CLI. The normal stack has one API and one worker. PostgreSQL-backed job claiming is sufficient; do not add Celery, Kafka or another scheduling framework.

Redis can be degraded without losing runs or events. Database event polling/replay must remain correct when Redis is unavailable. Document this explicitly; health must not misleadingly imply notification delivery is normal.

### 4.2 Code boundaries

The exact directory names below may be adapted to existing conventions; the dependency boundaries are mandatory.

| Boundary | Intended contents |
| --- | --- |
| config, db, models, repositories | Validated configuration and persistence. |
| agents / workflows definitions | Typed agent, tool and workflow definitions plus explicit registration. |
| runtime | Graph construction, execution, limits, cancellation, checkpoints and recovery. |
| llm | Provider-neutral invocation, real adapters, transport and response validation. |
| approvals | Generic pending gates, actor decisions and resume authorization. |
| events / streaming | Persisted event contracts and committed-event notification/replay. |
| api | Thin HTTP/WS adapters; no duplicate workflow engine. |
| cli | Thin operator commands using the same services or public API. |
| tests | Fixtures, test doubles and behavior/integration coverage. |
| examples | Explicitly enabled small extension examples with user-supplied input. |

Core imports must not depend on examples, demo catalogs or retired business schemas. The API and CLI must not each implement their own orchestration loop.

## 5. Generic definition and state contracts

### FR-01 — Agent definitions

An agent definition has:

- Stable id and version.
- Human-readable name and one clear responsibility.
- Instructions supplied by the installed definition.
- Pydantic input and output schemas.
- A provider/model reference resolved from operator configuration.
- Timeout and bounded output limits.
- No credentials embedded in the definition, run snapshot or API response.

An invocation validates input, calls a real provider, validates output and records provider/model/attempt metadata. Multiple agents may use the same model with different responsibilities; do not require multiple cloud accounts.

Agents do not approve requests, mutate arbitrary run status, choose arbitrary Python modules or bypass output validation. The workflow graph controls transitions.

### FR-02 — Tool definitions

A registered tool is a real deterministic operation with typed input/output. Examples include text normalization, numeric calculation or assembling already validated results.

Each tool declares whether it is pure, idempotent or potentially non-idempotent, plus whether approval is required. Installed Python extensions run with the worker's privileges; this release does not sandbox untrusted code.

Do not ship general-purpose shell, arbitrary HTTP-fetch, filesystem-write or messaging tools. An explicit control node may record a real lifecycle transition without making an LLM call; that is not fake inference.

### FR-03 — Workflow definitions

A workflow definition has:

- Stable id, immutable version and definition hash.
- Typed external input/output.
- An ordered list of uniquely identified agent, tool or approval nodes.
- Explicit input mappings from the run input or validated prior node outputs.
- A designated final output mapping.
- Bounded execution limits.

Use a code-first Python registration interface with typed models. Operator-installed modules may be enabled through a documented allowlist such as MAOS_EXTENSION_MODULES. Both API and worker load and validate the same definitions. No public endpoint accepts executable Python, eval expressions, arbitrary imports or remote package installation.

Reject duplicate IDs, missing references, invalid mappings, unsupported node types, unbounded loops and malformed definitions before creating an executable run.

Workflow definitions are configuration. They may be discovered via API without creating run rows. The default registry may be empty. An empty registry must return an honest empty result, not synthesize an example.

Persist an immutable serializable definition snapshot/hash with each run. Its canonical identity includes agent instructions, schema identities, mappings, node types, limits and registered handler implementation identities. Enabled extensions expose an immutable version and a reproducible artifact fingerprint; do not hash function repr or process-specific addresses. API and worker compare the same identity before accepting/claiming work. Missing extensions or changed definition/implementation fingerprints block resume clearly. Do not serialize executable Python into the database.

### FR-04 — Generic run state

The external state model includes:

| Area | Required information |
| --- | --- |
| Identity | Run ID, workflow ID/version/hash, schema version and creator. |
| Data | Validated input, bounded JSON context, validated node outputs and final output. |
| Lifecycle | Status, state revision, current/pending node, timestamps and cancellation request. |
| Execution | Attempt metadata, execution generation/claim, limits and structured errors. |
| Approval | Pending approval identity, approved content revision/hash and final decision references. |
| Events | Durable event cursor and separately paginated history. |

Customer, items, quotation, compliance, email and procurement_quotation must not be mandatory core fields or enums.

Normal run responses return summaries and final output; node outputs and event history are fetched through bounded detail/list endpoints. Never return an unbounded growing event array with every state update.

The main product stores bounded JSON/text outputs in PostgreSQL. File attachments and object storage are out of scope; do not create a new storage subsystem to replace MinIO.

### FR-05 — Extension proof

Add one public opt-in example: text_review.

1. An analyst agent structures user-supplied text.
2. A reviewer agent consumes the analyst's validated result.
3. An approval node pauses on the concrete reviewed result.
4. After a recorded approval and explicit resume, a pure tool assembles the final output.

There is no bundled customer dataset, prerecorded answer, generated sample history or automatic execution. The example is an extension loaded explicitly by the operator.

Package the example as maos_examples.text_review, with its source under backend/maos_examples/ so the backend build context can include it. Ship that small package in the release image. Both API and worker activate the same version only when MAOS_EXTENSION_MODULES explicitly includes maos_examples.text_review; core never imports/registers it by default. Verify this exact packaged path, not an example that works only from a source checkout.

An unrelated second workflow must be defined in integration-test extension code and execute without changing core schemas, stage enums, runtime service or graph builder. This proves that the product was generalized rather than renamed.

## 6. Lifecycle, approval and execution guarantees

### FR-06 — Run lifecycle

Use these generic states; keep one canonical enum and transition policy.

| State | Meaning | Allowed next states |
| --- | --- | --- |
| CREATED | Validated run saved; no job submitted. | QUEUED, CANCELLED |
| QUEUED | Durable execution job is available. | RUNNING, CANCELLED |
| RUNNING | One current execution claim owns the run. | WAITING_APPROVAL, COMPLETED, FAILED, CANCELLED, INTERRUPTED |
| WAITING_APPROVAL | A durable pending approval gate exists. | APPROVED, REJECTED, CANCELLED |
| APPROVED | A valid human decision is recorded; execution remains paused. | QUEUED through explicit resume, CANCELLED |
| INTERRUPTED | Execution ownership was lost and the outcome needs recovery. | QUEUED through permitted explicit recovery, FAILED, CANCELLED |
| COMPLETED | All required nodes and final output validated and committed. | None |
| FAILED | Definitive execution failure. | None; create a new run for a fresh retry |
| REJECTED | Human rejected the pending gate. | None |
| CANCELLED | Cancellation has been committed. | None |

Multiple approval nodes are supported sequentially. Each has its own request and content identity. A successful run is COMPLETED only when the graph actually reaches its validated terminal output.

A caller may cancel CREATED/QUEUED/WAITING_APPROVAL/APPROVED/INTERRUPTED immediately. Cancelling RUNNING sets a durable cancellation request; the worker stops at a supported boundary. The API must distinguish cancellation accepted from cancellation completed.

Worker process loss is INTERRUPTED, not user cancellation. Late worker/provider results cannot overwrite CANCELLED, a newer state revision or a new execution claim.

### FR-07 — Durable submission and node commits

- Creating, starting and resuming runs must not execute the whole graph inside the HTTP request.
- Start/resume validate preconditions and atomically persist the new state plus one job; return 202 with the run identity.
- Claims use a transactionally guarded owner/generation or equivalent fencing token. Only the current claim may commit a node result.
- Each claim has an owner, fencing generation and lease expiry based on database time. The worker renews its lease in short transactions; initial heartbeat/lease defaults are 10/60 seconds. A reconciliation loop atomically marks expired owned work INTERRUPTED, records the event and invalidates the old generation. Completion, failure and cancellation writes validate current ownership. Tests may use shorter validated durations.
- Never hold a database transaction or row lock across an LLM/network call.
- Persist a node's validated output, state transition and associated events atomically.
- Persist failures in their own successful transaction even if the application operation reports an error.
- Completed committed nodes are not rerun during resume.
- Persist enough metadata to distinguish an unstarted node, an executing node, a committed node and an interrupted uncertain attempt.
- Bound worker concurrency; the initial default is one active run per worker.

LangGraph must be the authoritative orchestration path for real agent/tool execution. Do not retain a decorative graph beside a separate business loop.

The implementer may use a compatible PostgreSQL checkpoint adapter or application-owned node checkpoints, but must document the single state authority and transaction ownership. API-visible completion and checkpoint state must not contradict each other. Verify compatibility against the locked LangGraph version; do not rely on remembered APIs.

### FR-08 — Recovery and idempotency

A worker crash must not lose committed outputs. Expired execution ownership becomes INTERRUPTED with a persisted event. Queued jobs remain available after restart.

Recovery is explicit in this release:

- Pure or declared-idempotent interrupted tool nodes may be resumed under a new claim. Agent nodes may be replayed only through this explicit recovery path, with a new persisted attempt.
- Repeating an interrupted model request may consume additional model resources; disclose this behavior and retain the consumed attempt/call budget.
- A potentially non-idempotent external action with an unknown result is not resumable in this release. Return 409 unsafe_resume_requires_reconciliation. The operator may cancel the run, reconcile the external outcome independently and explicitly create a new run when appropriate. There is no public mark-node-completed repair operation. Do not advertise exactly-once side effects.
- Completed nodes, approved snapshots and prior decisions remain immutable.
- A missing/mismatched definition version blocks resume with a clear error.

Support Idempotency-Key for run creation, start and resume. Scope keys by authenticated principal and operation family. The fingerprint includes principal, HTTP method, canonical resource path including run ID, and canonical validated body; creation also includes the exact workflow version/hash and input. Reusing the same key with the same request returns the existing outcome. Within the same principal/operation family, a different resource or body returns 409. Persist the idempotency record atomically with the run/job mutation. Concurrent requests without a shared key still cannot create two active execution claims for one run.

Keep operation keys for the lifetime of the run for this release. Do not add an unrelated scheduled retention subsystem.

### FR-09 — Human approval

An approval is a real authorization boundary, not an agent-generated boolean.

- Bind it to run ID, node ID, workflow version/hash and the exact pending content/input through an immutable approval_content_revision and content_hash. These are separate from the mutable run state revision.
- Decision requests include the expected pending-content identity and current run revision for concurrency protection. Recording a decision or queuing a resume may increase the run revision without changing approved content. Resume verifies the stored approval identity/content, not equality with the pre-decision run revision.
- Record actor, decision, timestamp and optional comment.
- Only admin/operator can decide. Viewer and model output cannot.
- Reject stale or changed-content approvals.
- Enforce one final decision per approval request at the database level or with equivalent transactionally proven uniqueness.
- Approval does not automatically resume execution.
- A rejected approval cannot be overwritten or reused.
- A resume validates both the state and the persisted applicable approval.
- Expose approval history through the API and CLI.

Remove ordinary public endpoints for arbitrary state replacement or manual status transitions. A user must not bypass gates by PATCHing internal workflow JSON.

### FR-10 — Events and streaming

Every event contains a stable ID, run ID, monotonically increasing per-run sequence, timestamp, event type, safe actor/node metadata and a bounded payload.

Required event categories include run created/queued/started/completed/failed/cancelled/interrupted/resumed, node started/completed/failed, and approval requested/decided.

State and corresponding events commit together. Publish only committed event identities. Redis notification failure must not roll back a completed run or lose its durable history.

Provide cursor-based event retrieval and one authenticated streaming transport. Retaining WebSocket is preferred because it already exists. A stream consumer must recover from the last committed sequence, deduplicate repeated IDs and obtain all later committed events. Fix the backlog/subscription race with database catch-up, not a claim that Pub/Sub is durable.

The server must eventually check the database even when a notification is missed. Notification data should carry identifiers rather than raw prompts or full run input.

## 7. LLM provider behavior

### FR-11 — Real providers only in distribution

Preserve and generalize the existing Ollama, Groq, OpenRouter and Gemini adapters. Expose the existing OpenAI-compatible transport as a configurable adapter for a self-hosted OpenAI-compatible endpoint. This is a required bounded extension, not a claim that the baseline already exposes it.

Supported provider choices for this release: ollama, openai_compatible, groq, openrouter, gemini.

- Require an explicit model and applicable endpoint/credentials.
- No fake/mock provider enum or factory branch in release code.
- No LLM_RUNTIME_ENABLED switch that selects placeholder processing.
- No fake fallback.
- Disable automatic cross-provider fallback in the first release; switching provider is an operator action. Keep transient retries within the selected real provider.
- A missing key/model, unsupported provider, network failure, timeout, rate limit or malformed response produces an actionable error, never successful fixture output.
- Never fabricate token counts or prices. Unknown usage/cost remains null/unknown.
- Record actual provider/model, attempt count and provider-reported usage when available.
- Resolve and pin provider/model profile identity when creating the run. A later configuration change must not silently reroute an existing run to a different model/provider. Credentials may rotate without changing that identity; a missing matching profile blocks execution/resume clearly.

The default documented recipe is a real local Ollama endpoint with an operator-selected installed model. Do not hardcode a model as “latest,” guarantee it exists on the host or download model weights automatically.

For openai_compatible, document the exact HTTP/structured-output subset supported and the endpoint used in verification. Do not promise compatibility with every server merely because it uses that label.

### FR-12 — Validation, limits and errors

Validate structured output with the declared Pydantic schema before persisting a successful node. Invalid JSON and schema mismatch are failures. No fixture substitution or success after silently dropping required fields.

Starting defaults, overridable within documented bounded ranges:

| Limit | Initial default |
| --- | --- |
| Workflow nodes | 32 |
| Active runs per worker | 1 |
| Provider request timeout | 60 seconds |
| Transient retries per request | 2, with bounded exponential backoff and jitter |
| Total provider calls per run, including retries | 16 |
| Run external-input JSON | 64 KiB |
| Persisted output per node | 64 KiB |
| Total stored run input/context/output | 1 MiB |
| Event payload | 4 KiB |
| Event/list page size | 100, maximum 500 |

Validate configuration ranges and fail before exceeding limits. Do not mutate limits to make tests pass. A model-output token limit is explicitly configured for the selected provider; do not imply byte limits alone control inference cost.

Before dispatching each provider request, including retries/recovered attempts, transactionally reserve one call against the run's persisted budget under the current claim. An attempt with an unknown remote outcome still consumes its reservation. Restart/recovery must not reset call counts or consumed resources.

Transient retries apply to bounded timeout/unavailable/rate-limit categories. Configuration, authentication and schema errors are not repeatedly retried. Respect a bounded Retry-After when applicable.

Use cancellable async network I/O with explicit timeouts and connection cleanup. Cancelling the client request cannot guarantee the upstream model stops generating; the runtime must still reject stale results and stop scheduling later nodes.

Stable machine-readable error codes must cover configuration, authorization, invalid definitions/input/output, provider errors, invalid transitions, conflicts, stale approvals, interrupted execution and limits. Never include secrets or raw provider response bodies in user-visible errors.

## 8. API and CLI contracts

### FR-13 — REST and streaming API

Retain /api/v1 as the prefix for this breaking pre-1.0 release. Document the break; do not keep procurement routes as hidden compatibility shims.

| Method and target | Behavior |
| --- | --- |
| GET /live | Process liveness only. |
| GET /ready | Readiness for current schema, configuration and core storage; reports notification degradation accurately. |
| GET /health | Safe aggregate status with no infrastructure secrets. |
| GET /docs; GET /openapi.json | Generated API documentation/schema. |
| POST /api/v1/auth/login | Authenticate a real provisioned user. |
| POST /api/v1/auth/refresh | Rotate a valid refresh token. |
| POST /api/v1/auth/logout | Revoke the relevant refresh session. |
| GET /api/v1/auth/me | Identity and generic roles. |
| GET /api/v1/agents | List registered agent metadata without secrets. |
| GET /api/v1/workflows | List registered workflow definitions. |
| GET /api/v1/workflows/{workflow_id} | Current definition metadata and schema; version selection documented. |
| POST /api/v1/runs | Validate and create a CREATED run for an exact workflow version. |
| GET /api/v1/runs | Paginated summaries, filterable by status and workflow. |
| GET /api/v1/runs/{run_id} | Current state summary and final output. |
| GET /api/v1/runs/{run_id}/nodes | Bounded node execution records and validated outputs. |
| POST /api/v1/runs/{run_id}/start | Persist a job and return 202. |
| POST /api/v1/runs/{run_id}/cancel | Request/commit cancellation according to current state. |
| GET /api/v1/runs/{run_id}/approvals | Pending requests and decision history. |
| POST /api/v1/runs/{run_id}/approvals/{approval_id}/decision | Decide with expected content/state identity. |
| POST /api/v1/runs/{run_id}/resume | Resume approved work or permitted interrupted work; return 202. |
| GET /api/v1/runs/{run_id}/events?after_sequence=N&limit=100 | Durable ordered replay. |
| WS /api/v1/runs/{run_id}/stream?after_sequence=N | Authenticated committed-event stream. |

Map validation to 422, missing/invalid authentication to 401, denied role to 403, unknown resources to 404, state/idempotency/stale-approval conflicts to 409, and service configuration/dependency unavailability to 503. Asynchronous model execution failure is a persisted run outcome, not a retroactive HTTP response.

Use Authorization: Bearer for protected HTTP and WebSocket handshakes. Do not put bearer tokens into URLs. Remove previous query-token authentication.

### FR-14 — CLI

Canonical entry point: python -m app.cli. A short installed alias may be added but is not required for acceptance.

Required command groups:

| Command | Purpose |
| --- | --- |
| --help; --version | Discover available operations and version. |
| config init | Generate missing local secrets/configuration safely without overwriting an existing configuration. |
| doctor | Validate settings, database/schema and registered definitions; no model inference by default. |
| migrate | Apply the supported schema from the release image. |
| admin bootstrap | Create the explicitly requested first administrator. |
| admin create-user; admin set-role | Explicit local administration for the single instance. |
| auth login; auth logout | Authenticate and manage local session credentials. |
| workflow list; workflow show; workflow validate | Discover and validate definitions. |
| run create; run start; run show; run list | Operate on real runs. |
| run events --follow | Follow durable events; REST polling is acceptable if documented. |
| run approve; run reject; run resume; run cancel | Enforce the same transitions and RBAC as the API. |
| provider check | Explicit bounded real-provider probe. |

Ordinary run commands call the HTTP API so their behavior matches other clients. Local configuration, migration and privileged bootstrap commands may use application services directly. Do not build a second runtime into the CLI.

Use nonzero exit codes for failures and stable JSON output with --json. Human output goes to stdout; diagnostics go to stderr. Never print a success marker after a partially failed operation.

Passwords use a hidden prompt or stdin; no literal password command-line arguments in examples. If tokens are persisted, use an explicit user-owned file with restrictive permissions and no Git tracking. Login output must not casually print credentials into logs.

Provide an opt-in Compose cli service/profile using the same image, an entry point of python -m app.cli, the internal API URL and a dedicated .maos/cli directory mounted at /cli. Use the invoking operator's UID/GID recorded by config init. Store sessions at /cli/auth.json with mode 0600, and keep the host directory mode 0700. Separate login and run-command containers use the same file. Do not mount this credential directory into API or worker. The README must verify login followed by a separate authenticated CLI invocation.

## 9. Authentication and trust boundary

### FR-15 — Generic roles

This is one trusted self-hosted instance, not a multi-tenant SaaS.

| Capability | admin | operator | viewer |
| --- | --- | --- | --- |
| Read registered definitions, runs, outputs and events in the instance | Yes | Yes | Yes |
| Create/start/cancel runs | Yes | Yes | No |
| Approve/reject/resume | Yes | Yes | No |
| Bootstrap/create users/change roles through local admin CLI | Yes, host-authorized local administration | No | No |
| Change installed extension code or provider secrets | Host operator only | Host operator only | No |

Users with a read role can see instance run data; do not imply per-tenant or per-owner isolation. Remote user-management UI/API is not required.

Reuse Argon2 password hashing and JWT access tokens. Remove business roles such as Sales/Legal/Finance from the new public contract.

Implement stored hashed refresh-token/session records and rotation/revocation for the retained refresh/logout endpoints. Access tokens remain short-lived and may remain valid until expiry after logout; document that exact behavior instead of promising immediate global access-token revocation.

Do not create default admin accounts/passwords or public self-registration. Repeating bootstrap must never reset an existing user's credentials or silently grant roles.

### FR-16 — Secrets and sensitive data

- Generate non-default JWT/database secrets locally; never commit .env, auth token files or operator keys.
- No fixed example passwords in any runnable self-host configuration.
- API and worker run without root where practical; do not mount the Docker socket.
- Provider URLs and extensions are set by trusted host configuration, not untrusted run input.
- Logs contain IDs, status, duration, safe error categories and bounded metadata.
- Raw prompts, provider request/response bodies, credentials, authorization headers and hidden model reasoning are not application logs/events.
- Persist user input and validated outputs only as required for operation. Document that this instance stores them in PostgreSQL.
- Redact secrets in CLI errors, diagnostics and environment validation as well as web logs.
- Do not claim all data remains local when a remote model provider is selected.
- Do not add telemetry by default.

## 10. Self-host packaging and initialization

### FR-17 — Supported deployment

Primary support target: Docker Engine plus Docker Compose v2 on Linux. Document the exact tested versions and host in release evidence. Document Docker Desktop differences only where verified, especially host-to-container model connectivity. Do not claim an untested operating-system matrix.

The default API port binds to 127.0.0.1. PostgreSQL and Redis have no public host-port mappings. Public exposure requires an explicit operator configuration and documented TLS reverse-proxy setup.

Use named PostgreSQL volumes. A normal stop/restart/upgrade must preserve data. Avoid fixed container_name values so isolated Compose projects work.

The optional local-model profile requires explicit activation and explicit model installation. The core API/worker image does not contain model weights or need GPU access.

### FR-18 — One release image, complete commands

The release image must contain application code, dependencies, Alembic configuration/migrations, CLI, its configuration template and the opt-in maos_examples package. It excludes tests, fake providers, frontend code, academic assets, build caches and unrelated development Harness files.

Keep a dev/test build target for deterministic CI. Lock dependencies reproducibly. Remove Qdrant/MinIO/frontend packages and update the lockfile normally; do not hand-edit hashes.

Use one canonical docker-compose.yml plus a clearly scoped development/test override if needed. Delete or rewrite the old production-demo Compose file so it cannot become an alternate misleading installation path.

### FR-19 — Initialization contract

The rewritten README must supply commands that pass from a fresh clone. Build the image directly before invoking Compose, so required-secret interpolation cannot block secret generation. Target initialization on the supported Linux host:

~~~bash
git clone https://github.com/hzjanuary/multi-agent-system.git
cd multi-agent-system
mkdir -p .maos
chmod 700 .maos
docker build --target runtime -t multi-agent-os:local ./backend
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,source=$(pwd)/.maos,target=/config" \
  multi-agent-os:local \
  python -m app.cli config init --output /config/.env
~~~

Next, the operator edits .maos/.env to select the real provider, an already installed model, its reachable endpoint and the explicitly enabled maos_examples.text_review extension. Generated JWT/database secrets are already present. No model download or inference happens during initialization.

Then the documented target sequence is:

~~~bash
docker compose --env-file .maos/.env config --quiet
docker compose --env-file .maos/.env up -d --wait postgres redis
docker compose --env-file .maos/.env run --rm --no-deps api python -m app.cli migrate
docker compose --env-file .maos/.env run --rm --no-deps api python -m app.cli admin bootstrap
docker compose --env-file .maos/.env up -d api worker
docker compose --env-file .maos/.env exec api python -m app.cli doctor
docker compose --env-file .maos/.env --profile cli run --rm cli auth login
docker compose --env-file .maos/.env --profile cli run --rm cli workflow list
~~~

These are target commands until verified by the implementer. Required supporting behavior:

- .maos/ is Git-ignored and private. config init creates .env with mode 0600 and cli/ with mode 0700, populates only missing secrets, preserves existing nonempty values and writes atomically through the directory mount. It never logs secrets.
- The release image contains the default configuration template, cross-checked with .env.example. Configuration generation dispatches before full application settings validation and never imports/starts the API.
- Generated configuration includes COMPOSE_PROJECT_NAME=multi-agent-os-core and the invoking operator's UID/GID for the CLI profile.
- Compose uses image multi-agent-os:local with the matching backend runtime build target. It explicitly forwards configured runtime variables to API and worker: --env-file supplies interpolation values and is not assumed to inject every key automatically.
- Migration and bootstrap validate their applicable database/auth configuration but do not require a reachable model or make inference calls.
- .env.example remains the public reference template; .maos/.env is the canonical local installation file. A configuration-path override, if implemented, must be applied consistently to Compose, CLI and documentation.

Bootstrap prompts for the chosen email/password and creates only generic roles plus that requested account. No automatic seed service runs.

Application startup performs no model inference, paid network probe or model download. Missing provider configuration is exposed clearly through doctor/readiness and prevents agent run submission; it never selects a fake provider. Missing/unsafe authentication secrets fail startup.

Readiness checks current migration/schema and core storage. Notification degradation is identified separately. A reachable model is verified by the explicit provider check/live smoke, not a hidden paid health check.

The worker has its own health/heartbeat check. doctor reports whether a worker is available to consume jobs; API liveness alone does not prove execution is available.

Use docker compose config --quiet or equivalent for validation so interpolated secrets are not printed.

## 11. Data compatibility, history and migrations

### FR-20 — Clean-install-first breaking release

Old procurement databases are not silently convertible into the new generic contract.

- Preserve existing data, Git history, local .env files and volumes by default.
- Record the graduation baseline SHA and historical restore instructions.
- Use a new explicit Compose project/database/volume namespace for the new product.
- Before applying or stamping the new lineage, the migration wrapper rejects known legacy revisions, unknown revisions and a nonempty application schema without the expected revision marker. Only an empty supported schema or a recognized new-product predecessor may migrate. Refusal performs no schema or data write.
- Never fix an incompatible database by dropping tables, stamping a new revision over it or deleting volumes.
- Do not modify already-applied historical migrations in place and pretend they still describe the old database. If using a new migration lineage, state that it is only for a new database and retain historical lineage in Git history.
- The old release remains the way to inspect old procurement runs. Do not load them into the new service.
- Removing mock data means removing source data, automatic seeding and new-install defaults. It does not authorize deleting an operator's existing records.

No in-place legacy data migration is required. Normal future migrations within the new headless product must preserve new-product data and be tested.

### FR-21 — Backup and restore

Provide documented commands/scripts for backup and restoration of the new PostgreSQL database into a separate instance. Verify that completed outputs, waiting approvals, event order and auth state survive restore.

Do not include real backups in Git. Document where configuration/secrets are kept separately and what is needed to run the restored instance.

Recovery tests must use disposable named databases/volumes under a unique test Compose project. Never run docker compose down -v against an operator's default project.

## 12. README and open-source project files

### FR-22 — README rewrite

Rewrite the English README around the new user journey. Remove the defense-demo structure, old SPEC status scoreboard, UI instructions, seeded passwords, mock-provider quickstart and unsupported production claims.

Use an opening equivalent to:

> Multi-Agent OS is a headless, self-hosted runtime for building and running typed multi-agent workflows. It combines real model-provider integrations, durable run state, human approval, and an API/CLI interface.

The final README must include, in this order or an equally usable order:

1. What the product is and its current maturity.
2. Implemented capabilities and explicit limitations.
3. Compact architecture showing API, worker, PostgreSQL, Redis and configured model.
4. Prerequisites and tested deployment environment.
5. Complete first-run quickstart with secure configuration and real admin bootstrap.
6. Real local-model setup; supported remote-provider configuration.
7. One opt-in example with user input, real execution, approval and explicit resume.
8. API/CLI discovery, authentication, events and stable errors.
9. Configuration reference with defaults, required values and secret handling.
10. Persistence, restart/recovery, backup/restore and upgrade instructions.
11. How to define another agent, deterministic tool and workflow.
12. Development, tests, CI and real-provider smoke instructions.
13. Legacy graduation migration boundary.
14. Contribution/security/license links.
15. A short provenance acknowledgment of the university graduation project.

Every runnable command must be verified against the final release image or clearly labeled as an optional/manual deployment example. Replace screenshots and fictional output with actual sanitized evidence or compact schema examples.

Do not describe fixture-based CI as real model inference. Distinguish contract-tested adapters from adapters actually verified live in the release.

### FR-23 — Required repository documentation

| Deliverable | Purpose |
| --- | --- |
| README.md | Public onboarding and honest capability statement. |
| backend/README.md | Short developer/service guide or pointer; no contradictory second quickstart. |
| LICENSE | Selected MIT text for appropriately owned project material, subject to notice review. |
| CONTRIBUTING.md | Setup, tests, extension workflow and contribution expectations. |
| SECURITY.md | Honest supported scope and an existing, verified reporting channel; no invented email. |
| CHANGELOG.md | Breaking headless extraction and removal list. |
| .env.example | Complete placeholders/defaults with no real secrets or demo credentials. |
| docs/architecture.md | Runtime, state authority, jobs, approvals, events and trust boundary. |
| docs/self-hosting.md | First installation, model connectivity, operations and TLS exposure. |
| docs/configuration.md | Environment/config reference generated from or cross-checked with code. |
| docs/providers.md | Configuration, error behavior and tested compatibility matrix. |
| docs/extending.md | Typed agent/tool/workflow registration and example. |
| docs/api.md | API/CLI overview with links to generated OpenAPI. |
| docs/migration.md | Legacy isolation, breaking contracts, backup and restore. |
| docs/release/verification.md | Acceptance matrix with concrete evidence and unresolved gates. |
| AGENTS.md and docs/WORKFLOW.md | Concise current product boundaries and actual verification commands. |
| docs/plans/active/spec-029-headless-oss.md | One resumable implementation plan; archive only after its criteria are honestly assessed. |

Root SPEC.md should become a short pointer to the current specification or a concise current product contract. Remove conflicting active .ai product contracts or replace them with explicit pointers. Rename/reconcile existing uppercase/lowercase architecture and documentation files and update all active links so there is one current authority. Do not leave the deleted web/RAG architecture marked immutable.

MIT is a proposed product decision, not evidence that the baseline is already licensed. The accompanying goal selects MIT if the maintainer uses it unchanged. Before adding the root license, review any retained third-party/template code and preserve required notices; do not invent ownership. If rights are uncertain, finish independent engineering and leave a concrete license/publication gate for the maintainer. Do not publish the release in this task.

## 13. Verification and acceptance

### 13.1 Test strategy

Use deterministic fixtures only in test code and the dev/test image. That is compatible with removing runtime mocks. Test providers must be injected through interfaces; no environment setting can activate them in a release image.

Preserve or rewrite tests for retained invariants. Delete tests only when their feature was deliberately removed and note that mapping. Do not obtain green CI by globally skipping old tests, weakening assertions or lowering thresholds without a behavior-based explanation.

Use real PostgreSQL/Redis for integration tests that claim persistence, locking, transaction, event or recovery behavior. An in-memory fake database cannot prove those guarantees.

Run a separate explicitly enabled real-provider smoke. Do not call paid providers in default CI or automatically download a model. Prefer an already configured local provider. A remote smoke requires explicit operator enablement and a bounded call/token budget.

### 13.2 Acceptance matrix

All evidence must name the checked commit and the command/test that produced it. Existing README claims and historical test counts are not evidence for this release.

| ID | Required outcome | Verification |
| --- | --- | --- |
| AC-01 | Backend builds, migrates and starts without frontend/Node/Qdrant/MinIO. | Clean release-image build and isolated Compose bootstrap. |
| AC-02 | No demo accounts, business records, run results or synthetic activity on fresh install. | Real database assertions before and after explicit admin bootstrap. |
| AC-03 | Admin bootstrap creates the requested account and never silently resets/re-grants on repetition. | CLI integration tests with an empty and existing instance. |
| AC-04 | Fake/placeholder providers cannot be selected in the release image. | Negative configuration tests and release-package import/content inspection. |
| AC-05 | No retained core import depends on removed demo/RAG/pricing modules. | Import/build tests and bounded removal-reference inventory. |
| AC-06 | Two unrelated workflows execute without core modifications. | Registered extension integration tests using distinct input/output schemas. |
| AC-07 | Real LLM and deterministic tool steps use one orchestration path. | Runtime integration plus graph execution evidence. |
| AC-08 | At least two real agent invocations consume real user input and chained output. | Explicit live-provider text_review smoke with actual provider/model metadata. |
| AC-09 | Missing configuration or provider failure cannot become fake success. | Negative tests for missing model/key, rejected auth, timeout and exhausted retries. |
| AC-10 | Invalid structured output fails and later nodes do not execute. | Parser/schema integration tests with persisted failure read from a new DB session. |
| AC-11 | Start/resume submission survives client disconnect and API restart. | Durable job integration test with independent worker process. |
| AC-12 | Committed node outputs survive worker restart and are not recomputed. | Controlled worker termination/restart with real PostgreSQL. |
| AC-13 | Interrupted unsafe actions are not automatically retried. | Fault-injected test tool with observable side-effect boundary. |
| AC-14 | Concurrent starts/resumes cannot create duplicate active execution. | Real database concurrent-request/claim tests. |
| AC-15 | Idempotency-key replay is stable; changed body or target resource conflicts within the same operation family. | API concurrency/replay tests and atomic record/job persistence. |
| AC-16 | Approval survives restart and only authorized, current-content decisions apply. | API/CLI role, restart and stale-revision tests. |
| AC-17 | Two conflicting approval requests cannot both finalize. | Concurrent decision test with a unique committed outcome. |
| AC-18 | Approval does not run downstream nodes until explicit resume. | Paused workflow inspection and worker execution counters. |
| AC-19 | Cancellation persists and late results cannot overwrite terminal state. | In-flight cancellation and stale-claim tests. |
| AC-20 | Failure state/events remain after the failing transaction/session ends. | Provider failure observed from a separate new DB session. |
| AC-21 | Events describe committed state and reconnect replay has no missing committed entries. | Rollback, disconnect/catch-up and missed-notification tests. |
| AC-22 | Redis loss degrades notification but not durable results or replay. | Integration test with stopped Redis and working DB event retrieval. |
| AC-23 | RBAC protects every control/detail surface and no public state-patch bypass remains. | API/WS authorization tests plus OpenAPI route inspection. |
| AC-24 | Limits are enforced and secrets do not leak through logs/events/errors/CLI. | Boundary, redaction and malformed-input tests. |
| AC-25 | Readiness detects missing/current schema and invalid run configuration correctly. | Fresh/unmigrated/unavailable dependency tests; no hidden model calls. |
| AC-26 | Release image includes CLI/migrations and excludes tests/fake/demo/UI code. | Image-level command and content verification. |
| AC-27 | Legacy/unknown/nonempty-unmarked databases are refused without modification; old volumes remain untouched. | Disposable legacy and unknown-schema fixtures with migration refusal tests. |
| AC-28 | Backup restores outputs, events and pending approvals into a separate instance. | Documented restore rehearsal with a paused run. |
| AC-29 | README quickstart works from a clean clone and exact release image, including persistent login across CLI invocations. | Independent clean-install walkthrough using documented commands. |
| AC-30 | Unit/integration tests, Ruff, formatting, MyPy, lockfile and Compose checks pass. | Rewritten backend-only CI and local gates. |
| AC-31 | Relevant dependency/security findings and committed-secret checks are resolved or honestly recorded. | Current dependency audit/secret scan with justified scope and results. |
| AC-32 | Docs/links/AGENTS reflect the new product and license/notice review is complete. | Documentation review and release checklist. |

Do not invent a fixed required number of tests or require arbitrary coverage inflation. Require proof of these behaviors.

### 13.3 Evidence states

Use PASS, FAIL, BLOCKED and NOT_RUN for each acceptance item. A skipped live test is not PASS.

Engineering complete requires all applicable non-live engineering gates to pass and every remaining blocker to be explicit. Fully verified release readiness additionally requires real-provider execution, clean-install/restore evidence and the license gate.

If the environment lacks Docker, a real model, credentials or another required capability, complete all independent work and report the exact affected criteria, attempted checks and the smallest next action. Do not claim “production-ready,” “complete self-host verification” or all criteria passed.

Do not widen testing indefinitely after the listed risks and gates are covered. Stop optional testing once relevant verification is sufficient.

## 14. Implementation milestones

Maintain one plan with checked tasks, decisions, current failures and next steps. Small coherent local commits are encouraged. A milestone is complete when its behavior and proof are complete, not when its prose is written.

| Phase | Work | Exit condition |
| --- | --- | --- |
| M0 — Baseline and inventory | Inspect status/HEAD/instructions, map imports and feature removals, record existing failures, identify legacy schema and license material, establish new product authority. | Bounded keep/remove/generalize manifest and executable verification plan. |
| M1 — Generic contracts | Introduce agent/tool/workflow registry, generic state, versions, errors and one real execution path. | Two unrelated definitions work without fixed business-stage changes. |
| M2 — Durable execution | Add jobs/claims, per-node commits, generic approvals, cancellation, recovery and durable event cursors. | Persistence/race/restart/approval tests pass with actual PostgreSQL. |
| M3 — Product extraction | Remove UI/demo/RAG/pricing/outbound/Telegram surfaces, fake production paths and obsolete harness/template coupling. | Release imports and dependency graph have no removed-feature dependency. |
| M4 — Operator experience | Implement CLI, clean bootstrap, release migrations, Compose, validated provider config and operational docs. | Isolated fresh install and actual release-image commands work. |
| M5 — OSS documentation and CI | Rewrite README/docs/AGENTS, add selected license/notices/contributor files, replace legacy gates and scripts. | Documentation is consistent and backend-only CI exercises the shipped product. |
| M6 — End-to-end verification | Run remaining acceptance matrix, real local/approved remote smoke, clean-clone walkthrough and backup/restore. | Evidence-based final status, known limits, and concrete blocked steps if any. |

M1–M4 may overlap where dependencies permit, but define generic replacements before deleting modules they still import. Do not delete the frontend first and declare the refactor done.

Independent agents may review runtime, packaging and documentation in parallel. Do not assign overlapping file ownership without coordination. Preserve the maintainer's selected Codex model/effort; no special model switch is required by this spec.

## 15. Delivery and completion boundaries

Deliver:

1. The implemented source refactor on a separate local feature branch.
2. A rewritten README and coherent operator/developer documentation.
3. A complete release image/Compose/CLI path.
4. Relevant deterministic tests and executable real-provider smoke.
5. The filled acceptance evidence matrix.
6. A concise Vietnamese final report: what changed, exact validation, how to run it, breaking changes and unresolved items.

Authorized by the supplied implementation goal: local repository edits, explicit listed removals, local branches/commits, isolated test resources, dependency updates necessary for the retained product, and preparing the selected license/documents.

Not authorized by this spec alone: deleting existing user data/volumes, history rewriting, pushing or merging remotely, publishing releases/packages/images, changing repository settings, remote deployment, sending messages or paid external model calls without the specified operator enablement/budget.

Routine in-scope engineering decisions and milestones do not require repeated confirmation. Ask only for a concrete missing product decision, unresolved rights/ownership, inaccessible external capability or destructive action that cannot be safely avoided. Continue independent work before surfacing the final blocker.

## 16. Source references

All repository links below refer to the reviewed immutable baseline; future implementation must recheck current HEAD.

- [Baseline commit](https://github.com/hzjanuary/multi-agent-system/commit/92e5f1cfb2b0144bdb39a48db99371974bd372a5)
- [README](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/README.md)
- [Old product contract](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/.ai/project/PROJECT_CONTRACT.md)
- [AGENTS](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/AGENTS.md)
- [Current repository workflow](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/docs/WORKFLOW.md)
- [Dependency manifest](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/pyproject.toml)
- [Workflow schemas](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/workflows/schemas.py)
- [Runtime schemas](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/runtime/schemas.py)
- [Graph implementation](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/runtime/graph.py)
- [Default placeholder nodes](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/runtime/nodes.py)
- [Runtime service](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/runtime/service.py)
- [LLM runtime adapter](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/runtime/llm_adapter.py)
- [LLM factory](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/llm/factory.py)
- [Knowledge retrieval](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/knowledge/retrieval.py)
- [Fake embedding implementation](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/knowledge/embeddings.py)
- [Event service](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/workflows/events.py)
- [Workflow API](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/api/v1/workflows.py)
- [Readiness](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/app/core/readiness.py)
- [Dockerfile](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/backend/Dockerfile)
- [Compose](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/docker-compose.yml)
- [Environment validator](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/scripts/ops/validate_environment.py)
- [CI](https://github.com/hzjanuary/multi-agent-system/blob/92e5f1cfb2b0144bdb39a48db99371974bd372a5/.github/workflows/ci.yml)
- [Official Codex Goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
