# Secrets And Provider Keys Runbook

## Purpose

Use this runbook to handle secrets and provider keys for Multi-Agent System /
Enterprise Multi-Agent OS.

This document is operational guidance only. It does not add secret storage,
enable provider calls, enable outbound sending, change runtime defaults, change
Docker/Compose or CI behavior, or introduce final quotation behavior.

## Secret Categories

| Category | Examples | Current policy |
| --- | --- | --- |
| Database credentials | `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Required for deployed state. Use unique environment-specific values outside Git. |
| JWT/auth secrets | `JWT_SECRET_KEY`, token signing settings | Required for auth. Never use example placeholders in production-like runs. |
| MinIO credentials | `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Required for object storage. Replace demo/default values outside Git. |
| Telegram bot token | `TELEGRAM_BOT_TOKEN` | Local demo bridge only. Never commit. Rotate if exposed. |
| Tavily API key | `TAVILY_API_KEY` | Manual-only live provider verification. Not required in CI or stable demo. |
| LLM provider keys | `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` | Optional. Backend runtime remains disabled by default. Never required for deterministic validation. |
| Ollama settings | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, Telegram LLM envs | Local model endpoint settings. Usually not secrets, but must not expose private network details in public evidence if sensitive. |
| Outbound/email provider keys | future Gmail/SMTP/Resend-like values | Future only. No real send behavior or send endpoint exists now. |
| Frontend public values | `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_BASE_URL` | Browser-visible. Must never contain secrets. |

Documented local-demo credentials may appear in demo docs only when clearly
marked local-demo/board-demo. They are not production credentials.

## Secret Storage Policy

- Do not commit real secrets.
- Do not commit local `.env` files.
- Do not commit `docker-compose.override.yml`.
- Do not commit provider keys, Telegram tokens, cookies, Authorization headers,
  JWTs, database passwords, MinIO secrets, raw provider payloads, raw prompts,
  embeddings, vector payloads, chain-of-thought, or real customer data.
- Store production-like secrets in a local ignored env file or a deployment
  environment manager.
- Use least privilege for provider keys and service credentials.
- Use separate values per environment.
- Rotate keys on a defined schedule and immediately after suspected exposure.
- Keep placeholder templates safe and obvious, such as
  `change-me-in-production` or empty strings.
- Never place secrets in `NEXT_PUBLIC_*` values because they are exposed to the
  browser.
- Do not require live provider keys for default CI, deterministic demo, or
  release validation gates.

Recommended local-only files:

```text
.env
backend/.env
frontend/.env.local
docker-compose.override.yml
```

These files must remain ignored/untracked.

## Rotation Schedule

Suggested rotation cadence for production-like environments:

| Secret | Suggested cadence | Rotate immediately when |
| --- | --- | --- |
| JWT secret | Per release or incident-driven, with token invalidation plan | Token signing key may be exposed or auth behavior is suspicious. |
| Database password | Regular operations window | Logs, screenshots, terminal history, or Git expose it. |
| MinIO credentials | Regular operations window | Object storage access may be exposed. |
| Telegram token | Before public demos if exposed, otherwise periodic | Token appears in chat, screenshots, logs, shell history, or Git. |
| Tavily/provider keys | Provider policy or incident-driven | Key appears in logs, CI, screenshots, shell history, issue reports, or Git. |
| Future email provider keys | Before enabling any future send path | Key appears anywhere outside the approved secret store. |

Rotation must include application restart or environment refresh if the running
process reads the secret at startup.

## Leak Response Checklist

If a secret is suspected to have leaked:

1. Stop using the exposed key or token.
2. Revoke or rotate it at the source provider or service.
3. Invalidate affected sessions or tokens when auth secrets are involved.
4. Replace local ignored env values with the new secret.
5. Restart affected local or production-demo services.
6. Search tracked files and recent diffs for the exposed value.
7. If the secret was committed, remove it from current files and treat Git
   history as compromised; rotate the secret even if the current file is fixed.
8. Review logs, screenshots, issue reports, docs, and copied terminal output.
9. Record the incident without including the secret value.
10. Re-run the relevant smoke checks after rotation.

Useful checks:

```bash
git status --short
git diff --check
git ls-files | rg '(^|/)\\.env$|docker-compose\\.override\\.yml'
```

Focused tracked-file review examples:

```bash
git grep -n "TELEGRAM_BOT_TOKEN\\|TAVILY_API_KEY\\|GROQ_API_KEY\\|OPENROUTER_API_KEY\\|GEMINI_API_KEY" || true
git grep -n "Authorization:\\|Bearer \\|api_key\\|password=" || true
```

These grep commands are review aids. They do not prove the repository is
secret-free by themselves.

## Provider Key Policy

### Tavily

