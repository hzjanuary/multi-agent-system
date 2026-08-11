# Multi-Agent System / Enterprise Multi-Agent OS

**Enterprise Procurement Workflow Automation using a LangGraph-based Multi-Agent System**

Multi-Agent System is a graduation-ready enterprise workflow orchestration
project. It is not a chatbot. The application turns procurement requests into
stateful workflows, runs deterministic agent stages, pauses at human approval,
shows bounded operational evidence, and resumes only after an authorized
decision.

## Status

- Final graduation-ready project.
- SPEC-001 through SPEC-023 completed and approved.
- SPEC-024 dependency/security maintenance is closed with bounded frontend
  patch updates applied and remaining npm audit findings documented/deferred
  without changing demo behavior.
- Frontend demo surfaces use the **Violet Operations Console** dark command
  center design.
- Default demo is deterministic and no-key.
- Optional RAG-enabled demo works without real LLM keys.
- Optional local Telegram + Ollama extraction path is available for live
  phone-to-workflow defense demos.
- Docker Compose local and production-demo stacks are available.
- Final evaluation, report, diagram, screenshot, demo script, release, and Q&A
  assets are included.

This repository does not claim cloud production deployment, Kubernetes,
Terraform, enterprise SSO, production secret vault, production OCR, production
email sending, or zero-downtime deployment.

## What It Demonstrates

The defense demo path:

```text
Vietnamese Telegram RFQ
  -> local Telegram bridge
  -> optional Ollama intent extraction
  -> deterministic normalization and catalog safety guard
  -> backend workflow create
  -> deterministic /run
  -> WAITING_APPROVAL
  -> Agent Monitor observation
  -> Manager approval
  -> explicit /resume
  -> COMPLETED with email preview only
```

No final quote, price, stock, delivery promise, auto-approval, auto-resume, or
real email is claimed.

## Key Capabilities

- FastAPI backend with typed APIs.
- Next.js dashboard with dark enterprise operations UI.
- JWT auth and RBAC for Admin, Manager, Sales, Legal, Finance, and Viewer.
- LangGraph workflow runtime with deterministic no-key default behavior.
- `/run` stops at `WAITING_APPROVAL`; `/resume` continues only after approval.
- Human approval history, duplicate-final-decision protection, and audit/event
  trail.
- Agent Monitor for Planner, Retrieval/RAG, Calculator, Compliance,
  Validation/Finance, Approval Package, Human Approval, and Email Preview
  stages.
- Persisted workflow events and WebSocket timeline streaming.
- LLM provider abstraction for fake, Groq, OpenRouter, Ollama, and Gemini.
- Local Telegram inbound bridge with deterministic parser, optional Ollama
  extraction, sales-style replies, Office 365 detection, and unsupported mixed
  item guard.
- RAG/document knowledge base with fake embeddings by default, Qdrant vector
  store, and MinIO object storage.
- Docker Compose local and production-demo stacks.
- Health, liveness, readiness, structured logs, request IDs, redaction, and
  protected bounded metrics.
- CI/local quality gates and final non-mutating quality gate script.
- Final evaluation, report, Mermaid diagrams, screenshot checklist, final demo
  script, and defense Q&A assets.

## Architecture

```mermaid
flowchart LR
  Telegram[Telegram Customer]
  Bridge[Local Telegram Bridge]
  Frontend[Next.js Violet Operations Console]
  API[FastAPI Backend API]
  Auth[JWT Auth / RBAC]
  Workflow[Workflow Services]
  Runtime[LangGraph Runtime]
  Agents[Deterministic Agent Stages]
  Approval[Human Approval / Resume]
  Knowledge[Knowledge / RAG Service]
  LLM[LLM Provider Abstraction]
  Postgres[(Postgres)]
  Redis[(Redis)]
  Qdrant[(Qdrant)]
  MinIO[(MinIO)]
  Ollama[Optional Local Ollama]

  Telegram --> Bridge
  Bridge --> API
  Frontend --> API
  API --> Auth
  API --> Workflow
  Workflow --> Runtime
  Runtime --> Agents
  Runtime --> Approval
  Runtime --> Knowledge
  Runtime --> LLM
  Bridge -. optional extraction .-> Ollama
  Workflow --> Postgres
  Runtime --> Redis
  Knowledge --> Qdrant
  Knowledge --> MinIO
```

More detail:

- [Architecture diagrams](docs/report/diagrams/README.md)
- [Architecture and design narrative](docs/report/ARCHITECTURE_AND_DESIGN.md)
- [Project architecture contract](.ai/project/ARCHITECTURE.md)

## Tech Stack

