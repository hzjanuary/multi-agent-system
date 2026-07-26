# SPEC-019 - Provider Live Verification

## Status

Planned / ready for review before implementation

## Product Objective

Add manual-only live verification for optional external provider adapters,
starting with Tavily, while keeping CI mocked/no-key and keeping
Telegram/workflows deterministic by default.

SPEC-019 is about proving optional provider configuration safely in a private
local environment. It does not enable live provider calls in Telegram, workflow
runtime, CI, or the stable demo.

## Current Dependencies

- SPEC-016 price research schemas, service shell, fake/manual/RAG providers,
  Tavily adapter, safe Telegram evidence rendering, and frontend evidence
  panels.
- Existing Tavily settings:
  - `TAVILY_API_KEY`
  - `TAVILY_SEARCH_URL`
  - `TAVILY_MAX_RESULTS`
  - `TAVILY_INCLUDE_RAW_CONTENT`
  - `TAVILY_SEARCH_DEPTH`
- Existing `PRICE_RESEARCH_ENABLED=false` default.
- Existing backend test patterns for injected transports and no-network CI.

## Target Architecture

```text
Manual operator
  -> explicit smoke command with --confirm-live-provider
  -> local environment key validation
  -> selected provider adapter
  -> bounded provider request
  -> normalized reference evidence JSON
  -> redacted console/file output
  -> no workflow / Telegram side effect
```

### Manual Live Smoke Script / Command Design

The live smoke path should be an explicit local command, not a test and not an
application startup behavior. It should require a confirmation flag such as
`--confirm-live-provider`.

The command should:

- require `TAVILY_API_KEY` only when the Tavily provider is selected
- construct a safe reference price request for a demo catalog item
- call the provider through the SPEC-016 service/provider boundary
- print bounded JSON summaries only
- return non-zero on missing key, timeout, provider error, or unsafe output
- avoid workflow creation, Telegram replies, and frontend behavior

### Provider Key Handling

Provider keys must be local environment variables only. The smoke command must
not print keys, log Authorization headers, or write raw provider payloads.

### No-Key CI Boundary

CI must continue to use mocked/injected transports and no-key tests. Automated
tests must not call Tavily or any external provider.

### Safe Output JSON Contract

Live smoke output should use the existing provider-independent result shape:

- provider
- evidence label
- sources
- reference prices only when explicit structured data exists
- confidence
- retrieved timestamp
- warnings
- `is_final_quote=false`

Raw response bodies, raw HTML, prompt text, headers, secrets, cookies, and
tokens must not be printed or stored.

### Timeout / Error Handling

Provider errors must be safe:

- missing key: safe configuration error
- timeout: safe timeout message
- non-2xx: safe status-only message
- invalid JSON: safe parse message
- policy/terms concern: fail closed with operator guidance

Exception messages must not include raw response bodies or API keys.

### Evidence-Only Behavior

Live provider output is reference evidence for internal review only. It must
not become a customer quotation, stock promise, delivery promise, discount
approval, or approval decision.

### No Telegram / Web Automation Boundary

The live smoke command must not:

- run Telegram polling
- create workflows
- call `/run`
- approve or resume workflows
- automate a browser
- scrape arbitrary websites

### Audit / Log Redaction

Any command logs must redact:

- API keys
- Authorization headers
- cookies
- request tokens
- provider raw payloads
- customer personal data

### Provider Policy Verification Checklist

Before enabling a live provider command for operator use, docs must include:

- provider terms reviewed
- endpoint documented
- authentication documented
- rate limits checked
- data retention/privacy checked
- output citation quality reviewed
- no scraping beyond provider API
- no CI/live key requirement

## User Stories

### Operator Runs Tavily Smoke Locally

As a developer/operator, I want to verify Tavily configuration with an explicit
manual command so I can confirm the adapter works without changing the stable
demo.

### CI Remains No-Key

As a maintainer, I want all provider tests to use mocks/injected transports so
CI never requires a real Tavily key or live network.

### Evidence Is Safe To Review

As a Manager, I want live provider output to be normalized into bounded
reference evidence so I can review sources without mistaking them for final
quotes.

### Provider Failure Is Safe

As a demo operator, I want missing keys, timeouts, and provider errors to fail
closed with safe messages and no leaked secrets.

## Acceptance Criteria

- Tavily live verification is manual-only and requires explicit confirmation.
- CI tests require no provider key and perform no live web calls.
- `PRICE_RESEARCH_ENABLED=false` remains the default.
- Telegram and workflows do not call live providers automatically.
- Output JSON is bounded and matches the reference evidence contract.
- Missing key, timeout, non-2xx, invalid JSON, and malformed response cases are
  handled safely.
- No price is inferred from prose.
- No final quote, stock, delivery, discount, approval, or email-sent claim is
  introduced.
- No provider key, raw payload, raw HTML, Authorization header, prompt, cookie,
  token, or secret is logged.

## Safety Boundaries

- No real provider key in CI.
- No committed secrets.
- No live web calls in automated tests.
- No Telegram automatic live provider calls.
- No workflow automatic provider calls unless a later explicit spec enables it.
- No scraping arbitrary websites.
- No price inference from prose.
- No final quote.
- No stock or delivery promise.
- No auto-approval.
- No auto-resume.

## Feature Flags And Configuration

- `PROVIDER_LIVE_SMOKE_ENABLED=false`
- `TAVILY_API_KEY`, set locally only for manual smoke
- `TAVILY_SEARCH_URL`
- `PRICE_RESEARCH_PROVIDER=tavily`, only when explicitly configured
- `PRICE_RESEARCH_ENABLED=false`, remains the stable default
- `PRICE_RESEARCH_TIMEOUT_SECONDS`
- `PRICE_RESEARCH_MAX_SOURCES`

The exact implementation may use CLI flags rather than runtime feature flags,
but the safety defaults must remain no-key and non-live.

## Non-Goals

- Telegram integration with live providers.
- Workflow runtime integration with live providers.
- CI live provider calls.
- Browser automation or scraping.
- Autonomous final quotes.
- Price extraction from snippets/prose.
- Provider-management UI.
- Caching/rate-limit production service unless a later task scopes it.
- Storing provider payloads in the database.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| A live key leaks into logs or commits | Use environment-only keys, redaction tests, and docs warning against committed secrets. |
| CI accidentally calls Tavily | Keep live smoke behind manual confirmation and mocked tests only. |
| Search snippets are mistaken for prices | Do not infer prices from prose; label sources as reference evidence. |
| Provider policy changes | Maintain a policy checklist and fail closed until reviewed. |
| Operator enables provider in demo unexpectedly | Keep stable demo docs on fake/no-key defaults and isolate smoke command from runtime. |

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
```

Implementation validation should include:

```bash
python3 scripts/demo/provider_live_smoke.py --help
python3 scripts/demo/provider_live_smoke.py --provider tavily
docker compose run --rm backend-test pytest app/tests/test_price_research_tavily_provider.py -q
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
bash scripts/ci/all-gates.sh
git diff --check
```

Manual live validation, only with a private local key:

```bash
TAVILY_API_KEY="<set locally>" python3 scripts/demo/provider_live_smoke.py --provider tavily --confirm-live-provider
```

## Suggested Task Order

1. TASK 019.1 - Live Verification Spec And Policy Checklist
2. TASK 019.2 - Manual Tavily Smoke Script With Explicit Confirmation
3. TASK 019.3 - Safe JSON Output And Redaction Tests
4. TASK 019.4 - Docs For Local Provider Verification
5. TASK 019.5 - Final Validation And Docs
