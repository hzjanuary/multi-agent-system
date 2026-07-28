# Production Smoke Test Checklist

## Purpose And Scope

Use this checklist before a production-demo presentation or future
production-like operator review of Multi-Agent System / Enterprise Multi-Agent
OS.

This is a smoke-test checklist only. It does not add automation, change
Docker/Compose or CI behavior, enable provider calls, enable outbound send,
change runtime defaults, change backend/frontend behavior, change Telegram
behavior, modify APIs, modify database schema, or introduce final quote
behavior.

The checklist separates required deterministic validation from optional manual
paths. Required checks must not require provider keys, Telegram network access,
Tavily, Ollama, RAG ingestion, live web calls, or real email.

## Preconditions

Confirm the repository and environment are safe before starting.

- [ ] `git status --short` shows only intentional work.
- [ ] `git diff --check` passes.
- [ ] `git ls-files docker-compose.override.yml` returns no tracked file.
- [ ] Local `.env` files and `docker-compose.override.yml` remain untracked.
- [ ] `docs/deployment/.env.production.example` has been reviewed as a
  placeholder template only.
- [ ] No real provider key, Telegram token, JWT, cookie, password,
  Authorization header, database password, MinIO secret, raw prompt, provider
  payload, embedding, vector payload, chain-of-thought, or real customer data
  is present in tracked files or captured evidence.
- [ ] Risky feature flags remain disabled unless this smoke is explicitly
  testing an optional path:
  - `LLM_PROVIDER=fake`
  - `LLM_RUNTIME_ENABLED=false`
  - `PRICE_RESEARCH_ENABLED=false`
  - `RAG_ENABLED=false`
  - `OUTBOUND_COMMUNICATION_ENABLED=false`
  - `OUTBOUND_SEND_ENABLED=false`
  - `TELEGRAM_LLM_EXTRACTION_ENABLED=false`
  - `TELEGRAM_SALES_REPLY_ENABLED=false`

## Config Validation Commands

Run from the repository root.

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Expected:

- local Compose config is valid;
- production-demo Compose config is valid with placeholder values;
- no image push, cloud deployment, provider call, live web call, Telegram call,
  outbound send, or real email occurs.

## Required Local Validation Commands

Run the deterministic release checks:

```bash
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
bash scripts/ci/all-gates.sh
```

Expected:

- parser benchmark passes with no provider or Telegram network calls;
- demo safety benchmark passes with no backend/database/provider/email calls;
- all gates pass, including Compose, backend, frontend, production-demo image
  build, and whitespace checks;
- no real provider key is required.

## Backend Smoke Checks

With backend running, check the documented health surfaces:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/live
curl -fsS http://localhost:8000/ready
```

Expected:

- `/health` responds with safe process/service metadata;
- `/live` confirms the backend process is alive;
- `/ready` confirms Postgres, Redis, Qdrant, and object storage readiness when
  dependencies are healthy;
- readiness errors are bounded and do not expose connection strings, secrets,
  tokens, stack traces, provider payloads, raw prompts, embeddings, or vector
  payloads.

Optional authenticated metrics check, only when an Admin/Manager token is
intentionally available:

```bash
curl -fsS \
  -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/observability/metrics
```

Rules:

- do not paste real tokens into docs, screenshots, issues, or evidence files;
- metrics are bounded in-process visibility, not a managed monitoring system;
- metrics must not expose secrets or raw payloads.

API documentation availability should be checked only when the running
environment intentionally exposes docs. Do not treat public docs exposure as a
production requirement unless a future security review approves it.

## Frontend Smoke Checks

Required automated frontend validation is covered by:

```bash
bash scripts/ci/frontend-gate.sh
```

Manual route smoke should confirm these pages load and remain readable:

- `/login`
- `/demo`
- `/dashboard`
- `/agent-monitor`
- `/agent-monitor?workflowId=<workflow_id>`
- `/workflows`
- `/workflows/<workflow_id>`

Expected:

- dashboard loads without fake metrics;
- workflow detail loads with run/approval/resume controls visible when relevant;
- Agent Monitor loads with current status, next human action, Agent Activity,
  and timeline;
- reference evidence, catalog metadata, and outbound preview panels render only
  explicit workflow state/API data and do not fabricate data;
- no raw prompt, provider payload, embedding, vector payload,
  chain-of-thought, token, cookie, password, or secret is visible.

## Workflow Smoke Path

Use the documented deterministic demo seed when a local database needs demo
data:

```bash
docker compose run --rm backend-test alembic upgrade head
docker compose run --rm backend-test \
  python -m app.demo.seed --confirm-local-demo
