# SPEC-015 - Final Evaluation, Demo Validation, and Graduation Report Assets

## Status

Draft

## Context

Enterprise Multi-Agent OS now has a complete graduation-demo product path:

- SPEC-001 through SPEC-004 established the backend, database, auth/RBAC,
  Redis, Qdrant, and MinIO foundations.
- SPEC-005 through SPEC-008 established workflow state, deterministic
  LangGraph runtime execution, workflow APIs, persisted events, and WebSocket
  streaming.
- SPEC-009 established the Next.js workflow dashboard.
- SPEC-010 established deterministic local-demo seed data and runbooks.
- SPEC-011 added provider-independent LLM contracts with no-key fake defaults.
- SPEC-012 added human approval and explicit post-approval resume.
- SPEC-013 added the RAG/document knowledge base, demo ingestion, retrieval
  APIs, runtime grounding behind `RAG_ENABLED=false`, and frontend evidence
  surfaces.
- SPEC-014 added production-demo environment templates, Docker Compose
  packaging, readiness, structured observability, CI gates, smoke scripts, and
  deployment runbooks.

SPEC-015 plans the final graduation-readiness layer. It should not add major
product behavior. It should package existing implementation evidence into a
defensible final evaluation, reproducible demo validation, report-ready
technical assets, diagrams, screenshot checklists, final demo script, and
defense preparation material.

## Product Goal

- Turn the completed product into a defensible graduation project package.
- Prove the system works end to end through repeatable validation.
- Produce clear evidence for:
  - architecture quality
  - multi-agent workflow orchestration
  - human approval and resume lifecycle
  - RAG evidence grounding
  - frontend usability
  - production-demo deployability
  - CI and quality gates
- Prepare report and demo assets without adding new major product features.

## Non-goals

- New backend product features.
- New frontend product features, except tiny polish explicitly scoped by later
  SPEC-015 tasks.
- Admin operations or approval-policy builder.
- Enterprise SSO.
- Production email sending.
- Production secret vault.
- Cloud deployment automation.
- Terraform or Kubernetes.
- Upload UI or admin document-management UI.
- Token streaming or agent-thought streaming.
- Global response envelope rollout.
- Real secrets or provider keys.
- Paid/live LLM provider requirements for final evaluation.
- Final report chapters, slides, screenshots, diagrams, or evaluation scripts
  during this planning task.

## Final Evaluation Strategy

The graduation project is considered done when the repository can demonstrate,
document, and defend the implemented MVP across these dimensions:

| Dimension | Evidence source |
| --- | --- |
| Functional completeness | Existing SPEC-001 through SPEC-014 tasks, runbooks, and final demo checklist |
| Backend API correctness | Backend pytest suite, OpenAPI route list, workflow/approval/knowledge API tests |
| Workflow orchestration correctness | Runtime tests, workflow status lifecycle tests, persisted event timelines |
| Approval/resume correctness | Approval service/API/frontend tests and demo walkthrough |
| RAG grounding correctness | Knowledge ingestion/retrieval/runtime/frontend tests and RAG demo evidence |
| Frontend usability | Frontend component tests, build output, screenshot checklist, manual smoke flow |
| Deployment readiness | Production Compose config, image build, smoke script, readiness checks |
| Observability/readiness | `/health`, `/live`, `/ready`, metrics endpoint, structured log/redaction tests |
| Test coverage and CI gates | GitHub Actions workflow and `scripts/ci/all-gates.sh` evidence |
| Security/safety boundaries | No-secret scans, RBAC tests, redaction tests, documented non-goals |

Existing automated tests and gate scripts are the primary evidence. SPEC-015
tasks may add bounded evaluation reports, command-capture templates, manual
checklists, and report assets, but should not widen the product surface.

Default evaluation mode remains deterministic and no-key:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