| Area | Stack |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic v2, async SQLAlchemy, Alembic |
| Runtime | LangGraph |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Storage | Postgres, Redis, Qdrant, MinIO |
| Auth | JWT, Argon2, RBAC |
| LLM | fake, Groq, OpenRouter, Ollama, Gemini |
| RAG | deterministic chunking, fake embeddings, Qdrant retrieval, MinIO document storage |
| Observability | structured JSON logs, request IDs, readiness checks, redaction, in-process metrics |
| DevOps | Docker, Docker Compose, GitHub Actions, Bash gate scripts |
| Quality | pytest, Ruff, Black, MyPy, npm lint/build/typecheck/test |

## Repository Structure

```text
backend/                  FastAPI backend, runtime, APIs, services, tests
frontend/                 Next.js operations console and frontend tests
docs/demo/                Demo runbooks, Telegram bridge docs, operator guide
docs/deployment/          Env docs, production-demo runbook, smoke, troubleshooting
docs/evaluation/          SPEC-022 benchmark guide and demo regression checklist
docs/final/               Final evaluation, demo validation, release assets
docs/governance/          Catalog, provider evidence, approval, and outbound policy
docs/production/          Production hardening checklists and secrets runbook
docs/release/             Final release-readiness package and command checklist
docs/security/            Dependency/security maintenance and triage docs
docs/report/              Graduation report narrative assets
docs/report/diagrams/     Mermaid architecture diagram sources
docs/llm/                 Provider setup and local Ollama smoke docs
scripts/ci/               Compose, backend, frontend, and all-gates scripts
scripts/deployment/       Production-demo smoke script
scripts/demo/             Local Telegram and LLM smoke utilities
scripts/final/            E2E validation and final quality gate scripts
.github/workflows/ci.yml  GitHub Actions CI workflow
.ai/specs/                SPEC planning and closeout assets
docker-compose.yml        Local development Compose stack
docker-compose.prod.yml   Production-demo Compose stack
SPEC.md                   Product specification
AGENTS.md                 Agent operating guide
```

## Quick Start - Stable Local Demo

```bash
git clone https://github.com/hzjanuary/multi-agent-system.git
cd multi-agent-system
```

Stable backend mode:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

Start infrastructure and seed the local demo explicitly:

```bash
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
docker-compose up --build backend
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000/demo
```

Use the documented local-demo Manager account from
[Frontend operator guide](docs/demo/FRONTEND_OPERATOR_GUIDE.md). Demo
credentials are local-demo/board-demo only.

## Telegram Live Demo

Use this path for the phone-to-system defense demo:

```bash
export TELEGRAM_BOT_TOKEN="<set locally from BotFather>"
export TELEGRAM_LLM_EXTRACTION_ENABLED=true
export TELEGRAM_LLM_BASE_URL=http://localhost:11434
export TELEGRAM_LLM_MODEL=qwen2.5:7b-instruct-q4_K_M
export TELEGRAM_SALES_REPLY_ENABLED=true

python scripts/demo/telegram_inbound_bridge.py --llm-extraction --sales-replies
```

Ollama is used only by the local Telegram bridge for RFQ extraction. The backend
runtime remains deterministic when `LLM_PROVIDER=fake` and
`LLM_RUNTIME_ENABLED=false`.

Primary live demo message:

```text
vay lay truoc cho toi 20 cai laptop tieu chuan kem san office 365
```

Reference evidence is optional display only: the bridge never calls Tavily or
live price lookup, and reference prices are review material, never a final
quote. The feature-flagged price research foundation is documented in
`.ai/specs/SPEC-016-conversational-sales-agent/spec.md` with a manual-only live
smoke path in `docs/demo/PROVIDER_LIVE_VERIFICATION.md` and evidence policy in
`docs/governance/PROVIDER_EVIDENCE_POLICY.md`.

Reference docs:

- [Final live demo runbook](docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md)
- [Telegram inbound bridge](docs/demo/TELEGRAM_INBOUND_DEMO.md)
- [Frontend operator guide](docs/demo/FRONTEND_OPERATOR_GUIDE.md)
- [Ollama local smoke guide](docs/llm/OLLAMA_LOCAL_SMOKE.md)

## Production-Demo Compose

The production-demo stack packages frontend, backend, Postgres, Redis, Qdrant,
and MinIO. It is a bounded demo deployment package, not a cloud production
claim.

```bash
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend
bash scripts/deployment/smoke-prod-demo.sh --help
```

Docs:

- [Deployment README](docs/deployment/README.md)
- [Production-demo runbook](docs/deployment/RUNBOOK.md)
- [Smoke checks](docs/deployment/SMOKE_CHECKS.md)
- [Troubleshooting](docs/deployment/TROUBLESHOOTING.md)

