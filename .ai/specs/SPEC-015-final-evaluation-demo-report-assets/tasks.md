# SPEC-015 Tasks - Final Evaluation, Demo Validation, and Graduation Report Assets

## Task List

### TASK 015.1 - Final Evaluation Matrix and Acceptance Evidence Plan

Goal: Define the final project evaluation matrix and evidence capture plan
without running full validation or creating final report chapters.

Scope:

- Create a final evaluation matrix under `docs/final/` or equivalent.
- Map product goals, user stories, and SPEC-001 through SPEC-014 capabilities
  to concrete evidence.
- Define acceptance evidence for backend APIs, runtime orchestration,
  approval/resume, RAG grounding, frontend UX, deployment readiness,
  observability, CI gates, and safety boundaries.
- Define how command output summaries should be captured without secrets.
- Add known limitations and deferred scope categories.
- Update README links only if appropriate.

Acceptance criteria:

- Evaluation matrix exists and is traceable to implemented specs.
- Evidence requirements are bounded and reproducible.
- No real provider keys, real secrets, raw prompts, provider payloads,
  embeddings, or chain-of-thought are requested.
- No backend/frontend/runtime behavior, migrations, models, tests, CI, or
  deployment automation are changed.

Validation:

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
git diff --check
```

### TASK 015.2 - End-to-End Demo Validation Script and Checklist

Goal: Add a final E2E demo validation checklist and, if bounded, a non-invasive
script wrapper that records expected commands and manual checkpoints.

Scope:

- Define a repeatable final demo validation checklist.
- Cover production-demo/local stack startup, migrations, demo seed, knowledge
  ingestion, frontend login, workflow run to `WAITING_APPROVAL`, RAG evidence,
  approval, resume, `COMPLETED`, RBAC, readiness, and metrics checks.
- If a script is added, keep it non-mutating by default and require explicit
  confirmation before any seed/ingestion/write path.
- Use existing endpoints and scripts only.
- Do not implement browser automation unless explicitly scoped and bounded.

Acceptance criteria:

- Checklist covers the full graduation demo path.
- Commands align with existing runbooks and scripts.
- Default validation remains no-key and deterministic.
- Script, if added, does not deploy, push images, call real LLM providers,
  mutate data by default, or print secrets.
- No app behavior, API contracts, migrations, models, or frontend features are
  changed.

Validation:

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
bash scripts/deployment/smoke-prod-demo.sh --help
git diff --check
```

### TASK 015.3 - Graduation Report Structure and Technical Narrative Assets

Goal: Create report-ready markdown structure and technical narrative drafts for
the graduation submission without producing a final polished thesis document.

Scope:

- Add report outline files under `docs/final/` or `docs/report/`.
- Draft concise sections for abstract, problem statement, goals/scope,
  architecture, implementation phases, evaluation method, limitations, future
  work, and setup/demo appendix.
- Link to existing SPEC, demo, deployment, LLM, and decision docs.
- Keep claims aligned with implemented behavior and documented limitations.
- Do not invent cloud deployment, upload UI, production OCR, secret vault,
  enterprise SSO, production email, or token streaming.

Acceptance criteria:

- Report structure is complete enough for final writing.
- Technical narrative accurately reflects SPEC-001 through SPEC-014.
- Limitations and future work are explicit.
- Docs contain no real secrets, provider keys, tokens, raw prompts, provider
  payloads, raw embeddings, or chain-of-thought.
- No backend/frontend/runtime behavior, migrations, models, CI, or deployment
  behavior are changed.

Validation:

```bash
git status --short
docker-compose config
git diff --check
```

### TASK 015.4 - Architecture Diagrams and Screenshot Checklist

Goal: Add maintainable diagram sources and a screenshot/media checklist for
final report and presentation use.

Scope:

- Add Mermaid or markdown diagram sources for:
  - system context
  - container/deployment
  - backend layers
  - database/domain overview
  - LangGraph workflow
  - approval/resume lifecycle
  - RAG ingestion/retrieval
  - event streaming
  - frontend/API integration
  - CI/deployment flow
- Add screenshot checklist with routes, expected state, and no-secret review.
- Do not capture screenshots or generate videos in this task unless explicitly
  requested.
- Do not add image-generation dependencies or external diagram tooling unless
  already present and justified.