Optional RAG evidence mode may set:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
```

No final evaluation task should require remote LLM keys or external provider
network access.

## End-to-End Demo Validation

SPEC-015 should define a repeatable end-to-end scenario that can be followed
against local development or the SPEC-014 production-demo stack:

1. Start the local or production-demo stack.
2. Run migrations explicitly.
3. Seed deterministic demo users/workflows.
4. Ingest deterministic knowledge documents when RAG evidence will be shown.
5. Login as Manager or Admin.
6. Open workflow dashboard and workflow detail.
7. Run the procurement workflow to `WAITING_APPROVAL`.
8. Inspect persisted and live timeline events.
9. Inspect RAG evidence/citations if enabled.
10. Submit approval.
11. Resume workflow explicitly.
12. Verify `COMPLETED` status.
13. Verify approval/resume events, audit evidence where exposed, and bounded
    citation evidence.
14. Optionally verify Viewer or non-approval-role forbidden behavior.
15. Optionally verify `/ready` and Admin/Manager metrics visibility.

Expected validation outputs:

- command summary for Compose config and service startup
- migration result
- demo seed JSON or summary
- knowledge ingestion dry-run or confirmed summary
- workflow id and status progression
- event timeline evidence
- approval decision evidence
- resume result evidence
- RAG citation evidence when enabled
- frontend route/screenshot checklist result
- metrics/readiness evidence when included

## Evidence Capture Plan

Later SPEC-015 tasks should create a final evidence report such as:

```text
docs/final/EVALUATION_REPORT.md
```

The report should collect bounded, reproducible evidence:

- validation command outputs or summarized results
- CI/local gate summary
- backend test and frontend test counts
- Compose config and production image build evidence
- smoke check result
- demo seed and knowledge ingestion summaries
- workflow lifecycle status table
- approval/resume history summary
- RAG citation examples with bounded excerpts
- observability/readiness/metrics checks
- screenshot checklist completion table
- known limitations and deferred scope

The report must not store:

- real secrets
- real customer data
- API keys or tokens
- raw provider payloads
- raw prompts
- raw embeddings or vector payloads
- chain-of-thought or hidden reasoning
- unbounded documents or logs

## Graduation Report Asset Plan

SPEC-015 should plan report-ready markdown assets under a bounded location such
as:

```text
docs/final/
docs/report/
```

Planned report content:

- abstract and project overview
- business problem and motivation
- goals, scope, and non-goals
- requirements mapped to implemented specs
- system architecture
- technology stack rationale
- backend design
- workflow orchestration design
- human approval/resume design
- RAG knowledge-base design
- frontend design
- deployment and observability design
- implementation phase summary
- evaluation methodology and results
- security and safety boundaries
- limitations
- future work
- setup/demo appendix

Documentation convention remains English. This planning task does not generate
the final thesis/report body.

## Architecture Diagrams Inventory

Later tasks should create text-based diagram sources, preferably Mermaid inside
markdown, so diagrams remain reviewable and versionable.

Planned diagrams:

- system context diagram
- container/deployment diagram
- backend layered architecture diagram
- database/domain model overview
- LangGraph workflow diagram
- workflow lifecycle/status diagram
- human approval/resume lifecycle diagram
- RAG ingestion and retrieval diagram
- event streaming flow diagram
- frontend component/API integration diagram
- CI and production-demo deployment flow diagram

Diagrams should explain architecture and evaluation evidence. They should not
invent unimplemented infrastructure such as Kubernetes, Terraform, external
telemetry vendors, secret vaults, enterprise SSO, or production email sending.

## Screenshots And Demo Media Checklist

Later tasks should define and optionally capture screenshots for final report
and presentation use.

Planned screenshots:

- login page
- authenticated dashboard
- workflow list with seeded RFQ-001 examples
- workflow detail before run
- run result at `WAITING_APPROVAL`
- event timeline/backlog
- approval panel
- approval history
- evidence/citations panel
- knowledge search and document catalog
- resume action
- completed workflow and final timeline
- RBAC forbidden state
- `/ready` or metrics evidence where appropriate
- CI/local gate command evidence if useful
- production-demo smoke result if useful

Screenshots must avoid showing secrets, tokens, local env files, real provider
keys, private customer data, raw prompts, raw provider payloads, raw embeddings,
or chain-of-thought.

## Final Demo Script

The final demo script should target an 8-12 minute presentation with a 3-5
minute fallback summary.

Planned flow:

1. One-sentence product pitch.
2. Business problem: procurement workflow coordination, traceability, and
   evidence.
3. Architecture overview: Next.js, FastAPI, LangGraph, Postgres, Redis,
   Qdrant, MinIO, LLM abstraction.
4. Live demo setup: no-key deterministic mode and optional RAG mode.
5. Login as Manager/Admin.
6. Show workflow dashboard and seeded procurement workflows.
7. Run workflow to `WAITING_APPROVAL`.
8. Explain multi-stage orchestration and deterministic calculation boundary.
9. Show timeline events and observability.
10. Show RAG evidence/citations when enabled.
11. Approve and resume explicitly.
12. Show `COMPLETED` status and final timeline.
13. Explain safety: RBAC, audit/event history, no automatic email sending,
    no real secrets.
14. Explain deployment readiness: production Compose, readiness, metrics,
    CI gates.
15. Closing value proposition and limitations.

Commands and route references should align with existing demo and deployment
runbooks.

## Defense And Q&A Preparation

Later tasks should create a Q&A bank covering:

- why a multi-agent workflow architecture instead of a chatbot
- why LangGraph for state-driven orchestration
- why FastAPI and Next.js
- why Postgres, Redis, Qdrant, and MinIO
- deterministic demo versus real LLM mode
- provider abstraction and fake provider rationale
- why LLMs do not perform arithmetic
- human approval/resume lifecycle
- RBAC and auditability
- RAG benefits and limitations
- evidence/citation reliability boundaries
- deployment limitations
- observability choices
- testing strategy
- security and no-secret handling
- known limitations and future work

This planning task does not generate the full Q&A bank.

## Repository Release Checklist

SPEC-015 should include a final repository release checklist:

- root README has clear entry points
- backend/frontend/deployment/demo docs are cross-linked
- SPEC index reflects SPEC-015
- environment examples contain placeholders only
- no real secrets or real-looking provider keys are committed
- no local `.env` files are tracked
- CI status is visible or reproducible locally
- `scripts/ci/all-gates.sh` passes
- production Compose config passes
- production app images build
- smoke script help and default checks work
- demo seed and knowledge ingestion dry-runs work
- known limitations are documented honestly
- license/academic attribution is present if required

Final no-secret scan should include docs, env examples, tests, scripts, Compose
files, backend, and frontend sources while excluding generated dependency and
build folders.

## Testing And Evaluation Strategy

Final validation should be reproducible with existing scripts and commands:

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
bash scripts/ci/all-gates.sh
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend
bash scripts/deployment/smoke-prod-demo.sh --help
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo --dry-run --json
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

Optional manual validation:

- start the production-demo stack
- run migrations
- run demo seed
- run knowledge ingestion
- run smoke checks
- perform the full frontend walkthrough
- capture report screenshots

No automated evaluation should require real provider keys, live external LLM
providers, paid services, or cloud credentials.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Final assets claim unimplemented capabilities | Add explicit limitation and non-goal review in each asset task |
| Screenshot/evidence capture leaks secrets | Use no-key demo mode and add no-secret scan checklist |
| Demo validation becomes non-reproducible | Anchor commands to existing scripts and deterministic seed/ingestion |
| RAG evidence depends on unseeded Qdrant data | Include explicit knowledge ingestion prerequisite and dry-run/confirmed evidence |
| Real LLM mode introduces variable output | Keep final evaluation no-key by default and document real-provider mode as optional |
| Report assets drift from current architecture | Base diagrams and narrative on SPEC-001 through SPEC-014 plus current runbooks |
| Final polish accidentally adds product features | Keep SPEC-015 tasks docs/evidence-focused with tiny polish only when scoped |

## Suggested Task Breakdown

- TASK 015.1 - Final Evaluation Matrix and Acceptance Evidence Plan
- TASK 015.2 - End-to-End Demo Validation Script and Checklist
- TASK 015.3 - Graduation Report Structure and Technical Narrative Assets
- TASK 015.4 - Architecture Diagrams and Screenshot Checklist
- TASK 015.5 - Final Demo Script and Defense Q&A Bank
- TASK 015.6 - Repository Release Polish and Final Quality Gate
- TASK 015.7 - Final Project Closeout Review

## Acceptance Criteria

- Final evaluation scope is clearly defined.
- End-to-end demo validation strategy is repeatable.
- Evidence capture plan is bounded and safe.
- Graduation report asset plan is defined without generating final report
  content in planning.
- Architecture diagram inventory is defined.
- Screenshot and demo media checklist is defined.
- Final demo script and Q&A preparation scope are defined.
- Repository release checklist is defined.
- Testing strategy preserves no-key deterministic behavior.
- Planning does not require real LLM keys or external provider keys.
- Planning does not add real secrets.
- Planning does not implement final assets yet.
- Planning does not modify backend, frontend, runtime, workflow API,
  knowledge API, deployment behavior, migrations, or database models.
- Planning does not add cloud resources.

