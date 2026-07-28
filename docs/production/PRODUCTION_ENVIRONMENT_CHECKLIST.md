# Production Environment Checklist

## Purpose

Use this checklist before running the production-demo stack or preparing a
future production-like deployment of Multi-Agent System / Enterprise Multi-Agent
OS.

This document is a hardening checklist only. It does not change application
behavior, Docker/Compose configuration, CI, runtime defaults, provider behavior,
Telegram behavior, API contracts, database state, outbound email behavior, or
final quotation behavior.

The current `docker-compose.prod.yml` stack is a production-demo package. It is
not a claim of cloud deployment automation, Kubernetes, Terraform, enterprise
SSO, production secret vault, production backup automation, zero-downtime
deployment, or real outbound email sending.

## Stable Demo Defaults

The stable defense/demo mode remains deterministic and no-key:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
```

Additional stable defaults and boundaries:

- `EMBEDDING_PROVIDER=fake`
- `TELEGRAM_LLM_EXTRACTION_ENABLED=false`
- `TELEGRAM_SALES_REPLY_ENABLED=false`
- no real email sending;
- no outbound send endpoint;
- no automatic live provider calls;
- no Telegram live price research;
- no final quote before Manager/Admin approval and explicit resume;
- provider keys are not required for deterministic validation or CI.

`RAG_ENABLED=true`, Telegram LLM extraction, sales replies, provider live
verification, and outbound preview are optional paths. Enable them only when a
specific runbook says to do so.

## Required Environment Files

Review these files before production-demo use:

| File | Purpose | Production hardening rule |
| --- | --- | --- |
| `backend/.env.example` if present | Backend local environment example | Example only; never commit a copied real `.env`. |
| `frontend/.env.example` if present | Frontend local environment example | Browser-visible values only; never include secrets in `NEXT_PUBLIC_*`. |
| `docs/deployment/.env.production.example` | Production-demo env template | Placeholder values only; replace through local ignored env files or deployment injection for real runs. |
| `.env` | Local backend settings loaded by Pydantic if present | Must remain untracked. |
| `docker-compose.override.yml` | Local Compose override | Must remain untracked and local-only. |

Local override policy:

- keep local `.env` files outside Git;
- keep `docker-compose.override.yml` outside Git;
- use placeholder examples only in tracked files;
- never paste real provider keys, Telegram tokens, JWT secrets, database
  passwords, MinIO secrets, cookies, or access tokens into tracked docs;
- review screenshots and copied command output before committing evidence.

Related production runbooks:

- `docs/production/SECRETS_AND_PROVIDER_KEYS_RUNBOOK.md`
- `docs/production/BACKUP_RESTORE_AND_MIGRATION_RUNBOOK.md`
- `docs/production/OBSERVABILITY_AND_INCIDENT_RESPONSE_RUNBOOK.md`

## Required Production Checks

Run from the repository root unless a section says otherwise.

### Repository Hygiene

```bash
git status --short
git diff --check
```

Expected:

- only intentional docs or release changes are present;
- no generated screenshots, videos, PDFs, DOCX files, build outputs, or local
  evidence files are accidentally committed;
- no tracked file contains real secrets or customer data;
- no dependency, backend, frontend, Docker, Compose, CI, API, database,
  Telegram, provider, outbound, runtime-default, or final-quote behavior change
  is present unless a future approved task explicitly authorizes it.

### Compose Validation

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Expected:

- local Compose config is valid;
- production-demo Compose config is valid with placeholder values;
- validation does not call live providers, send email, push images, or deploy
  cloud resources.

### Backend Health And Readiness Checks

With backend running:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/live
curl http://localhost:8000/ready
```

Expected:

- `/health` confirms the backend process is alive;
- `/live` confirms liveness;
- `/ready` confirms dependencies are reachable when Postgres, Redis, Qdrant,
  and MinIO are healthy;
- readiness failures are investigated before demo or production-like use.

### Frontend Build Checks

```bash
cd frontend
npm install
npm run lint
npm run build
npm run typecheck
npm test
cd ..
```

Expected:

- frontend lint/build/typecheck/test pass;
- no fake metrics, fake evidence, provider payloads, secrets, or final quote
  claims are introduced.

