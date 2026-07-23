# Local LLM Demo Guide

This guide explains how the LLM provider abstraction interacts with the local
procurement demo. The default board demo should remain deterministic unless you
explicitly enable LLM runtime mode.

## Recommended Board Demo Mode

Use the safe default settings:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

This mode requires no API keys and keeps the existing demo stable:

- seeded workflows are deterministic
- `/run` uses deterministic runtime nodes
- no LLM provider network calls occur
- the workflow still stops at `WAITING_APPROVAL`
- live event streaming and persisted event backlog work as before

## Standard Demo Startup

Run from the repository root:

```bash
docker-compose config
docker-compose up -d postgres redis qdrant minio
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
docker-compose up --build backend
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000
```

Use the board walkthrough in `docs/demo/DEMO_RUNBOOK.md`.

## Optional Real-Provider Experiment

Real-provider mode is for local experimentation only. It is not required for
the deterministic board demo and may produce variable results.

1. Copy `backend/.env.example` to a local `.env`.
2. Set the provider, model, and key variables for the provider you want.
3. Explicitly enable the runtime adapter:

```text
LLM_RUNTIME_ENABLED=true
```

4. Restart the backend so settings are reloaded.
5. Run a `CREATED` workflow through the existing `/run` path from the frontend.

The `/run` API contract remains the same. Runtime still stops at
`WAITING_APPROVAL`. Human approval and explicit `/resume` continuation are
handled by SPEC-012, while customer-facing email sending remains deferred.

## Example Local Configurations

Fake provider with LLM runtime adapter enabled:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=true
LLM_MODEL=fake-deterministic-model
```

Groq:

```text
LLM_PROVIDER=groq
LLM_RUNTIME_ENABLED=true
GROQ_API_KEY=<local key>
GROQ_MODEL=<model name>
```

OpenRouter:

```text
LLM_PROVIDER=openrouter
LLM_RUNTIME_ENABLED=true
OPENROUTER_API_KEY=<local key>
OPENROUTER_MODEL=<model name>
```

Ollama:

```text
LLM_PROVIDER=ollama
LLM_RUNTIME_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=<local model name>
```

Gemini:

```text
LLM_PROVIDER=gemini
LLM_RUNTIME_ENABLED=true
GEMINI_API_KEY=<local key>
GEMINI_MODEL=<model name>
```

Do not commit the local `.env` file or any real API key.

## Expected Runtime Behavior

When LLM runtime mode is enabled:

- planner uses requirement extraction prompt/output schemas
- retrieval uses supplier/pricing analysis prompt/output schemas
- quotation remains deterministic and does not use LLM arithmetic
- compliance uses legal/compliance analysis prompt/output schemas
- validation uses finance/risk analysis prompt/output schemas
- approval uses approval package prompt/output schemas

Only validated, bounded structured output is written to workflow state. Raw
provider payloads, API keys, full prompts, and hidden reasoning are not stored.

## Troubleshooting

### Missing Provider Key

Groq, OpenRouter, and Gemini require API keys when selected. Add the matching
environment variable locally and restart the backend. Do not commit the key.

### Wrong Provider Name

Use one of:

```text
fake
groq
openrouter
ollama
gemini
```

### Missing Model

Set either `LLM_MODEL` or the provider-specific model variable:

```text
GROQ_MODEL
OPENROUTER_MODEL
OLLAMA_MODEL
GEMINI_MODEL
```

### Timeout

Increase `LLM_TIMEOUT_SECONDS` locally if the provider or local Ollama model is
slow. Keep automated tests mocked and deterministic.

### Rate Limit

Remote providers may return rate limit errors. Retries are bounded by
`LLM_MAX_RETRIES`. Fallback is disabled unless explicitly enabled.

### Invalid Structured JSON Response

LLM runtime mode requires valid JSON matching the stage schema. Invalid JSON or
schema mismatch fails safely and records bounded error metadata.

### Ollama Server Not Running

Start Ollama locally and ensure `OLLAMA_BASE_URL` points to it. Verify the
configured model is available before running the backend in Ollama mode.

For the Docker backend, use `OLLAMA_BASE_URL=http://host.docker.internal:11434`
in a local `docker-compose.override.yml`. See
`docs/llm/OLLAMA_LOCAL_SMOKE.md` for the complete local smoke guide.

### Fallback Expectations

`LLM_FALLBACK_ENABLED=false` by default. Fallback does not hide authentication
or configuration errors.

### Secrets

Never commit real keys. Review `git diff` before committing docs or local env
changes.

## Limitations

- No RAG or document indexing.
- No frontend provider-management UI.
- No admin key management.
- No LLM-backed approval continuation; human approval/resume uses the
  deterministic SPEC-012 workflow path.
- No LLM token streaming to frontend.
- No provider cost dashboard.
- No production secret vault integration.