Acceptance criteria:

- Diagram inventory/source files exist and are reviewable as text.
- Diagrams do not include unimplemented architecture as if present.
- Screenshot checklist covers login, dashboard, workflow run, approval,
  evidence, resume, timeline, knowledge search/catalog, metrics/readiness, and
  CI/smoke evidence.
- No app behavior, migrations, models, deployment automation, or frontend
  features are changed.

Validation:

```bash
git status --short
docker-compose config
git diff --check
```

### TASK 015.5 - Final Demo Script and Defense Q&A Bank

Goal: Prepare the final presentation script and defense/Q&A bank for the
graduation board.

Scope:

- Add an 8-12 minute final demo script.
- Add a 3-5 minute fallback summary.
- Include product pitch, business problem, architecture overview, live demo
  steps, RAG explanation, approval/resume explanation, deployment/CI/
  observability explanation, limitations, and closing value proposition.
- Add a Q&A bank covering architecture choices, LangGraph, FastAPI/Next.js,
  Postgres/Redis/Qdrant/MinIO, deterministic demo mode, real LLM mode,
  approval auditability, RAG limitations, deployment limitations, testing, and
  future work.
- Keep commands aligned with existing runbooks.

Acceptance criteria:

- Demo script is timed and executable against current runbooks.
- Q&A bank answers likely defense questions without overstating scope.
- No real secrets, keys, tokens, screenshots of env files, raw prompts, raw
  provider payloads, embeddings, or chain-of-thought are included.
- No app behavior, migrations, models, frontend features, or deployment
  automation are changed.

Validation:

```bash
git status --short
docker-compose config
git diff --check
```

### TASK 015.6 - Repository Release Polish and Final Quality Gate

Goal: Perform final repository release polish and run the complete quality gate
without adding new product features.

Scope:

- Review README entry points and docs index links.
- Review env examples and docs for placeholder-only secrets.
- Run no-secret scans across source/docs/scripts/env examples while excluding
  generated dependency/build folders.
- Run local CI gates and production-demo smoke checks.
- Capture final gate summaries for the evaluation report.
- Make tiny docs/copy fixes only when they block final evaluation clarity.

Acceptance criteria:

- README/docs entry points are coherent.
- No real secrets or real-looking provider keys are committed.
- `scripts/ci/all-gates.sh` passes or any blocker is documented with exact
  failure evidence.
- Production compose config and image build pass.
- Demo seed and knowledge ingestion dry-runs pass.
- Frontend lint/build/typecheck/test pass.
- No backend/frontend/runtime behavior, migrations, models, or deployment
  automation are changed except tiny docs polish.

Validation:

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

Optional:

```bash
bash scripts/deployment/smoke-prod-demo.sh --start
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example down --remove-orphans
```

### TASK 015.7 - Final Project Closeout Review

Goal: Verify the project is graduation-ready, evidence-backed, safe, and ready
for final submission.

Scope:

- Review all SPEC-015 final docs/assets.
- Review SPEC-001 through SPEC-014 closure evidence.
- Verify final evaluation matrix, E2E checklist, report structure, diagrams,
  screenshots checklist, demo script, Q&A bank, release checklist, and known
  limitations.
- Run final validation gates where practical.
- Make only tiny docs/test/hardening fixes if a blocking issue is found.
- Record Harness closeout evidence.

Acceptance criteria:

- Final project status is Approved or Rejected with evidence.
- Final validation results are reported.
- Blocking and non-blocking issues are listed.
- No real secrets, real provider keys, raw prompts, provider payloads, raw
  embeddings, or chain-of-thought are present in final assets.
- No unplanned backend/frontend/runtime behavior, migrations, models, cloud
  resources, deployment automation, upload UI, secret vault, enterprise SSO,
  token streaming, or production email are added.

Validation:

```bash
git status --short
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
bash scripts/ci/all-gates.sh
bash scripts/deployment/smoke-prod-demo.sh --help
git diff --check
git diff --cached --check
```

Output:

- Final project status: Approved or Rejected.
- Evidence summary.
- Functional evaluation summary.
- Demo validation summary.
- Report/diagram/screenshot asset summary.
- Deployment/CI/observability summary.
- Security/no-secret summary.
- Blocking issues.
- Non-blocking issues.
- Backlog items.
- Final recommendation.

