# Provider Live Verification

## Purpose

This guide documents the manual-only live smoke path for optional external
provider adapters. Tavily is the first supported live provider check.

Provider live verification is not part of CI, not part of the stable defense
demo, and not connected to Telegram, workflows, frontend pages, approval,
resume, or email. It only verifies that a local operator can call the Tavily
adapter and receive bounded reference evidence JSON.

Operational provider evidence policy and future-change checklists live under
`docs/governance/`.

## Safety Rules

- Run live verification manually only.
- Never commit `TAVILY_API_KEY`.
- Do not paste provider keys into docs, screenshots, shell history, or chat.
- Dry-run mode is no-key and no-network.
- Live mode requires both `TAVILY_API_KEY` and `--confirm-live-provider`.
- Output is reference evidence only, not a customer quotation.
- The command does not create workflows, run workflows, approve, resume, poll
  Telegram, call frontend routes, send email, or write database rows.
- The command must not print API keys, Authorization headers, raw provider
  payloads, raw HTML, cookies, tokens, prompts, secrets, or customer personal
  data.

## Dry Run

Dry-run validates the request shape and safety notes without a provider key or
network call:

```bash
python3 scripts/demo/tavily_live_smoke.py \
  --provider tavily \
  --item "Standard business laptop" \
  --region VN \
  --currency VND \
  --dry-run
```

Expected output is bounded JSON with:

```json
{
  "status": "dry_run",
  "dry_run": true,
  "provider_call": false
}
```

## Live Smoke

Run live smoke only with a private local key:

```bash
export TAVILY_API_KEY="<set locally>"

python3 scripts/demo/tavily_live_smoke.py \
  --provider tavily \
  --item "Standard business laptop" \
  --region VN \
  --currency VND \
  --confirm-live-provider \
  --pretty
```

Confirmed live mode lazy-loads the exact production Tavily adapter
(`backend/app/price_research/web_provider.py`), so run it from a Python
environment with backend dependencies installed. `--help` and `--dry-run`
remain dependency-light and do not import backend packages.

Optional flags:

```bash
--quantity 20
--requested-addon office_365
--timeout-seconds 30
--max-results 5
```

The adapter fixes the search endpoint (`https://api.tavily.com/search`), search
depth (`basic`), and does not request raw content; these are production adapter
settings, not smoke-configurable. `--max-results` is bounded to 1..5 to match
the adapter cap.

The smoke test suite (`scripts/demo/test_tavily_live_smoke.py`) runs on the host
without backend dependencies; the live-path wiring test (real adapter with a
mocked transport, no network or key) requires backend dependencies and is
skipped where they are absent.

The output includes a safe request summary, bounded sources, warnings, and
`is_final_quote=false`. Tavily search snippets are treated as external web
reference evidence only. The smoke command does not infer prices from prose.

## Safe Failure Modes

Missing confirmation:

```bash
python3 scripts/demo/tavily_live_smoke.py --provider tavily --item "Standard business laptop"
```

returns a nonzero exit code with a safe JSON error.

Missing key:

```bash
unset TAVILY_API_KEY
python3 scripts/demo/tavily_live_smoke.py \
  --provider tavily \
  --item "Standard business laptop" \
  --confirm-live-provider
```

returns a nonzero exit code with a safe JSON error and does not call Tavily.

Unsupported provider names return a nonzero exit code. Provider errors are
reported with bounded messages only; raw response bodies and keys are not
printed.

## Provider Policy Checklist

Before using a live provider during operator testing, confirm:

- provider terms and acceptable use were reviewed;
- endpoint and authentication method are documented;
- rate limits are understood;
- data retention and privacy posture are acceptable for demo queries;
- output source quality was reviewed manually;
- no arbitrary website scraping is performed outside the provider API;
- no CI job requires a live provider key.

## Key Leak Response

If a provider key appears in a screenshot, shell history, commit, terminal log,
or chat message:

1. Revoke or rotate the key immediately in the provider dashboard.
2. Remove the leaked material from the local workspace.
3. Do not reuse the exposed key.
4. Re-run the smoke command only with the rotated key in a local environment
   variable.

## Stable Demo Boundary

The stable demo remains deterministic and no-key:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
```

Telegram and workflows still do not call Tavily or any live price research
provider automatically. Manager/Admin approval remains the boundary before any
customer-ready quote.
