# Final Live Demo Runbook

## Purpose

This runbook freezes the verified live defense path for Multi-Agent System /
Enterprise Multi-Agent OS. It combines the stable deterministic backend runtime
with the optional Telegram inbound bridge, local Ollama RFQ extraction, and
sales-style Telegram replies.

The goal is a reliable live story:

```text
Telegram customer message
  -> local Telegram bridge
  -> deterministic parser and normalizer
  -> backend workflow create
  -> /run to WAITING_APPROVAL
  -> Agent Monitor
  -> Manager approval
  -> /resume
  -> COMPLETED
```

No final quote, price, stock, delivery date, automatic approval, automatic
resume, or real email is claimed.

## Stable Backend Mode

Use the deterministic backend runtime for the defense demo:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

This keeps the workflow reproducible. Backend stages still execute the
deterministic procurement runtime and stop at `WAITING_APPROVAL`. Real LLM
providers remain optional and feature-flagged, but they are not required for
the final defense path.

Optional provider live checks, such as Tavily adapter verification, are
documented separately in `docs/demo/PROVIDER_LIVE_VERIFICATION.md`. They are
manual-only, not part of CI, and not part of the stable Telegram/workflow demo
path.

## Optional Telegram LLM Extraction Mode

Ollama is optional and runs on the host machine. In this demo path it is used
only by the local Telegram bridge to extract natural Vietnamese RFQ intent. It
is not used by the backend runtime when `LLM_RUNTIME_ENABLED=false`.

Bridge settings:

```text
TELEGRAM_LLM_EXTRACTION_ENABLED=true
TELEGRAM_LLM_BASE_URL=http://localhost:11434
TELEGRAM_LLM_MODEL=qwen2.5:7b-instruct-q4_K_M
TELEGRAM_SALES_REPLY_ENABLED=true
```

The bridge still runs deterministic normalization after LLM extraction:

- laptop aliases become `Standard business laptop`
- Office 365 aliases become `office_365`
- quantity must be a positive integer
- unsupported mixed items are blocked
- raw prompts and provider payloads are not stored or printed

## Repository Hygiene

`docker-compose.override.yml` is ignored because it may contain local machine
settings. Use the safe placeholder template instead:

```bash
cp docker-compose.override.example.yml docker-compose.override.yml
```

PowerShell:

```powershell
Copy-Item docker-compose.override.example.yml docker-compose.override.yml
```

Do not commit local override files, Telegram tokens, provider API keys, copied
shell history, screenshots with secrets, or local `.env` files.

## Startup - Git Bash

From the repository root:

```bash
export LLM_PROVIDER=fake
export LLM_RUNTIME_ENABLED=false

docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
docker-compose up --build backend
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Start Ollama on the host:

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama serve
```

Start the Telegram bridge in another terminal:

```bash
export TELEGRAM_BOT_TOKEN="<set locally from BotFather>"
export TELEGRAM_LLM_EXTRACTION_ENABLED=true
export TELEGRAM_LLM_BASE_URL=http://localhost:11434
export TELEGRAM_LLM_MODEL=qwen2.5:7b-instruct-q4_K_M
export TELEGRAM_SALES_REPLY_ENABLED=true

python scripts/demo/telegram_inbound_bridge.py --llm-extraction --sales-replies
```

## Startup - Windows PowerShell

From the repository root:

```powershell
$env:LLM_PROVIDER = "fake"
$env:LLM_RUNTIME_ENABLED = "false"

docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
docker-compose up --build backend
```

Start the frontend in another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Start Ollama on the host:

```powershell
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama serve
```

Start the Telegram bridge in another terminal:

```powershell
$env:TELEGRAM_BOT_TOKEN = "<set locally from BotFather>"
$env:TELEGRAM_LLM_EXTRACTION_ENABLED = "true"
$env:TELEGRAM_LLM_BASE_URL = "http://localhost:11434"
$env:TELEGRAM_LLM_MODEL = "qwen2.5:7b-instruct-q4_K_M"
$env:TELEGRAM_SALES_REPLY_ENABLED = "true"

python scripts/demo/telegram_inbound_bridge.py --llm-extraction --sales-replies
```

## Final Demo Script

### 1. Greeting

Send:

```text
xin chào
```

Expected:

- sales-style greeting/help
- no workflow created
- no backend workflow mutation

### 2. Mixed Unsupported Item Safety

Send:

```text
báo giá 20 cái laptop và 5 cái máy in hp
```

Expected:

