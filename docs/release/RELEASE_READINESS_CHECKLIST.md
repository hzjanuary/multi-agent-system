# Release Readiness Checklist

## Purpose

Use this checklist before tagging, submitting, or presenting the final
Multi-Agent System / Enterprise Multi-Agent OS repository package.

This checklist is documentation and release hygiene only. It does not enable
provider calls, live web research, outbound sending, automatic approval,
automatic resume, or final quotation behavior.

## 1. Stable Deterministic Demo Defaults

Confirm the stable defense/demo path uses no-key deterministic defaults:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
PRICE_RESEARCH_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
TELEGRAM_LLM_EXTRACTION_ENABLED=false
TELEGRAM_SALES_REPLY_ENABLED=false
```

Expected:

- backend workflow runtime remains deterministic;
- `/run` stops at `WAITING_APPROVAL`;
- Manager/Admin approval is required;
- `/resume` is explicit;
- no real email is sent;
- no customer-ready quotation is produced before approval and resume.

## 2. Optional Feature Flags

Optional paths must remain explicit and local/manual:

| Flag | Purpose | Release default |
| --- | --- | --- |
| `TELEGRAM_LLM_EXTRACTION_ENABLED=true` | Local Telegram RFQ extraction through Ollama | `false` |
| `TELEGRAM_SALES_REPLY_ENABLED=true` | Customer-friendly Telegram reply wording | `false` |
| `RAG_ENABLED=true` | RAG demo after explicit knowledge ingestion | `false` |
| `PRICE_RESEARCH_ENABLED=true` | Future reference evidence integration | `false` |
| `TAVILY_API_KEY=<local>` | Manual-only provider live verification | empty |
| `OUTBOUND_COMMUNICATION_ENABLED=true` | Preview loading after approval/resume evidence | `false` |
| `OUTBOUND_SEND_ENABLED=true` | Future send behavior only | `false` |

Do not require real provider keys for release validation.

## 3. Repository Hygiene

Run:

```bash
git status --short
git diff --check
```

Expected:

- only intentional release changes are present;
- no whitespace errors;
- no generated screenshots, PDFs, DOCX files, videos, slides, build outputs, or
  local evidence files are accidentally committed;
- no `docker-compose.override.yml` is tracked;
- no untracked file contains a token, provider key, password, cookie, JWT, or
  real customer data.

## 4. Compose Configuration

Run:

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Expected:

- local Compose config is valid;
- production-demo Compose config is valid with placeholder values;
- no cloud deployment, image push, live provider call, or email send occurs.

## 5. Backend Gate

Run:

```bash
bash scripts/ci/backend-gate.sh
```

Backend gate evidence should include:

- pytest summary;
- Ruff result;
- Black check result;
- MyPy result;
- demo seed dry-run JSON summary;
- knowledge ingestion dry-run JSON summary.

## 6. Frontend Gate

Run:

```bash
bash scripts/ci/frontend-gate.sh
```

Frontend gate evidence should include:

- dependency install result;
- lint result;
- production build result;
- typecheck result;
- test result.

Manual frontend smoke should confirm:

- `/login` renders local-demo account guidance;
- `/demo` explains the Telegram and workflow demo path;
- `/agent-monitor` shows observer workflow choices;
- `/agent-monitor?workflowId=<workflow_id>` shows status, next action, Agent
  Activity, timeline, catalog metadata, reference evidence, and no fake data;
- `/workflows` and `/workflows/<workflow_id>` keep run/approve/resume controls
  visible;
- `/dashboard` points to current demo paths without fake metrics.

## 7. Evaluation Runners

Run:

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

- parser benchmark passes;
- demo safety benchmark passes;
- output is deterministic;
- no backend API, database, Telegram network, LLM/provider, Tavily/live web, or
  email call is required.

## 8. Full Quality Gate

Run:

```bash
bash scripts/ci/all-gates.sh
bash scripts/final/final-quality-gate.sh
```

Expected:

- Compose gate passes;
- backend gate passes;
- frontend gate passes;
- production-demo image build passes;
- whitespace check passes;
- final quality gate remains non-deploying and non-mutating by default.

## 9. Secret And Override Checklist

Confirm tracked files do not include:

- `TELEGRAM_BOT_TOKEN`;
- `TAVILY_API_KEY`;
- Groq, OpenRouter, Gemini, Ollama, or other provider keys;
- backend access tokens;
- JWT production secrets;
- passwords other than documented local-demo credentials;
- cookies;
- Authorization headers;
- raw provider payloads;
- raw prompts;
- embeddings/vector payloads;
- chain-of-thought;
- real customer data.

Confirm local-only files are not committed:

- `.env`;
- frontend/backend local `.env` files;
- `docker-compose.override.yml`;
- screenshots or logs containing secrets.

## 10. Final Approval Checklist

Before release submission, confirm:

- README is the public landing page.
- `docs/release/FINAL_PROJECT_PACKAGE.md` summarizes the final package.
- Demo runbooks match the implemented routes and commands.
- SPEC-001 through SPEC-022 are completed and approved.
- SPEC-023 is ready for closeout review.
- Known limitations are documented.
- Future roadmap is bounded and not claimed as implemented.
- No safety boundary is weakened.

## 11. Explicit No-Send / No-Final-Quotation Boundaries

The release package must continue to state:

- no outbound send endpoint exists;
- approved outbound communication is preview-only;
- no real email is sent;
- Telegram does not perform live price research;
- provider live verification is manual-only;
- reference evidence is not a customer-ready quotation;
- final customer quotation requires Manager/Admin approval and explicit resume;
- no stock, delivery date, discount approval, or unsupported auto-pricing claim
  is made.

## 12. Known Limitations

Release limitations:

- no cloud production deployment automation;
- no Kubernetes/Terraform;
- no enterprise SSO;
- no production secret vault;
- no production email sending;
- no production backup automation;
- no OCR/upload document management UI;
- no provider-management UI;
- no automatic live provider calls;
- deterministic catalog remains demo-focused;
- reference price/evidence foundation is present but not an autonomous pricing
  or final quotation system.