### Evaluation Runner Checks

```bash
python3 -m unittest scripts.evaluation.test_evaluate_telegram_parser
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_telegram_parser.py \
  --output-json /tmp/telegram_eval_metrics.json

python3 -m unittest scripts.evaluation.test_evaluate_demo_safety
python3 scripts/evaluation/evaluate_demo_safety.py
python3 scripts/evaluation/evaluate_demo_safety.py \
  --output-json /tmp/demo_safety_metrics.json
```

Expected:

- deterministic parser and demo safety benchmarks pass;
- no backend API, database, Telegram network, LLM provider, Tavily/live web, or
  email call is required.

### Full Gate

```bash
bash scripts/ci/all-gates.sh
```

Expected:

- Compose gate passes;
- backend gate passes;
- frontend gate passes;
- production-demo backend/frontend image build passes;
- whitespace check passes.

## Forbidden Production Defaults

These values or conditions are forbidden for real production-like operation:

- `APP_ENV=development`;
- `DEBUG=true`;
- `JWT_SECRET_KEY=change-me-in-production`;
- `JWT_SECRET_KEY=development-only-change-me-32-bytes-minimum`;
- empty required secrets for `JWT_SECRET_KEY`, `DATABASE_URL`,
  `POSTGRES_PASSWORD`, `MINIO_ACCESS_KEY`, or `MINIO_SECRET_KEY`;
- `DATABASE_URL` containing `postgres:postgres` or `change-me-in-production`;
- `POSTGRES_PASSWORD=change-me-in-production`;
- `MINIO_ACCESS_KEY=minioadmin` for a real deployment;
- `MINIO_SECRET_KEY=minioadmin` for a real deployment;
- `MINIO_ACCESS_KEY=change-me-in-production`;
- `MINIO_SECRET_KEY=change-me-in-production`;
- real `TELEGRAM_BOT_TOKEN` in tracked files;
- real `TAVILY_API_KEY` in tracked files;
- real Groq, OpenRouter, Gemini, Ollama-adjacent, or other LLM provider keys in
  tracked files;
- provider keys in `NEXT_PUBLIC_*` variables;
- `OUTBOUND_SEND_ENABLED=true` without a future approved send spec and
  implementation;
- committed local `.env` files;
- committed `docker-compose.override.yml`;
- screenshots, logs, issue reports, docs, or metrics output containing tokens,
  cookies, Authorization headers, passwords, provider payloads, raw prompts,
  embeddings, vector payloads, chain-of-thought, or real customer data.

## Feature Flag Review Table

| Setting | Stable/default expectation | Production hardening review |
| --- | --- | --- |
| `LLM_PROVIDER` | `fake` | Keep fake for stable demo. Real providers require explicit local keys and future production policy. |
| `LLM_RUNTIME_ENABLED` | `false` | Do not enable backend LLM runtime by default. Validate approval and no-final-quote boundaries before any future change. |
| `PRICE_RESEARCH_ENABLED` | `false` | Price research is reference evidence only and disabled by default. No Telegram live price research. |
| `RAG_ENABLED` | `false` | Optional after explicit knowledge ingestion. Evidence appears only when workflow state supplies it. |
| `OUTBOUND_COMMUNICATION_ENABLED` | `false` | Preview-only path. Requires completed approval/resume evidence when enabled. |
| `OUTBOUND_SEND_ENABLED` | `false` | Must remain false until a future approved send spec adds send behavior. |
| `TELEGRAM_LLM_EXTRACTION_ENABLED` | `false` | Optional local demo bridge behavior only. Not a backend runtime setting. |
| `TELEGRAM_SALES_REPLY_ENABLED` | `false` | Optional local demo bridge reply style only. It must not issue final quotes. |
| `TAVILY_API_KEY` | empty | Manual-only provider live verification. Never required in CI. Never commit. |
| `GROQ_API_KEY` | empty | Optional LLM provider key. Never required for deterministic demo or CI. |
| `OPENROUTER_API_KEY` | empty | Optional LLM provider key. Never required for deterministic demo or CI. |
| `GEMINI_API_KEY` | empty | Optional LLM provider key. Never required for deterministic demo or CI. |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | local/manual | Ollama may support local Telegram extraction or local LLM smoke only; backend runtime remains disabled by default. |
| `NEXT_PUBLIC_API_BASE_URL` | public backend API URL | Browser-visible; must not contain secrets. |
| `NEXT_PUBLIC_WS_BASE_URL` | public backend WebSocket URL | Browser-visible; must not contain secrets. |