- no workflow created
- reply mentions the supported laptop request
- reply mentions `5 x máy in HP` as unsupported
- reply explains the demo catalog supports laptop quotation only
- reply asks for a laptop-only RFQ or catalog/pricing extension

### 3. Laptop-Only RFQ

Send:

```text
vậy lấy trước cho tôi 20 cái laptop tiêu chuẩn kèm sẵn office 365
```

Expected:

- workflow created
- bridge auto-runs `/run`
- backend status reaches `WAITING_APPROVAL`
- reply includes workflow URL
- reply includes Agent Monitor URL
- reply states human approval is required
- no final quote, price, stock, delivery date, or email claim

### 4. Agent Monitor

Open the Agent Monitor URL from the Telegram reply.

Expected:

- pre-approval deterministic stages are complete
- Human Approval is waiting
- Email Preview is blocked until approval
- timeline/events show bounded operational evidence
- no chain-of-thought, raw prompts, raw provider payloads, embeddings, tokens,
  or secrets are shown

### 5. Manager Approval

Open the workflow detail URL and approve as Manager/Admin.

Expected:

- approval history records the decision
- workflow becomes `APPROVED`
- no automatic resume occurs

### 6. Resume

Click Resume workflow in the web UI.

Expected:

- workflow reaches `COMPLETED`
- email preview is generated
- no real email is sent

## Defense Explanation

Use this concise explanation during Q&A:

- Telegram is the front-office sales interaction layer for the live demo.
- Ollama helps extract natural Vietnamese RFQ intent locally.
- The bridge never trusts raw LLM output directly; deterministic normalization
  validates quantity, canonical item name, add-ons, and unsupported items.
- The backend runtime remains deterministic with `LLM_PROVIDER=fake` and
  `LLM_RUNTIME_ENABLED=false`, making the defense demo reproducible.
- Agent Monitor shows bounded operational evidence from workflow state and
  persisted events, not hidden reasoning.
- Human approval prevents autonomous final quote issuance.
- The mixed unsupported item guard prevents silent item dropping and avoids
  pretending the demo has printer catalog/pricing support.

## Safety Checklist

Before the live demo:

- `TELEGRAM_BOT_TOKEN` is set only in the local shell.
- No Telegram token is committed.
- No provider API keys are committed.
- `docker-compose.override.yml` is ignored and untracked.
- Backend runtime uses `LLM_PROVIDER=fake`.
- Backend runtime uses `LLM_RUNTIME_ENABLED=false`.
- Demo seed has been run explicitly if the database was reset.
- Telegram bridge is started with `--llm-extraction --sales-replies`.

During and after the demo:

- Do not show shell history containing tokens.
- Do not show raw provider payloads or prompts.
- Do not claim a final price before approval.
- Do not claim stock availability.
- Do not promise delivery dates.
- Do not claim real email was sent.
- Do not auto-approve.
- Do not auto-resume.
- Rotate the Telegram token if it appeared in screenshots, logs, chat, or a
  recording.

## Troubleshooting

### `/run` Returns HTTP 500 When Backend LLM Runtime Is Enabled

Use stable defense mode:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

Restart the backend after changing the environment.

### Telegram Bridge Does Not Reply

- Restart the bridge.
- Confirm `TELEGRAM_BOT_TOKEN` is set in the same terminal.
- Do not use `--once` for the live demo.
- Confirm the bot is not restricted by `--allowed-chat-id`.

### Ollama Extraction Does Not Work

Check:

```bash
ollama list
```

Confirm the model is pulled and the bridge points to:

```text
TELEGRAM_LLM_BASE_URL=http://localhost:11434
```

If Ollama is unavailable, the deterministic fallback still handles supported
laptop RFQs.

### Workflow Created But Not Auto-Run

Open the workflow URL from the Telegram reply. Click Run workflow after the
backend is ready. The workflow should stop at `WAITING_APPROVAL`.

### Mixed Printer/Laptop Request Creates Workflow

Restart the Telegram bridge so it loads the latest code. The expected behavior
is a clarification reply and no workflow creation.

## Validation Commands

Use these before defense:

```bash
git status --short
git ls-files docker-compose.override.yml
python scripts/demo/telegram_inbound_bridge.py --help
python scripts/demo/telegram_inbound_bridge.py --dry-run --once --sales-replies
python -m unittest scripts.demo.test_telegram_inbound_bridge
docker-compose config
docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
docker-compose run --rm backend-test pytest -q
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
git diff --check
```

`git ls-files docker-compose.override.yml` should print no tracked output.
