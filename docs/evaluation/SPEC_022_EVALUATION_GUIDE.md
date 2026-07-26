# SPEC-022 Evaluation Guide

## Purpose

This guide explains the deterministic SPEC-022 Sprint 1 evaluation foundation.
It benchmarks the local Telegram RFQ parser against a fixed English/Vietnamese
dataset without changing product behavior.

The benchmark is intentionally narrow:

- no Telegram network call;
- no backend API call;
- no LLM call;
- no Tavily/provider/web call;
- no database access;
- no workflow mutation;
- no email sending.

## What Is Evaluated

The Sprint 1 benchmark evaluates deterministic parser behavior for:

- supported catalog items;
- supported catalog items with Office 365 / Microsoft 365 add-ons;
- unsupported items;
- mixed supported/unsupported requests;
- missing quantity;
- missing item;
- greeting/help messages;
- benchmark output safety.

Dataset:

```text
scripts/evaluation/telegram_parser_cases.json
```

Runner:

```text
scripts/evaluation/evaluate_telegram_parser.py
```

The dataset covers English and Vietnamese examples for the current demo catalog:

- Standard business laptop
- Business desktop PC
- Office monitor
- Office printer
- Wireless keyboard and mouse combo
- Office 365 / Microsoft 365 add-on

Unsupported examples include projector, server, phone, camera, and router
requests.

## Run The Benchmark

From the repository root:

```bash
python3 scripts/evaluation/evaluate_telegram_parser.py
```

Use an explicit dataset path:

```bash
python3 scripts/evaluation/evaluate_telegram_parser.py \
  --cases scripts/evaluation/telegram_parser_cases.json
```

Write machine-readable metrics:

```bash
python3 scripts/evaluation/evaluate_telegram_parser.py \
  --output-json /tmp/telegram_eval_metrics.json
```

Run the benchmark tests:

```bash
python3 -m unittest scripts.evaluation.test_evaluate_telegram_parser
python3 -m py_compile scripts/evaluation/evaluate_telegram_parser.py
```

## Interpret Metrics

The metrics JSON includes:

- `total_cases`
- `passed_cases`
- `failed_cases`
- `accuracy`
- `category_breakdown`
- `language_breakdown`
- `failures`
- `generated_at`
- `deterministic=true`
- `provider_calls=false`
- `live_network_calls=false`

`accuracy` is benchmark correctness for this fixed parser dataset. It is not a
business accuracy, market pricing, latency, coverage, or user-study metric.

Safety-critical failures are reported separately through `safety_violations`.
Mixed supported/unsupported requests and unsupported item handling should be
treated as safety-sensitive because a false acceptance can create a misleading
workflow.

## Deterministic / No-Key Boundary

The benchmark uses the existing deterministic Telegram parser path with LLM
extraction disabled:

```text
TELEGRAM_LLM_EXTRACTION_ENABLED=false
```

It does not require:

- `TELEGRAM_BOT_TOKEN`;
- backend access token;
- `TAVILY_API_KEY`;
- Ollama;
- Groq, OpenRouter, Gemini, or other provider keys;
- database services;
- Docker services.

Stable demo defaults remain:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
```

## Add A New Case Safely

Before adding a case, review:

- `docs/governance/GOVERNANCE_CHANGE_CHECKLIST.md`
- `.ai/specs/SPEC-018-catalog-expansion/spec.md`
- `.ai/specs/SPEC-021-catalog-governance-provider-policy/spec.md`

Each case must include:

- `id`
- `language`
- `category`
- `input_message`
- `expected_should_create_workflow`
- `expected_normalized_item_name`
- `expected_quantity`
- `expected_requested_addons`
- `expected_safety_outcome`

Rules:

- Use local-demo text only.
- Do not include real customer data.
- Do not include prices.
- Do not include provider keys, tokens, cookies, passwords, or secrets.
- Do not add unsupported items as accepted unless catalog governance and
  parser behavior have already been explicitly updated.
- Treat mixed supported/unsupported requests as blocked unless every requested
  item is supported by the active catalog.
- Keep Office 365 / Microsoft 365 as an add-on, not part of the item name.

## What Is Not Evaluated

Sprint 1 does not evaluate:

- backend workflow APIs;
- database persistence;
- frontend rendering;
- WebSocket timeline behavior;
- real Telegram polling;
- optional Ollama extraction;
- Tavily live provider verification;
- RAG retrieval;
- outbound preview endpoint behavior;
- full end-to-end approval/resume flow.

Those surfaces remain covered by existing tests, demo runbooks, and future
SPEC-022 tasks.

## Future Governance Boundary

Future benchmark automation may become part of local or CI gates only when a
specific task scopes it. CI-safe benchmark work must remain no-key and
no-network. Provider live verification must stay manual-only and must not
require live keys in CI.
