# Demo Regression Checklist

## Purpose

Use this checklist before a defense demo or evaluator walkthrough. It combines
the SPEC-022 deterministic parser and demo-safety benchmarks with existing
backend, frontend, Telegram, provider, and outbound safety checks.

This checklist does not enable live providers, real email, final quotation, or
new product behavior.

## 1. Repository State

```bash
git status --short
git diff --check
```

Expected:

- only intentional local changes are present;
- no whitespace errors;
- no local `.env` files, provider keys, Telegram tokens, screenshots with
  secrets, or `docker-compose.override.yml` are committed.

## 2. Parser Benchmark

```bash
python3 -m unittest scripts.evaluation.test_evaluate_telegram_parser
python3 -m py_compile scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_telegram_parser.py \
  --output-json /tmp/telegram_eval_metrics.json
```

Expected:

- all deterministic parser benchmark cases pass;
- English and Vietnamese cases are covered;
- supported catalog families are accepted;
- unsupported requests are rejected;
- mixed supported/unsupported requests are blocked;
- output reports no provider calls and no live network calls.

## 3. Backend Gates

## 3. Demo Safety Benchmark

```bash
python3 -m unittest scripts.evaluation.test_evaluate_demo_safety
python3 -m py_compile scripts/evaluation/evaluate_demo_safety.py
python3 scripts/evaluation/evaluate_demo_safety.py
python3 scripts/evaluation/evaluate_demo_safety.py \
  --output-json /tmp/demo_safety_metrics.json
```

Expected:

- workflow lifecycle transition cases pass;
- invalid transitions are blocked;
- outbound preview remains disabled by default;
- outbound preview is available only for completed workflows with explicit
  approval, resume, and preview evidence;
- outbound send remains impossible;
- reference evidence schemas reject unsafe customer-ready flags and sensitive
  markers;
- catalog metadata contains no price, stock, delivery, supplier, or discount
  commitments;
- stable defaults remain no-key and disabled for runtime LLM, RAG, price
  research, outbound preview, and outbound send.

## 4. Backend Gates

For a lightweight pre-demo check:

```bash
bash scripts/ci/backend-gate.sh
```

For focused parser bridge continuity:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
```

Expected:

- backend tests pass;
- parser bridge tests pass;
- no live provider keys are required;
- no final quote, auto-approval, auto-resume, or real email behavior appears.

## 5. Frontend Gates

```bash
bash scripts/ci/frontend-gate.sh
```

Expected:

- lint/build/typecheck/test pass;
- core demo surfaces remain usable:
  - `/login`
  - `/demo`
  - `/agent-monitor`
  - `/workflows`
  - workflow detail
  - `/dashboard`

Manual smoke should confirm:

- current status and next action are visible;
- approval/resume controls are visible when relevant;
- Agent Activity is readable;
- catalog metadata appears only when explicit workflow state contains it;
- reference evidence appears only when explicit workflow state contains it;
- outbound preview remains preview-only.

## 6. Compose Configuration

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Expected:

- local Compose config passes;
- production-demo Compose config passes with placeholder env values;
- no cloud deployment, image push, or live provider call is performed.

## 7. Telegram Dry-Run And Manual Smoke

Dry-run parser/payload check:

```bash
python3 scripts/demo/telegram_inbound_bridge.py --dry-run --once
python3 scripts/demo/telegram_inbound_bridge.py --dry-run --once --sales-replies
```

Manual live Telegram smoke is optional and local-only. If used, follow:

```text
docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md
docs/demo/TELEGRAM_INBOUND_DEMO.md
```

Expected:

- greeting creates no workflow;
- supported catalog RFQ creates a workflow;
- mixed unsupported request creates no workflow;
- auto-run stops at `WAITING_APPROVAL`;
- Manager/Admin approval is still required;
- resume is explicit;
- no real email is sent.

## 8. Provider Live Verification

Provider live verification remains optional and manual-only:

```text
docs/demo/PROVIDER_LIVE_VERIFICATION.md
```

Dry-run checks may be used without keys:

```bash
python3 scripts/demo/tavily_live_smoke.py --dry-run
```

Do not run live provider verification unless:

- a local provider key is intentionally configured;
- the command requires explicit live confirmation;
- output will be reviewed and redacted;
- the result is understood as reference evidence only.

Provider live smoke is not part of CI and is not required for the stable demo.

## 9. Outbound Preview Boundary

Before demo:

- confirm `OUTBOUND_SEND_ENABLED=false`;
- confirm no send button is shown;
- confirm outbound preview is available only after approval and resume;
- confirm preview text is not shown as real sent email.

Expected:

- preview-only behavior;
- no SMTP/Gmail/provider call;
- no customer send;
- no email-sent claim.

## 10. Safety Review

Confirm the demo does not claim:

- final quotation before approval/resume;
- stock availability;
- delivery date;
- discount approval;
- real email sent;
- auto-approval;
- auto-resume;
- live market price proof unless manually verified and labeled reference-only.

Confirm outputs do not expose:

- Telegram tokens;
- backend access tokens;
- provider API keys;
- passwords;
- cookies;
- raw prompts;
- raw provider payloads;
- embeddings or vector payloads;
- chain-of-thought;
- real customer data.

## 11. Full Gate

When time allows:

```bash
bash scripts/ci/all-gates.sh
```

Expected:

- compose gate passes;
- backend gate passes;
- frontend gate passes;
- production-demo image build passes;
- whitespace check passes.
