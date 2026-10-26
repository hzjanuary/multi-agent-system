# SPEC-029 headless OSS implementation

Date: 2026-10-26

## Status

Active. Branch `feat/spec-029-headless-oss`; baseline HEAD
`92e5f1cfb2b0144bdb39a48db99371974bd372a5`. Supplied untracked
`GOAL-029.txt` and `docs/specs/SPEC-029-headless-oss-selfhost.md` preserved.

## Outcome and authority

Implement the full headless, self-hosted product in SPEC-029, which the supplied
goal activates and authorizes, including MIT for maintainer-owned material.
Security/data protection remain required. No remote publishing, paid inference,
existing data deletion or history rewriting is authorized.

## Approach and ownership

- Root: API/CLI/bootstrap, product extraction inventory/removals, documentation,
  integration and acceptance audit.
- definitions_llm: typed registry, real provider service, opt-in text_review.
- runtime: generic persistence, jobs/leases/checkpoints/approvals/events, migrations.
- packaging: settings, image/Compose, backend-only CI and dependency lock.

## Inventory / removal map

- Retain/generalize Python FastAPI/LangGraph, PostgreSQL, Redis, real model
  transports, auth/roles/session rotation and sanitized errors.
- Replace procurement workflows/runtime/approval models with generic definitions
  and durable execution. Preserve relevant security tests by rewriting them for
  the new contracts; remove tests only for explicitly retired features.
- Remove frontend/datasets/demo/knowledge/vectorstore/storage/price_research/
  outbound, Telegram/demo/evaluation scripts and their exclusive tests.
- Inventory `.harness-*`, `.ai`, `.agents`, `.codex`, scripts/schema and old docs
  before removing active-distribution scaffold; Git baseline preserves history.
- License/third-party provenance inspection pending; no publication in scope.

## Risks and recovery

Use a new product schema and separately named Compose volumes. Refuse legacy,
unknown or unmarked nonempty databases before migrations. Never delete operator
data/volumes. Git branch and coherent local commits preserve source recovery.
External model calls require an explicitly configured local endpoint or approved
remote budget. Missing external capability is an explicit acceptance blocker.

## Progress

- [x] Read goal, spec, AGENTS and WORKFLOW; baseline and clean tracked tree checked.
- [x] Create local feature branch and establish policy authority.
- [ ] M0 import/scaffold/license inventory and baseline executable observations.
- [ ] M1 generic contracts and two unrelated workflow proof.
- [ ] M2 durable execution, recovery, approvals and PostgreSQL proof.
- [ ] M3 product extraction and removed-import proof.
- [ ] M4 CLI/bootstrap/image/Compose and isolated install proof.
- [ ] M5 English docs/license/backend CI.
- [ ] M6 full acceptance matrix, live model, clean install and restore rehearsal.

## Validation

Run unit/schema/provider fixtures first; then actual isolated PostgreSQL/Redis
integration, release image inspection and documented CLI walkthrough. Ruff,
formatting, strict MyPy, lock and Compose checks remain gates. Record exact
commands/results and checked source revision in docs/release/verification.md.
Each AC-01–AC-32 remains unproven until direct evidence is inspected.

## Decisions

- 2026-10-26: Use code-first installed Python extensions and application-owned
  node checkpoints; LangGraph executes the registered sequential graph.
- 2026-10-26: No intake/trace control-plane writes: current workflow and explicit
  goal authorize direct implementation.

## Result

Implementation in progress; engineering completion and release readiness not claimed.

## Resumed verification observations

- The original goal turn made implementation progress: registry, real adapters,
  generic leased runtime, schema guard, API/CLI/auth rotation, headless packaging
  and English docs now exist; listed retired source/doc surfaces removed only
  after import/CI inventory. Existing operator containers/volumes remain untouched.
- 2026-10-26: Root focused auth/RBAC/health/bootstrap/config suite: 43 passed;
  production provider-parser/graph/PostgreSQL composition plus worker-availability
  and middleware checks: 10 passed; separate CLI suite: 8 passed. These are
  deterministic fixtures and real DB tests, not live inference.
- 2026-10-26: Dependency audit remediation upgraded LangGraph and its checkpoint/
  SDK packages plus vulnerable compatible dependencies. Exported locked main
  dependency audit reports zero known vulnerabilities. Final source gates pending.
- 2026-10-26: Maintainer explicitly selected leaving AC-08 BLOCKED. No configured
  installed local model exists; no live/remote calls or model downloads are run.
- Added missing FR-19 worker availability: singleton database-time presence
  heartbeat, private worker health marker and nonzero doctor status if unavailable.
- Runtime agent runs real separate-database pg_dump/pg_restore proof; packaging
  agent prepares final image/clean install/independent API restart/stopped-Redis
  verification. Final-image identity and complete acceptance matrix still pending.
