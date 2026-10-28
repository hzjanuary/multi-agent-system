# Model providers

The runtime uses one configured `default` profile. Set `LLM_PROVIDER` and an
explicit `LLM_MODEL`; there is no model download, fake provider, automatic
cross-provider fallback, or inference during startup/readiness.

| Provider | Required settings | HTTP subset | Current evidence |
| --- | --- | --- | --- |
| `ollama` | `LLM_MODEL`, `OLLAMA_BASE_URL` | Non-streaming `POST /api/chat`, JSON format, `options.num_predict` | Injected transport contract/error tests; live verification pending |
| `openai_compatible` | `LLM_MODEL`, `OPENAI_COMPATIBLE_BASE_URL`; optional `OPENAI_COMPATIBLE_API_KEY` | Non-streaming `POST <base>/chat/completions`, JSON-object response format, `max_tokens` | Contract tests; Cloudflare Workers AI configured/offline-tested only, not live-verified |
| `groq` | `LLM_MODEL`, `GROQ_API_KEY` | OpenAI-style chat completions | Real openai/gpt-oss-20b analyst → reviewer, approval/resume/assembly completed; SPEC-029 32 PASS / 0 BLOCKED |
| `openrouter` | `LLM_MODEL`, `OPENROUTER_API_KEY` | OpenAI-style chat completions | Contract tests; two historical HTTP 429 attempts, no successful live workflow |
| `gemini` | `LLM_MODEL`, `GEMINI_API_KEY` | Non-streaming `generateContent`, JSON MIME type | Injected transport contract/error tests; live verification pending |

These contract tests use test-only responses. They do not prove model quality,
endpoint availability, account access or live inference. See the release
[verification matrix](release/verification.md) for actual release evidence.

For local Ollama, install a model yourself and put its exact installed name in
`LLM_MODEL`. The container must reach the endpoint: the supplied Linux Compose
configuration maps `host.docker.internal` to the host gateway. An Ollama server
listening only on host loopback might need an explicitly configured bind address
and host firewall rules. An optional `ollama` Compose profile runs an isolated
service; its model installation is also manual. The backend contains no weights.

For a self-hosted OpenAI-compatible server, configure a base URL including its
API prefix, for example `http://model-service:8000/v1`. The runtime appends
`/chat/completions`. It requires text in `choices[0].message.content` and requests
`response_format={"type":"json_object"}`. The server must support this subset;
compatibility with every OpenAI-style endpoint is not promised. No tools,
streaming or provider-specific reasoning options are sent.

Provider/model/endpoint and token/retry/timeout settings are pinned in each run. Changing configuration
cannot reroute an existing run: the installed matching profile must be restored
before execution/resume. Credential rotation preserves profile identity. Only
trusted host operators can configure endpoints or install extension code. Remote
providers receive the user input and prior output needed for their agent step.

Every real dispatch reserves one persisted call under the active worker claim.
Retries and explicit recovery consume the same run budget; unknown remote
outcomes still consume calls. Only timeout, unavailability and rate-limit errors
are retried. Numeric `Retry-After` is capped at eight seconds. Authentication,
configuration and malformed/schema-invalid output fail without a retry. Errors
and events expose safe categories rather than raw provider bodies. Usage remains
unknown when the provider omits it; no prices are invented.

The explicit provider probe makes at most one request. Run it only after
configuring an installed model:

```bash
docker compose --env-file .maos/.env exec api \
  python -m app.cli provider check --max-calls 1 --max-tokens 128
```

Remote provider probes additionally require `--enable-remote`. For a complete
analyst/reviewer/approval smoke, use `scripts/ops/live_text_review.py` as described
in [CONTRIBUTING](../CONTRIBUTING.md). It refuses an unbounded server
configuration; run it against a dedicated installation with two calls, no
retries and the chosen output token limit. There is no live model call in default
CI.


Default OpenRouter preferences require ZDR and deny provider data collection.
The private `openrouter-free-smoke` opt-in explicitly relaxed those preferences
for authorized non-sensitive tests; it is never ordinary startup configuration.
These flags do not apply to Groq or Cloudflare. Provider/model terms govern
remote data retention/training independently. No account-wide sharing is enabled
by the application. Historical OpenRouter failures do not leave SPEC-029 open;
direct Groq supplied the genuine completed workflow evidence. Cloudflare remains
configured/offline-tested, not live-verified. No new calls are part of SPEC-030.