## Demo Workflow In The UI

1. Open `/demo`.
2. Login as Manager.
3. Open Agent Monitor or a seeded workflow.
4. Run a CREATED workflow.
5. Verify `WAITING_APPROVAL`.
6. Inspect Agent Activity and timeline events.
7. Inspect RAG evidence only when RAG is enabled and knowledge was ingested.
8. Approve as Manager/Admin.
9. Resume explicitly.
10. Verify `COMPLETED`.

The frontend never fabricates workflow records, agent activity, events,
evidence, prices, approvals, or final quotes.

## API Overview

Implemented endpoint groups:

- `GET /`, `GET /health`, `GET /live`, `GET /ready`
- Auth login, refresh, logout, current user
- Workflow create, list, detail, run, approval, approval history, resume
- Workflow events and workflow WebSocket stream
- Knowledge document list/detail and search
- Admin/Manager observability metrics

Deferred areas include provider-management UI, cloud deployment automation,
upload/admin document management UI, production email sending, token streaming,
and agent-thought streaming.

## Quality Gates

Run from the repository root:

```bash
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
bash scripts/ci/compose-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
bash scripts/final/final-quality-gate.sh
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
npm run typecheck
npm test
```

The final quality gate is non-deploying and non-mutating by default. Full E2E
validation requires explicit `--confirm-local-demo`.

## Final Evaluation And Report Assets

- [Release readiness package](docs/release/FINAL_PROJECT_PACKAGE.md)
- [Release readiness checklist](docs/release/RELEASE_READINESS_CHECKLIST.md)
- [Release demo commands](docs/release/DEMO_COMMANDS.md)
- [Known limitations and roadmap](docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md)
- [Dependency security maintenance](docs/security/DEPENDENCY_SECURITY_MAINTENANCE.md)
- [Security triage report](docs/security/SECURITY_TRIAGE_REPORT.md)
- [SPEC-025 remediation matrix](docs/security/SPEC_025_REMEDIATION_MATRIX.md)
- [SPEC-022 evaluation guide](docs/evaluation/SPEC_022_EVALUATION_GUIDE.md)
- [Demo regression checklist](docs/evaluation/DEMO_REGRESSION_CHECKLIST.md)
- [Final docs index](docs/final/README.md)
- [Evaluation matrix](docs/final/EVALUATION_MATRIX.md)
- [Acceptance evidence plan](docs/final/ACCEPTANCE_EVIDENCE_PLAN.md)
- [E2E demo validation](docs/final/E2E_DEMO_VALIDATION.md)
- [Screenshot checklist](docs/final/SCREENSHOT_CHECKLIST.md)
- [Final demo script](docs/final/FINAL_DEMO_SCRIPT.md)
- [Defense Q&A bank](docs/final/DEFENSE_QA_BANK.md)
- [Release checklist](docs/final/RELEASE_CHECKLIST.md)
- [Final quality gate](docs/final/FINAL_QUALITY_GATE.md)
- [Report assets](docs/report/README.md)

## Safety Boundaries

- Do not commit real secrets, provider keys, Telegram tokens, local `.env`
  files, or `docker-compose.override.yml`.
- Use `docker-compose.override.example.yml` as a safe placeholder template.
- Demo credentials are local-demo/board-demo only.
- Do not use real customer data.
- No final quote is issued before approval.
- No auto-approval or auto-resume.
- No real email is sent.
- No unsupported item is silently dropped by the Telegram bridge.
- No fake price/catalog behavior.
- No raw prompts, provider payloads, embeddings, vector payloads, secrets,
  tokens, cookies, or chain-of-thought are displayed intentionally.
- Dependency remediation is tracked separately from the stable demo release;
  do not run automatic audit fixes without a reviewed maintenance sprint.

## Roadmap After Defense

1. SPEC-016 conversational sales / reference price evidence foundation:
   governance and live-verification hardening. Price research stays
   feature-flagged, disabled by default, and is never a final quote:
   `.ai/specs/SPEC-016-conversational-sales-agent/spec.md` and
   `docs/demo/PROVIDER_LIVE_VERIFICATION.md`.
2. LLM runtime hardening beyond the deterministic defense path.
3. Catalog governance and expansion beyond the closed SPEC-018 demo catalog.
4. Provider policy hardening after the manual-only SPEC-019 Tavily smoke path.
5. Email/Gmail send-provider planning beyond the closed SPEC-020 preview-only
   foundation.
6. Production deployment polish.
7. Bounded dependency/security patch sprint after SPEC-024 triage review.

## License

This repository is an academic graduation project.