- Tavily live verification is manual-only.
- Dry-run mode must remain no-key and no-network.
- Live smoke requires a local `TAVILY_API_KEY` and explicit live confirmation.
- Tavily output is reference evidence only, never a final quote.
- Tavily keys must not be present in CI by default.
- Telegram and workflow runtime must not call Tavily in the stable demo.

### Telegram

- Telegram is a local demo bridge, not a production integration.
- `TELEGRAM_BOT_TOKEN` must be set locally only.
- The bridge must not auto-approve, auto-resume, send real email, or issue a
  final quote.
- Rotate the token if it appears in screenshots, logs, shell history, Git, or
  public chat.

### LLM Providers

- Backend LLM runtime is disabled by default with
  `LLM_RUNTIME_ENABLED=false`.
- `LLM_PROVIDER=fake` remains the stable default.
- Groq, OpenRouter, Gemini, and Ollama settings are optional.
- Real provider keys must not be required for deterministic demo or CI.
- Do not store raw prompts, raw provider payloads, raw model output,
  chain-of-thought, provider keys, or request headers in docs, logs, UI,
  metrics, tests, or workflow state examples.

### Outbound / Email Providers

- Outbound communication is preview-only in the current product.
- `OUTBOUND_SEND_ENABLED=false` must remain the default.
- No outbound send endpoint exists.
- No Gmail/SMTP/Resend production provider integration exists.
- Do not create or store email provider keys until a future approved send spec
  defines provider selection, recipient policy, audit, retries, redaction,
  RBAC, and operator confirmation.

## Redaction Policy

Redact before sharing or committing:

- provider keys;
- Telegram bot tokens;
- JWTs and refresh tokens;
- cookies;
- Authorization headers;
- database passwords;
- MinIO access/secret keys;
- raw provider payloads;
- raw prompts;
- raw model output;
- embeddings and vector payloads;
- chain-of-thought;
- real customer names, emails, phone numbers, addresses, contracts, or RFQs.

### Logs

- Keep `LOG_REDACTION_ENABLED=true` for production-demo and production-like
  use.
- Do not paste full logs into issues or docs without reviewing for secrets.
- Prefer request IDs, timestamps, route names, status codes, and bounded error
  summaries.

### Screenshots

- Do not capture browser devtools storage, cookies, Authorization headers, or
  local env files.
- Redact hostnames or internal URLs if they identify a private environment.
- Demo credentials may appear only when clearly marked local-demo and not
  production.

### Issue Reports

- Include reproduction steps, command names, status codes, request IDs, and
  bounded summaries.
- Do not include full provider responses, full chat history, tokens, cookies,
  passwords, or raw secrets.

### Docs

- Use placeholder values only.
- Do not add "example" keys that resemble real provider keys.
- Keep final quote, stock, delivery, discount approval, and email-sent claims
  out of docs unless a future implementation genuinely supports them.

## CI Policy

- CI must not require live provider keys.
- CI must not call Telegram, Tavily, Groq, OpenRouter, Gemini, Ollama, or email
  providers in default gates.
- CI must keep deterministic/no-key defaults.
- Provider live verification remains manual-only and outside default CI.
- `bash scripts/ci/all-gates.sh` should remain non-secret and deterministic.
- Test fixtures must use fake or mocked provider transports.

Default validation commands:

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
bash scripts/ci/all-gates.sh
```

## Future Production Requirements

Before operating as a real production system, future specs should define:

- managed secret storage;
- environment-specific key provisioning;
- secret rotation automation;
- enterprise SSO;
- production backup and restore automation;
- external observability integration;
- provider rate limits and cost controls;
- outbound email provider policy and audit;
- incident response ownership;
- data retention and deletion policy;
- dependency/security remediation for remaining npm audit findings.

These requirements are not implemented by this runbook.

## Quick Commands And Checks

Repository hygiene:

```bash
git status --short
git diff --check
```

Tracked override check:

```bash
git ls-files docker-compose.override.yml
```

Expected: no output.

Tracked local env check:

```bash
git ls-files | rg '(^|/)\\.env$|\\.env\\.local$'
```

Expected: no real local env files. Tracked `.env.example` files are allowed.

Provider marker review:

```bash
git grep -n "TELEGRAM_BOT_TOKEN\\|TAVILY_API_KEY\\|GROQ_API_KEY\\|OPENROUTER_API_KEY\\|GEMINI_API_KEY" || true
```

This may find safe placeholder references in docs. Review any matches before
release.

Compose config validation:

```bash
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
```

Safe Telegram dry-run:

```bash
python scripts/demo/telegram_inbound_bridge.py --dry-run --once
python scripts/demo/telegram_inbound_bridge.py --dry-run --once --sales-replies
```

Tavily dry-run without key/network:

```bash
python3 scripts/demo/tavily_live_smoke.py \
  --provider tavily \
  --item "Standard business laptop" \
  --region VN \
  --currency VND \
  --dry-run
```
