# Enterprise Multi-Agent OS

**Academic Title:** Enterprise Procurement Workflow Automation using LangGraph-based Multi-Agent System

A state-driven business workflow operating system that automates complex enterprise procurement workflows by coordinating multiple specialized AI Agents, deterministic tools, enterprise knowledge bases, human approvals, and audit trails.

This is not a chatbot. It is a **workflow orchestration platform** where AI Agents act as specialized workers inside a controlled enterprise process.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Docker Services](#docker-services)
- [Backend](#backend)
- [Workflow Pipeline](#workflow-pipeline)
- [User Roles](#user-roles)
- [Implementation Phases](#implementation-phases)
- [Demo Dataset](#demo-dataset)
- [API Endpoints](#api-endpoints)

---

## Overview

Enterprise Multi-Agent OS orchestrates a multi-step procurement workflow:

```
Business Request
  -> Planner Agent (classify intent and domain)
  -> Retrieval Agent (fetch contracts, policies, pricing)
  -> Calculator Agent (deterministic quotation generation)
  -> Compliance Agent (check against policies and contracts)
  -> Validation Agent (schema and business rule validation)
  -> Human Approval (manager review)
  -> Email Preview Agent (generate customer-facing output)
  -> Completed Workflow
```

The platform supports five procurement domains:

- IT Equipment
- Office Furniture
- Facility Maintenance
- Software Subscription
- Logistics Equipment

---

## Architecture

```
NextJS Dashboard
    |
FastAPI API Gateway
    |
LangGraph Workflow Runtime
    |
Specialized Agent Layer
    |
+-- PostgreSQL (business data)
+-- Redis (runtime state, cache)
+-- Qdrant (vector search)
+-- MinIO (object storage)
+-- LLM Providers (Groq, OpenRouter, Ollama, Gemini)
```

**Design principles:**
- Clean Architecture with async-first backend
- State-driven orchestration with explicit human-in-the-loop control
- Tool-based Agent execution (Agents do not own workflow state)
- Every Agent has one responsibility and returns structured Pydantic output
- Deterministic calculation (LLM never performs arithmetic directly)
- All outputs carry citations and metadata

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| Database | PostgreSQL 16 (asyncpg), SQLAlchemy 2, Alembic |
| Cache | Redis 7 |
| Vector Store | Qdrant |
| Object Storage | MinIO |
| Workflow Engine | LangGraph |
| LLM Providers | Groq, OpenRouter, Ollama, Gemini |
| Auth | JWT (PyJWT), Argon2 password hashing |
| Code Quality | Ruff, Black, MyPy, Pytest |
| Logging | Structlog |
| Infrastructure | Docker, Docker Compose |
| Frontend (planned) | NextJS, TypeScript, Tailwind CSS, shadcn/ui |

---

## Project Structure

```
.
├── .ai/                          # AI development assets
│   ├── project/                  # Project contracts and architecture docs
│   │   ├── PROJECT_CONTRACT.md
│   │   ├── ARCHITECTURE.md
│   │   ├── TECH_STACK.md
│   │   ├── CODING_STANDARD.md
│   │   ├── FOLDER_STRUCTURE.md
│   │   ├── STATE_CONTRACT.md
│   │   ├── AGENT_CONTRACT.md
│   │   ├── API_CONTRACT.md
│   │   └── DATABASE_CONTRACT.md
│   ├── prompts/                  # Agent system prompts
│   ├── specs/                    # SPEC files (29 specs across 6 phases)
│   └── templates/                # Spec, task, ADR, PR templates
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/v1/               # API routes
│   │   ├── auth/                 # JWT, RBAC, password utilities
│   │   ├── cache/                # Redis cache provider
│   │   ├── config/               # Settings (pydantic-settings)
│   │   ├── core/                 # Logging, utilities
│   │   ├── db/                   # SQLAlchemy session, base, mixins
│   │   ├── exceptions/           # Exception handlers
│   │   ├── middleware/            # Request ID, logging middleware
│   │   ├── models/               # SQLAlchemy models
│   │   ├── repositories/         # Generic CRUD repository
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Business logic layer
│   │   ├── storage/              # MinIO object storage provider
│   │   ├── tests/                # Pytest test suite
│   │   ├── vectorstore/          # Qdrant vector store provider
│   │   └── workflows/            # Workflow state, lifecycle, events
│   ├── alembic/                  # Database migrations
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
├── datasets/                     # Demo data for MVP
│   ├── customers.csv / .json
│   ├── products.csv / .json
│   ├── pricing_rules.csv / .json
│   ├── contracts/                # Contract documents
│   ├── policies/                 # Policy documents
│   ├── rfqs/                     # Sample RFQ requests
│   ├── expected_outputs/         # Expected quotation outputs
│   └── index/                    # Document index
├── docs/                         # Harness and project documentation
├── scripts/                      # Schema SQL, CLI tools
├── docker-compose.yml
├── SPEC.md                       # Full product specification
└── AGENTS.md                     # Agent operating guide
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.12 (for local development)
- Poetry (Python package manager)

### Quick Start with Docker

```bash
# Clone the repository
git clone <repository-url>
cd graduation-project-2

# Start all services
docker-compose up --build

# Verify the backend is running
curl http://localhost:8000/health
```

### Local Development Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Start infrastructure services only
docker-compose up -d postgres redis qdrant minio

# Run database migrations
docker-compose run --rm backend-test alembic upgrade head

# Start the backend
poetry run uvicorn app.main:app --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

### Running Tests

```bash
# Via Docker (reproducible environment)
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app

# Or locally
cd backend
poetry run pytest
poetry run ruff check .
poetry run black --check .
poetry run mypy app
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | Environment mode | `development` |
| `DEBUG` | Debug mode | `true` |
| `LOG_FORMAT` | Backend log renderer (`json` or `text`) | `json` |
| `LOG_REDACTION_ENABLED` | Masks secrets and raw payloads in operational logs | `true` |
| `METRICS_ENABLED` | Enables bounded in-process backend metrics | `true` |
| `METRICS_ROUTE_ENABLED` | Enables authenticated metrics endpoint | `true` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_os` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `QDRANT_URL` | Qdrant URL | `http://localhost:6333` |
| `MINIO_ENDPOINT` | MinIO endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | |
| `MINIO_SECRET_KEY` | MinIO secret key | |
| `MINIO_BUCKET_NAME` | MinIO bucket | `enterprise-multi-agent-os` |
| `JWT_SECRET_KEY` | JWT signing secret | (development default) |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `LLM_PROVIDER` | Active LLM provider | `fake` |
| `LLM_RUNTIME_ENABLED` | Enables LLM-assisted runtime path | `false` |
| `LLM_TIMEOUT_SECONDS` | LLM provider timeout | `30` |
| `LLM_MAX_RETRIES` | LLM retry count for transient errors | `2` |
| `LLM_FALLBACK_ENABLED` | Enables transient-error fallback | `false` |
| `LLM_FALLBACK_PROVIDER` | Fallback provider | `fake` |
| `LLM_MODEL` | Global LLM model fallback | |
| `GROQ_API_KEY` | Groq API key | |
| `GROQ_MODEL` | Groq model override | |
| `OPENROUTER_API_KEY` | OpenRouter API key | |
| `OPENROUTER_MODEL` | OpenRouter model override | |
| `GEMINI_API_KEY` | Gemini API key | |
| `GEMINI_MODEL` | Gemini model override | |
| `OLLAMA_BASE_URL` | Ollama base URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model override | |

See `backend/.env.example` for the full list. Never commit real secrets.
Deployment environment profiles and production-demo templates are documented in
`docs/deployment/ENVIRONMENT.md`.
Production-demo Compose usage is documented in `docs/deployment/README.md`.
CI quality gates and the production-demo smoke script are also documented in
`docs/deployment/README.md` and can be run locally with:

```bash
bash scripts/ci/all-gates.sh
bash scripts/deployment/smoke-prod-demo.sh
```

LLM provider setup and local demo guidance are documented in:

- `docs/llm/PROVIDER_SETUP.md`
- `docs/llm/LOCAL_LLM_DEMO.md`

---

## Docker Services

| Service | Port | Description |
|---|---|---|
| `backend` | 8000 | FastAPI API server |
| `postgres` | 5432 | PostgreSQL 16 database |
| `redis` | 6379 | Redis 7 cache |
| `qdrant` | 6333 | Qdrant vector database |
| `minio` | 9000 (API), 9001 (console) | MinIO object storage |

---

## Backend

### Health Endpoints

```
GET /       Service metadata and endpoint links
GET /health Overall application health
GET /ready  Dependency readiness check
GET /live   Liveness status
GET /api/v1/observability/metrics  Admin/Manager operational metrics
```

### Authentication

```
POST /api/v1/auth/login    Login with email and password
POST /api/v1/auth/refresh  Refresh token pair
POST /api/v1/auth/logout   Logout (stateless MVP)
GET  /api/v1/auth/me       Current user profile
```

Passwords are hashed with Argon2. Tokens use JWT with configurable expiry.

### RBAC Roles

- **Admin** — Full system access
- **Manager** — Approve/reject workflows
- **Sales** — Create and track workflows
- **Legal** — Manage policies and compliance
- **Finance** — Manage pricing and calculations
- **Viewer** — Read-only access

### Storage Providers

- **Cache** — `app/cache/` with Redis implementation
- **Vector Store** — `app/vectorstore/` with Qdrant implementation
- **Object Storage** — `app/storage/` with MinIO implementation

All providers follow an interface-first design. Each has a provider contract and a concrete implementation.

---

## Workflow Pipeline

### Workflow Statuses

```
CREATED -> PLANNING -> RETRIEVING -> CALCULATING -> CHECKING_COMPLIANCE
  -> VALIDATING -> WAITING_APPROVAL -> APPROVED -> GENERATING_EMAIL -> COMPLETED
```

Failure paths: `FAILED`, `CANCELLED`, `REJECTED`

### Agents

| Agent | Responsibility |
|---|---|
| Planner Agent | Classify intent, identify procurement domain, create execution plan |
| Retrieval Agent | Fetch contracts, policies, pricing data with citations |
| Calculator Agent | Deterministic quotation calculation (no LLM arithmetic) |
| Compliance Agent | Check quotation against policies, contracts, and domain rules |
| Validation Agent | Validate schemas, required fields, calculation consistency |
| Email Agent | Generate professional email preview (requires approval) |

---

## User Roles

| Role | Capabilities |
|---|---|
| Admin | Manage users, roles, system config, master data, audit logs |
| Sales | Create workflows, upload RFQs, track progress, review outputs |
| Manager | View pending approvals, approve/reject workflows |
| Legal | Upload policies, review compliance reports, add legal comments |
| Finance | Upload pricing, manage tax/discount rules, review calculations |
| Viewer | View workflows, details, and analytics (read-only) |

---

## Implementation Phases

| Phase | Scope | Status |
|---|---|---|
| Sprint -1 | AI Development Framework (.ai project files, datasets) | Done |
| Phase 1 | Infrastructure (Auth, DB, Storage providers) | In Progress |
| Phase 2 | Core Workflow Engine (State, LangGraph, APIs, Events) | Planned |
| Phase 3 | Agent Implementation (Planner, Retrieval, Calculator, Compliance, Validation, Email) | Planned |
| Phase 4 | Frontend (NextJS dashboard, Auth UI, Agent Monitor, Approval Center) | Planned |
| Phase 5 | Observability, Analytics, Demo | Planned |
| Phase 6 | Deployment, CI/CD, Final Documentation | Planned |

### Demo Acceptance Criteria

The MVP is successful when:

1. Sales user creates a workflow from the demo RFQ
2. Planner identifies domain as IT equipment
3. Retrieval finds contract `CON-2026-ACME-IT` and applies 10% discount
4. Calculator produces grand total of **47,628 USD**
5. Compliance returns PASS or LOW risk
6. Validation confirms output validity
7. Manager approves the workflow
8. Email Agent generates the email preview
9. Workflow status becomes COMPLETED

---

## Demo Dataset

Located in `datasets/`. Includes:

- Customers (CSV/JSON)
- Products (CSV/JSON)
- Pricing rules (CSV/JSON)
- Contracts (markdown)
- Policies (markdown)
- Sample RFQs
- Expected outputs
- Document index

### Recommended Demo Order

1. RFQ-001: IT equipment (simple, easy to explain)
2. RFQ-004: Software subscription (VAT 0, seat-based pricing)
3. RFQ-005: Logistics equipment (multi-item quotation)
4. RFQ-003: Facility maintenance (compliance/SLA logic)
5. RFQ-002: Office furniture (multi-item, installation policy)

### Local Demo Runbook

The current board-ready local demo flow is documented in:

- `docs/demo/DEMO_RUNBOOK.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
- `docs/llm/LOCAL_LLM_DEMO.md`

Use the runbook for Docker startup, migrations, deterministic demo seeding,
local-demo credentials, frontend walkthrough checkpoints, and troubleshooting.

Production-demo packaging and operator docs are documented in:

- `docs/deployment/RUNBOOK.md`
- `docs/deployment/DEMO_PACKAGE.md`
- `docs/deployment/SMOKE_CHECKS.md`
- `docs/deployment/TROUBLESHOOTING.md`
- `docs/deployment/BACKUP_RESTORE.md`

Those docs use the Docker Compose production-demo stack and preserve the
default no-key demo mode.

Final graduation evaluation planning is documented in:

- `docs/final/README.md`
- `docs/final/EVALUATION_MATRIX.md`
- `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md`

---

## API Endpoints

### Auth

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Workflows

- `POST /api/v1/workflows`
- `GET /api/v1/workflows`
- `GET /api/v1/workflows/{workflow_id}`
- `POST /api/v1/workflows/{workflow_id}/transition`
- `PATCH /api/v1/workflows/{workflow_id}/state`
- `GET /api/v1/workflows/{workflow_id}/events`
- `POST /api/v1/workflows/{workflow_id}/run`
- `POST /api/v1/workflows/{workflow_id}/approval`
- `GET /api/v1/workflows/{workflow_id}/approval/history`
- `POST /api/v1/workflows/{workflow_id}/resume`
- `GET /api/v1/workflows/_meta`

### Events

- `WS /api/v1/workflows/{workflow_id}/stream`

### Deferred Endpoints

The following product-contract capabilities are not implemented yet:

- workflow cancellation route
- approval center routes
- real LLM token streaming endpoints
- provider-management or admin key-management endpoints

---

## License

This project is an academic graduation project.
