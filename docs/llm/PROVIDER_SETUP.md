# LLM Provider Setup

SPEC-011 adds a provider-independent LLM layer for Enterprise Multi-Agent OS.
The implementation supports `fake`, `groq`, `openrouter`, `ollama`, and
`gemini` behind one backend service interface.

This guide is for local development and demos. Do not commit real API keys.

## Safe Defaults

The safe default mode is offline and deterministic:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_FALLBACK_ENABLED=false
LLM_FALLBACK_PROVIDER=fake
```

With these defaults:

- no API keys are required
- no real provider network calls are needed for normal local demo use
- workflow runtime uses the deterministic LangGraph nodes
- the `/run` API response contract remains unchanged
- workflow runtime still stops at `WAITING_APPROVAL`

## Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | Active provider: `fake`, `groq`, `openrouter`, `ollama`, or `gemini` | `fake` |
| `LLM_MODEL` | Global model fallback when provider-specific model is empty | empty |
| `LLM_RUNTIME_ENABLED` | Enables LLM runtime adapter when `true` | `false` |
| `LLM_TIMEOUT_SECONDS` | Per-request provider timeout | `30` |
| `LLM_MAX_RETRIES` | Retry count for transient provider errors | `2` |
| `LLM_FALLBACK_ENABLED` | Enables fallback for transient provider errors | `false` |
| `LLM_FALLBACK_PROVIDER` | Provider used for fallback when enabled | `fake` |
| `GROQ_API_KEY` | Groq API key | empty |
| `GROQ_MODEL` | Groq model override | empty |
| `OPENROUTER_API_KEY` | OpenRouter API key | empty |
| `OPENROUTER_MODEL` | OpenRouter model override | empty |
| `OLLAMA_BASE_URL` | Local Ollama server base URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | empty |
| `GEMINI_API_KEY` | Gemini API key | empty |
| `GEMINI_MODEL` | Gemini model override | empty |

API keys are optional at application settings load time. Real remote providers
fail safely only when selected and used without required configuration.

## Fake Provider

Use `LLM_PROVIDER=fake` for tests, offline development, and the stable local
demo.

The fake provider:

- performs no network calls
- requires no API key
- returns deterministic responses
- is not a real AI model response

Keep `LLM_RUNTIME_ENABLED=false` for the board-stable deterministic demo. If
you intentionally enable LLM runtime mode with the fake provider, the runtime
uses the same LLM service boundary but remains local and deterministic.

## Groq

Groq uses the non-streaming OpenAI-compatible chat completions API.

Required local variables:

```text
LLM_PROVIDER=groq
GROQ_API_KEY=<local key>
GROQ_MODEL=<model name>
```

`LLM_MODEL` may be used instead of `GROQ_MODEL`, but the provider-specific
model override wins when both are set.

Common errors:

- missing key: configuration error
- invalid key: authentication error
- quota or throughput exceeded: rate limit error
- provider outage or 5xx: unavailable error
- timeout: timeout error

## OpenRouter

OpenRouter uses a non-streaming OpenAI-like chat completions API.

Required local variables:

```text
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=<local key>
OPENROUTER_MODEL=<model name>
```

`LLM_MODEL` may be used instead of `OPENROUTER_MODEL`, but the provider-specific
model override wins when both are set.

Common errors:

- missing key: configuration error
- invalid key: authentication error
- quota or provider routing limit: rate limit error
- upstream/provider outage: unavailable error
- timeout: timeout error

## Ollama

Ollama is intended for local development. It uses the local non-streaming
`/api/chat` endpoint and does not require an API key.

Example local variables:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=<local model name>
```

Before using Ollama mode, start the Ollama server and make sure the configured
model is available locally.

For a Docker Compose override example and a safe optional smoke command, see
`docs/llm/OLLAMA_LOCAL_SMOKE.md`.

Common errors:

- server not running or connection refused: unavailable error
- missing/incorrect model: provider error or invalid response depending on the
  Ollama response
- invalid base URL: configuration error
- timeout: timeout error

## Gemini

Gemini uses the non-streaming `generateContent` REST shape.

Required local variables:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=<local key>
GEMINI_MODEL=<model name>
```

`LLM_MODEL` may be used instead of `GEMINI_MODEL`, but the provider-specific
model override wins when both are set.

Common errors:

- missing key: configuration error
- invalid key: authentication error
- quota exceeded: rate limit error
- provider outage or 5xx: unavailable error
- malformed generation response: invalid response error

## Runtime Feature Flag

`LLM_RUNTIME_ENABLED=false` uses the deterministic runtime nodes and does not
call `LLMService`.

`LLM_RUNTIME_ENABLED=true` enables the `LLMRuntimeAdapter` path. In that mode,
runtime stages use provider-independent prompt builders, call `LLMService`,
parse structured JSON output with Pydantic, and write only validated bounded
outputs into workflow state.

The quotation stage still avoids LLM arithmetic. It records a deterministic
skip marker when LLM runtime mode is enabled.

## Retry And Fallback

Retries are bounded by `LLM_MAX_RETRIES` and apply only to transient categories:

- `timeout`
- `unavailable`
- `rate_limit`

The service does not retry configuration, authentication, invalid response,
safety, invalid request, or cancellation failures.

Fallback is disabled by default. If enabled, fallback is only used for safe
transient failures and does not hide missing-key or authentication errors.

## Security Notes

- Never commit real provider keys.
- Configure provider keys through environment variables only.
- Do not paste keys into documentation, tests, seed data, or demo screenshots.
- Logs, events, and runtime state must not expose API keys, bearer tokens, raw
  provider payloads, full prompts, or hidden reasoning.
- Production secret vault integration is not implemented yet.
- Admin provider key management UI and public provider-management APIs are not
  implemented.

## Known Limitations

- No RAG or document indexing through LLM providers yet.
- No frontend provider-management UI.
- No admin API key management.
- No LLM-backed approval continuation; human approval/resume uses the
  deterministic SPEC-012 workflow path.
- No LLM token streaming to the frontend.
- No provider cost dashboard.
- No production secret vault integration.
- No real-provider smoke tests are part of the automated validation gate.