## Pre-Deploy Checklist

- [ ] Confirm this is production-demo or a future approved production-like run.
- [ ] Confirm `git status --short` contains only intentional changes.
- [ ] Confirm no local `.env` or `docker-compose.override.yml` is tracked.
- [ ] Review `docs/deployment/.env.production.example` and local deployment
  env values.
- [ ] Replace placeholder secrets outside Git for real production-like use.
- [ ] Confirm `APP_ENV=production` for production-demo.
- [ ] Confirm `DEBUG=false`.
- [ ] Confirm `LOG_REDACTION_ENABLED=true`.
- [ ] Confirm browser-visible `NEXT_PUBLIC_*` values contain no secrets.
- [ ] Confirm stable no-key defaults unless an optional path is intentionally
  enabled.
- [ ] Confirm `OUTBOUND_SEND_ENABLED=false`.
- [ ] Confirm no live provider key is required by required validation.
- [ ] Run Compose config validation.
- [ ] Run backend/frontend/all-gates as appropriate for the release.
- [ ] Review remaining npm audit findings in
  `docs/security/SECURITY_TRIAGE_REPORT.md` and
  `docs/security/SPEC_025_REMEDIATION_MATRIX.md`.

## Post-Deploy Smoke Checklist

- [ ] Backend `/health` returns success.
- [ ] Backend `/live` returns success.
- [ ] Backend `/ready` returns success after dependencies are healthy.
- [ ] Frontend `/login` loads.
- [ ] Frontend `/demo` loads.
- [ ] Frontend `/agent-monitor` loads after login.
- [ ] Manager/Admin login works with intended environment credentials.
- [ ] Workflow list loads.
- [ ] Workflow detail loads.
- [ ] `/run` stops at `WAITING_APPROVAL`.
- [ ] Manager/Admin approval is required.
- [ ] `/resume` is explicit and only used after approval.
- [ ] Timeline/events are visible.
- [ ] Reference evidence is labeled reference-only when present.
- [ ] No final quote, stock, delivery, discount approval, auto-approval,
  auto-resume, real email, or email-sent claim appears before the approved
  lifecycle supports it.
- [ ] Metrics endpoint access remains protected and safe.

## Rollback Readiness Checklist

- [ ] Know the release tag or commit to roll back to.
- [ ] Keep previous env values available in a secure local store.
- [ ] Do not delete volumes during rollback unless a separate recovery plan
  requires it.
- [ ] Preserve Postgres, Redis, MinIO, and Qdrant volumes before destructive
  recovery.
- [ ] Stop production-demo services without deleting volumes:

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example down
```

- [ ] Rebuild known-good images if needed:

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example build backend frontend
```

- [ ] Restart with reviewed env values.
- [ ] Rerun health, readiness, login, workflow, approval, and resume smoke.
- [ ] Record the incident and rollback reason without exposing secrets.

## Known Limitations And Deferred Security Findings

Current limitations remain:

- no cloud production deployment automation;
- no Kubernetes or Terraform;
- no production secret vault;
- no enterprise SSO;
- no production backup automation;
- no real email sending;
- no outbound send endpoint;
- no automatic live provider calls;
- no Telegram live price research;
- reference evidence is not a final quotation;
- deterministic catalog remains demo-focused.

Dependency/security carryover:

- frontend `npm audit` still reports documented high-severity findings;
- SPEC-024 and SPEC-025 document triage and deferred remediation;
- `npm audit fix`, `npm audit fix --force`, broad `npm update`, Next major,
  React major, ESLint major, Tailwind major, or TypeScript major changes require
  a future reviewed maintenance sprint;
- backend dependency review should be rerun in an environment with Poetry
  available.