```

Manual workflow smoke:

1. Login as a documented local-demo Manager/Admin account.
2. Open `/demo` or `/workflows`.
3. Open a seeded `CREATED` workflow or create/list/detail a workflow through the
   existing UI/API.
4. Run the workflow.
5. Confirm the workflow reaches `WAITING_APPROVAL`.
6. Confirm `/run` does not continue to email preparation.
7. Confirm Agent Monitor and workflow timeline show persisted stage/runtime
   events.
8. Submit Manager/Admin approval.
9. Confirm approval history records the decision.
10. Resume explicitly.
11. Confirm the workflow reaches `COMPLETED`.
12. Confirm outbound communication remains preview-only and no real email is
    sent.

Safety expectations:

- no auto-approval;
- no auto-resume;
- no final customer quotation before Manager/Admin approval and explicit
  resume;
- no stock availability, delivery date, discount approval, or real email-sent
  claim.

## Telegram Smoke Path

Telegram smoke is optional and manual-only.

Use:

```text
docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md
docs/demo/TELEGRAM_INBOUND_DEMO.md
```

Expected:

- local `TELEGRAM_BOT_TOKEN` is supplied outside Git;
- dry-run mode works without token or network:

```bash
python3 scripts/demo/telegram_inbound_bridge.py --dry-run --once
python3 scripts/demo/telegram_inbound_bridge.py --dry-run --once --sales-replies
```

- optional Ollama extraction is local to the Telegram bridge only;
- no Telegram live price research occurs;
- no Tavily/backend price-research provider call occurs from Telegram;
- no workflow is created for greetings, missing quantity/item, or mixed
  unsupported requests;
- supported catalog RFQs may create and auto-run a workflow to
  `WAITING_APPROVAL`;
- the bridge does not auto-approve, auto-resume, send email, or issue a final
  quote.

## Provider Live Verification Smoke

Provider live verification is manual-only and outside CI.

Dry-run, no-key, no-network example:

```bash
python3 scripts/demo/tavily_live_smoke.py \
  --provider tavily \
  --item "Standard business laptop" \
  --region VN \
  --currency VND \
  --dry-run
```

Live provider checks require a local `TAVILY_API_KEY` and explicit live
confirmation in the provider runbook. Treat live output as reference evidence
only, not a final quote.

Rules:

- do not commit provider keys;
- do not run live provider verification in CI;
- do not infer final price from snippets or prose;
- do not claim stock, delivery, discount approval, or final quotation;
- redact provider output before using it as evidence.

## Failure Handling

When a smoke check fails:

1. Stop and preserve the failing command, timestamp, route, status code, and
   request ID if available.
2. Do not delete volumes, reset the database, rotate secrets, or rerun
   migrations until the failure mode is understood.
3. Check `docs/production/OBSERVABILITY_AND_INCIDENT_RESPONSE_RUNBOOK.md`.
4. Check `docs/production/BACKUP_RESTORE_AND_MIGRATION_RUNBOOK.md` before any
   restore or migration action.
5. Check `docs/deployment/TROUBLESHOOTING.md` for production-demo startup
   issues.
6. Keep copied logs bounded and redacted.
7. If a token or provider key appears in output, rotate it and remove it from
   evidence.

Common failure paths:

- `/ready` fails: inspect dependency health for Postgres, Redis, Qdrant, and
  MinIO.
- frontend route fails: confirm `NEXT_PUBLIC_API_BASE_URL` and
  `NEXT_PUBLIC_WS_BASE_URL`.
- workflow does not reach `WAITING_APPROVAL`: confirm deterministic runtime
  defaults and inspect workflow events.
- approval/resume fails: confirm role, status, and duplicate-final-decision
  rules.
- Telegram bridge does not reply: confirm local token, backend availability,
  and that the bridge is not running with `--once`.
- provider smoke fails: keep it optional/manual and do not block deterministic
  release validation unless a live-provider review is explicitly required.

## Sign-Off Checklist

- [ ] Required config validation passed.
- [ ] Required deterministic evaluation commands passed.
- [ ] `bash scripts/ci/all-gates.sh` passed or the reason for skipping/failure
  is recorded.
- [ ] Backend `/health`, `/live`, and `/ready` were checked when services were
  running.
- [ ] Frontend core routes were manually smoke-tested when services were
  running.
- [ ] Workflow run/approval/resume path was verified or documented as not run.
- [ ] Optional Telegram smoke was either completed or explicitly skipped.
- [ ] Optional provider live verification was either completed manually or
  explicitly skipped.
- [ ] No real email was sent.
- [ ] No final quote, stock, delivery, or discount approval claim was made.
- [ ] No secrets or generated sensitive evidence were committed.
- [ ] Remaining limitations are still documented in
  `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md`.
