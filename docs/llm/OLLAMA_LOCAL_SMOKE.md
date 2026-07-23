# Ollama Local Provider Smoke Guide

This guide verifies that a local Ollama server and model can answer the same
non-streaming `/api/chat` shape used by the backend Ollama provider.

This is optional local validation. The stable graduation demo remains fake-mode
and no-key by default.

## What This Checks

The smoke path checks:

- Ollama is installed and reachable on the local machine.
- The selected model is pulled and can answer a tiny harmless prompt.
- The Docker backend can be configured to reach host Ollama through
  `host.docker.internal`.

It does not:

- change default provider settings
- enable LLM runtime by default
- run in CI
- require API keys
- auto-approve or auto-resume workflows
- send customer email
- validate cloud production deployment

## Stable Default Mode

Keep these defaults for the defense-stable local demo:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

With these settings, workflow `/run` uses deterministic runtime stages and
still stops at `WAITING_APPROVAL`. Real LLM providers are optional experiments.

## Prerequisites

- Ollama installed locally.
- Docker Desktop or a Docker environment that supports backend containers
  reaching the host through `host.docker.internal`.
- The backend and frontend can still run with the normal local demo commands.

Pull a model:

```bash
ollama pull llama3.1:8b
```

Start Ollama if it is not already running:

```bash
ollama serve
```

## Optional Smoke Command

The repository includes a local manual utility:

```bash
python scripts/demo/llm_provider_smoke.py --help
```

Run a dry configuration check without calling Ollama:

```bash
python scripts/demo/llm_provider_smoke.py --provider ollama --model llama3.1:8b --dry-run
```

Run a real local Ollama smoke call from the host:

```bash
python scripts/demo/llm_provider_smoke.py --provider ollama --model llama3.1:8b --base-url http://localhost:11434
```

The command prints only bounded provider/model/status metadata. It does not
print prompts, response bodies, tokens, passwords, API keys, or environment
files.

Expected successful shape:

```text
provider=ollama model=llama3.1:8b status=ok base_url=http://localhost:11434 response_chars=2
```

If Ollama is not running, the status is `unavailable` or `timeout`.

## Docker Compose Local Override

To let the backend container call host Ollama, create an untracked
`docker-compose.override.yml` in the repository root:

```yaml
services:
  backend:
    environment:
      LLM_PROVIDER: ollama
      LLM_RUNTIME_ENABLED: "true"
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      OLLAMA_MODEL: llama3.1:8b
```

Do not commit local override files that contain machine-specific settings.

Then rebuild/restart the backend:

```bash
docker-compose up -d --build backend
```

The existing `docker-compose.yml` already keeps fake mode as the default. The
override above only applies on your local machine.

## Verify Backend Runtime With Ollama

After the override is active:

1. Confirm Ollama is serving the configured model.
2. Run migrations and demo seed if needed.
3. Login through the frontend.
4. Open a `CREATED` workflow.
5. Click **Run workflow**.
6. Confirm the workflow reaches `WAITING_APPROVAL`.

The `/run` API contract is unchanged. Human approval is still required before
post-approval continuation, and `/resume` remains the only continuation path.

## Switch Back To Stable Fake Mode

Remove or rename `docker-compose.override.yml`, or set:

```yaml
services:
  backend:
    environment:
      LLM_PROVIDER: fake
      LLM_RUNTIME_ENABLED: "false"
      OLLAMA_MODEL: ""
```

Restart the backend:

```bash
docker-compose up -d --build backend
```

You can also confirm the effective Compose configuration:

```bash
docker-compose config
```

## Telegram Demo Note

The Telegram inbound bridge does not require Ollama. It parses local demo RFQ
messages deterministically, creates a workflow through existing backend APIs,
and optionally calls `/run`. Ollama is only needed if you separately enable LLM
runtime behavior for local experimentation.

The bridge still does not auto-approve, auto-resume, or send real email.

## Troubleshooting

### Server Not Running

Start Ollama:

```bash
ollama serve
```

Then rerun:

```bash
python scripts/demo/llm_provider_smoke.py --provider ollama --model llama3.1:8b
```

### Model Missing

Pull the model:

```bash
ollama pull llama3.1:8b
```

Or set `OLLAMA_MODEL` / `--model` to a model that exists locally.

### Backend Container Cannot Reach Ollama

Use this base URL inside the backend container:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

If your Docker environment does not support `host.docker.internal`, configure
the equivalent host gateway address for your platform.

### Slow Local Model

Increase the timeout only for local experimentation:

```text
LLM_TIMEOUT_SECONDS=60
```

Keep automated tests and the default demo on fake/no-key settings.

## Safety Notes

- Do not commit real provider keys or local `.env` files.
- Ollama does not require an API key, but local override files can still expose
  machine-specific configuration.
- Do not paste raw prompts, provider payloads, embeddings, vector payloads,
  access tokens, cookies, or secrets into final evidence.
- This guide does not add CI validation against real Ollama.
