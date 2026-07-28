# Demo Commands

## Purpose

Copy-ready commands for the final local demo and release validation. Run from
the repository root unless a section says otherwise.

Commands in this file use existing repository scripts, Compose files, and docs.
They do not enable live provider calls, outbound send, auto-approval,
auto-resume, real email, or final quotation behavior.

## Local Infrastructure

Start local infrastructure services:

```bash
docker-compose up -d postgres redis qdrant minio
```

Run migrations:

```bash
docker-compose run --rm backend-test alembic upgrade head
```

Seed local-demo users and workflows explicitly:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

Optional RAG demo knowledge ingestion:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Start backend:

```bash
docker-compose up --build backend
```

## Backend Health Checks

With backend running:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/live
curl http://localhost:8000/ready
```

`/ready` may fail when dependencies are not ready. Use deployment and
troubleshooting docs for readiness investigation.

## Frontend Local Run

Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000/demo
```

Return to repository root:

```bash
cd ..
```

## Telegram Bridge Dry Run

No token required:

```bash
python scripts/demo/telegram_inbound_bridge.py --dry-run --once
python scripts/demo/telegram_inbound_bridge.py --dry-run --once --sales-replies
```

## Telegram Manual Local Run

Set the token locally only:

```bash
export TELEGRAM_BOT_TOKEN="<set locally from BotFather>"
```

Stable deterministic parser mode:

```bash
python scripts/demo/telegram_inbound_bridge.py
```

Optional local Ollama extraction plus sales-style replies:

```bash
export TELEGRAM_LLM_EXTRACTION_ENABLED=true
export TELEGRAM_LLM_BASE_URL=http://localhost:11434
export TELEGRAM_LLM_MODEL=qwen2.5:7b-instruct-q4_K_M
export TELEGRAM_SALES_REPLY_ENABLED=true

python scripts/demo/telegram_inbound_bridge.py --llm-extraction --sales-replies
```

This bridge does not auto-approve, does not auto-resume, does not call Tavily,
does not run live price research, and does not send real email.

## Ollama Local Preparation

Optional, only for Telegram RFQ extraction:

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama serve
```

The backend workflow runtime remains deterministic when:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

## Evaluation Runners

Telegram parser benchmark:

```bash
python3 -m unittest scripts.evaluation.test_evaluate_telegram_parser
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_telegram_parser.py \
  --output-json /tmp/telegram_eval_metrics.json
```

Demo safety benchmark:

```bash
python3 -m unittest scripts.evaluation.test_evaluate_demo_safety
python3 scripts/evaluation/evaluate_demo_safety.py
python3 scripts/evaluation/evaluate_demo_safety.py \
  --output-json /tmp/demo_safety_metrics.json
```

## Provider Dry Run

Tavily dry-run uses no key and no network call:

```bash
python3 scripts/demo/tavily_live_smoke.py \
  --provider tavily \
  --item "Standard business laptop" \
  --region VN \
  --currency VND \
  --dry-run
```

Live provider verification is manual-only and requires
`--confirm-live-provider`; do not run it as part of CI or stable release
validation.

## Compose Validation

Local Compose config:

```bash
docker compose config
```

Production-demo Compose config:

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Production-demo application image build:

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example build backend frontend
```

## Quality Gates

```bash
bash scripts/ci/compose-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
bash scripts/final/final-quality-gate.sh
```

`final-quality-gate.sh` is non-deploying and non-mutating by default.

## E2E Validation Help

Help output:

```bash
bash scripts/final/e2e-demo-validation.sh --help
```

Full mutating E2E validation requires explicit local-demo confirmation:

```bash
bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready
```

Run it only when local services are intentionally prepared.

## Production-Demo Smoke Help

```bash
bash scripts/deployment/smoke-prod-demo.sh --help
```

Optional startup smoke:

```bash
bash scripts/deployment/smoke-prod-demo.sh --start --include-ready
```

## Safe Shutdown

Stop local services without deleting volumes:

```bash
docker-compose down
```

Stop production-demo services without deleting volumes:

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example down
```

Do not delete volumes during a demo unless a separate recovery task explicitly
requires it.
