# Telegram Inbound Demo Bridge

## Purpose

The Telegram inbound bridge lets a customer actor send a procurement request
from a phone during the local graduation demo. The local script polls Telegram,
parses a bounded English or Vietnamese laptop quotation request, creates a
procurement workflow through the existing backend API, optionally runs it to
`WAITING_APPROVAL`, and replies with workflow and Agent Monitor links.

This is a local demo bridge. It is not a production Telegram webhook
integration.

## Why Polling

Polling with Telegram `getUpdates` keeps the demo local and avoids public
webhook hosting, TLS certificates, tunnel services, reverse proxy changes, new
backend routes, or database changes. The bridge is a separate local operator
script under `scripts/demo/` and uses only existing backend endpoints.

## Safety Boundaries

- Never commit `TELEGRAM_BOT_TOKEN`.
- The script does not print the Telegram bot token.
- The script does not print backend access tokens or passwords.
- The script does not auto-approve.
- The script does not auto-resume.
- The script does not send real customer email.
- The script does not fabricate workflow events, agent activity, or RAG
  evidence.
- The workflow created by the default auto-run path must still stop at
  `WAITING_APPROVAL`.
- Real LLM providers are not required.

## Create A Telegram Bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Choose a display name and username for the local demo bot.
4. Copy the bot token into a local shell environment variable only.
5. Do not paste the token into docs, commits, screenshots, or chat messages.

## Required Environment

```bash
export TELEGRAM_BOT_TOKEN="<set locally from BotFather>"
export BACKEND_API_BASE_URL="http://localhost:8000/api/v1"
export FRONTEND_BASE_URL="http://localhost:3000"
export DEMO_MANAGER_EMAIL="manager@example.test"
export DEMO_MANAGER_PASSWORD="DemoPassword123!"
export TELEGRAM_POLL_INTERVAL_SECONDS="2"
```

Windows PowerShell equivalent:

```powershell
$env:TELEGRAM_BOT_TOKEN = "<set locally from BotFather>"
$env:BACKEND_API_BASE_URL = "http://localhost:8000/api/v1"
$env:FRONTEND_BASE_URL = "http://localhost:3000"
$env:DEMO_MANAGER_EMAIL = "manager@example.test"
$env:DEMO_MANAGER_PASSWORD = "DemoPassword123!"
$env:TELEGRAM_POLL_INTERVAL_SECONDS = "2"
```

The Manager credentials are local-demo/board-demo only.

## Local Startup

Run the normal local demo preparation first:

```bash
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

Start the Telegram bridge from the repository root:

```bash
python scripts/demo/telegram_inbound_bridge.py
```

For a single polling pass:

```bash
python scripts/demo/telegram_inbound_bridge.py --once
```

For a parser/payload dry run that does not require a Telegram token:

```bash
python scripts/demo/telegram_inbound_bridge.py --dry-run --once
```

To create but not run the workflow automatically:

```bash
python scripts/demo/telegram_inbound_bridge.py --no-auto-run
```

To restrict processing to one chat:

```bash
python scripts/demo/telegram_inbound_bridge.py --allowed-chat-id "<telegram-chat-id>"
```

## Example Customer Messages

Primary board-demo message:

```text
We would like to purchase 50 standard business laptops for a new operations team. We signed a master agreement in May 2026. Please provide your best quotation with the applicable discount.
```

Supported simple variations:

```text
50 laptops
purchase 20 laptops
buy 10 laptops
quote for 5 business laptops
quotation for 7 standard business laptops
```

Supported Vietnamese variations:

```text
tôi muốn mua 50 cái máy tính xách tay doanh nhân tiêu chuẩn có cài sẵn office 365
tôi muốn mua 50 máy tính xách tay
cần báo giá 50 laptop
báo giá cho 30 máy tính xách tay
mua 20 laptop cho phòng kinh doanh
cần 15 laptop doanh nhân
50 máy tính xách tay có cài office 365
```

The deterministic parser normalizes `laptop`, `máy tính xách tay`,
`máy tính xách tay doanh nhân`, `laptop doanh nhân`, and
`máy tính xách tay tiêu chuẩn` to:

```text
Standard business laptop
```

It also detects these optional add-on phrases:

```text
office 365
microsoft 365
cài sẵn office
có office
```

Detected Office phrases are stored as `office_365` in the workflow request and
metadata.

Greeting-only messages such as `xin chào`, `hello`, and `hi` do not create a
workflow. The bridge replies with English and Vietnamese examples.

If the parser cannot identify both quantity and item, it replies:

```text
Please include quantity and item.
English example: quote for 50 standard business laptops.
Ví dụ tiếng Việt: cần báo giá 50 máy tính xách tay.
```

If a quantity is present but the item is unsupported, the bridge still refuses
to create a workflow silently. Ask the customer actor to use a supported laptop
phrase such as `laptop` or `máy tính xách tay`.

## Board Demo Script

1. Start backend infrastructure.
2. Run migrations and demo seed explicitly.
3. Start backend and frontend.
4. Open `/agent-monitor` in the browser.
5. Start `python scripts/demo/telegram_inbound_bridge.py`.
6. Send the primary customer message from a phone to the demo bot.
7. The bridge creates a workflow and, by default, calls `/run`.
8. The Telegram reply includes:
   - parsed request summary
   - detected options such as Office 365 when present
   - workflow id
   - status
   - workflow detail URL
   - Agent Monitor URL
   - human approval required note
9. Open `/agent-monitor?workflowId=<workflow-id>`.
10. Confirm Agent Activity and timeline events are visible.
11. Open the workflow detail link.
12. Approve as Manager/Admin.
13. Resume the workflow.
14. Confirm the workflow reaches `COMPLETED`.

## Backend APIs Used

The bridge uses existing backend APIs only:

```text
POST /api/v1/auth/login
POST /api/v1/workflows
POST /api/v1/workflows/{workflow_id}/run
```

It does not call approval or resume endpoints. Those remain human UI actions.

The workflow payload stores safe bounded metadata:

```text
source=telegram
language=en or vi
requested_addons=["office_365"] when detected
demo=true
parser_version=telegram-demo-parser-v2
```

The original Telegram text is preserved in the workflow request as `raw_text`
and `request_text`.

## Troubleshooting

### Invalid Telegram Token

The local console reports a bounded Telegram polling error. Re-copy the token
from BotFather into `TELEGRAM_BOT_TOKEN`. Do not print or commit the token.

### Backend Unavailable

Confirm:

```bash
docker-compose ps backend postgres redis qdrant minio
curl http://localhost:8000/health
```

The bridge expects `BACKEND_API_BASE_URL=http://localhost:8000/api/v1` unless
overridden.

### Login Fails

Run the demo seed explicitly:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

Confirm `DEMO_MANAGER_EMAIL` and `DEMO_MANAGER_PASSWORD` match the local-demo
credentials.

### Workflow Create Fails

Use the Manager or Admin demo account. Sales can create workflows in the normal
demo, but this bridge defaults to Manager because it also needs `/run` access
when auto-run is enabled.

### Run Fails After Workflow Creation

The Telegram reply reports the safe failure and includes the workflow URL when
available. Open the workflow detail page and inspect status/events. The bridge
does not retry with alternate credentials and does not resume.

### Agent Monitor Does Not Update

Open the workflow-specific URL from the Telegram reply:

```text
http://localhost:3000/agent-monitor?workflowId=<workflow-id>
```

Sign in to the frontend if the dashboard session is missing. The monitor uses
the existing workflow APIs and WebSocket timeline.

### Parser Rejects The Message

Send a message with a quantity and item:

```text
quote for 50 standard business laptops
cần báo giá 50 máy tính xách tay
```

The parser is intentionally deterministic for the board demo and does not try
to interpret arbitrary procurement text.

## Limitations

- Local polling only; no webhook endpoint.
- In-memory Telegram offset only; restart can re-read recent unconfirmed
  updates depending on Telegram offset state.
- Laptop quotation parser only, with English and Vietnamese demo phrases.
- Multi-item parsing is not implemented.
- No production secret storage.
- No Telegram user identity binding to backend users.
- No auto-approval or auto-resume.
- No customer email sending.
- No real LLM provider required.
