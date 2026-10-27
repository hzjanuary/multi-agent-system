# Optional direct-provider smoke campaign

**Latest authorized campaign completed; do not rerun it.**
`groq-permissions-20261027` completed on direct Groq `openai/gpt-oss-20b`, run
`dd922648-beb2-4afb-94e5-8bea36a2070f`, with 2 calls, normal approval/explicit
resume and pure assembly. Cloudflare stayed unused. Total history is now 5
(2 OpenRouter failures, 1 original Groq permission failure, 2 new successes),
within the separate maximum of 7. The exclusive allocation and all attempt
records remain sealed. No further campaign is authorized by unused allowance.
[Completed live/current-image proof](release/direct-campaign-completed.json)
justifies 32 PASS / 0 BLOCKED. All isolated services are stopped and data retained.
The commands below document the executed procedure; they are not a repeat-run
instruction for this retained environment.

**Retained campaign ended; do not rerun it.** The authorized execution on
2026-10-27 consumed one Groq request and failed at analyst with HTTP 403,
`model_permission_blocked_project` / `permissions_error`. Cloudflare was not
invoked, as required for fatal permission failures. Run
`8573b056-b869-416b-87e6-e03569dbfb5f`, campaign/attempt markers and all data remain
retained; all four isolated services are stopped. Cumulative requests: 3
(2 historical OpenRouter + 1 Groq), not a reusable allowance. That campaign stays
closed. A subsequent explicit authorization permits exactly one separate campaign
below. See [original campaign evidence](release/direct-campaign-attempt.json).

The actual release image's Groq transport already serialized
`User-Agent: multi-agent-os/0.2.0`. An offline HTTPX capture inside that pinned
image (network disabled) verified headers/auth, timeout, retry=0 and token/reasoning
parameters; 8 focused tests passed. No runtime change/image rebuild was needed.
Metadata preflight success did not prove generation permission or capacity.

The error explicitly identifies a project-level model restriction, matching
[Groq model-permission documentation](https://console.groq.com/docs/model-permissions).
The maintainer may review the intended isolated project at
[Settings → Projects → Limits](https://console.groq.com/settings/project/limits);
do not weaken shared production restrictions or change billing. Fixing a policy
does not authorize rerunning the consumed campaign. Any later attempt requires
a separate explicit decision and preserved historical counts/records.

## One separately authorized campaign after the project-permission change

The maintainer confirmed allowing `openai/gpt-oss-20b` in the intended Groq
project and explicitly authorized **one new campaign: at most 4 additional /
7 cumulative requests**, with 2/provider, retries 0, cap 1024 and the same fatal
failure/whole-workflow fallback rules. Metadata still does not prove inference
permission. The host helper adds one bounded creation operation; no runtime,
adapter, default privacy or image inputs change.

```bash
# Allocate exactly once; this performs no inference or service startup:
python3 scripts/ops/direct_smoke_campaign.py new-campaign groq-permissions-20261027
direct() { python3 scripts/ops/direct_smoke_campaign.py --campaign groq-permissions-20261027 "$@"; }
direct preflight
direct start
direct compose run --rm --no-deps api python -m app.cli doctor
# Only if the existing administrator's session has expired:
direct compose --profile cli run --rm cli auth login
direct compose --profile cli run --rm cli workflow list
direct run --approve
# Stop only the shared isolated project, retaining all volumes/configuration:
direct compose stop
```

The root `new-campaign.json` allocates this authorization exclusively across
different IDs and processes. It cannot be invoked again to create another
allowance. New records live at
`.maos/direct-smoke/campaigns/groq-permissions-20261027/`; the previous campaign
directory and all its files remain byte-for-byte intact. The new manifest hashes
all prior artifacts, links all three historical run records and reserves a
4-request ceiling above the 3 consumed. It copies the same private credentials/
Free-plan confirmations and pins the same release image, database/application
identity, volume, CLI directory and original input. No replacement administrator,
configuration initialization or bootstrap is performed.

The selected campaign has its own exclusive `campaign.json` and per-provider
`attempt.json`. Repeated `run` or creation invocations cannot reset it. The
original command without `--campaign` remains locked by the original record.
The runner verifies all three historical runs before/after each new provider
attempt. Unknown/partial outcomes retain the reservation and stop; no automatic
second campaign is authorized. Old limits below describe the original campaign,
not the separately authorized 3+4=7 allocation.

This guide does not itself initiate inference. The
fixed order is **groq-smoke → cloudflare-smoke**. Each provider gets a new
`text_review@1.0.0` run from the original non-sensitive input, pinned for analyst
and reviewer. No production fallback/routing feature is enabled. The two failed
OpenRouter runs and their records remain historical; this campaign cannot call
OpenRouter or reuse its unused allowance.

## Models, endpoints and free-use conditions

| Profile | Adapter and model | Actual chat endpoint |
| --- | --- | --- |
| groq-smoke | Existing Groq adapter; `openai/gpt-oss-20b` | `https://api.groq.com/openai/v1/chat/completions` |
| cloudflare-smoke | Existing OpenAI-compatible adapter; `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | `https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1/chat/completions` |

[Groq's active production catalog](https://console.groq.com/docs/models) and
[model card](https://console.groq.com/docs/model/openai/gpt-oss-20b) list GPT-OSS
20B, JSON object mode, 131072 context and 65536 maximum completion tokens. This
profile uses `response_format={"type":"json_object"}`, `max_completion_tokens=1024`,
`reasoning_effort=low`, and `include_reasoning=false`. Low reduces reasoning effort;
hiding reasoning does not reduce its token consumption. GPT-OSS does not accept
`reasoning_format`; it is not sent. See [Groq reasoning](https://console.groq.com/docs/reasoning).
The 1024 completion cap remains in force, including reasoning. Invalid/truncated
JSON fails normally, with no repair, larger cap or schema relaxation.

[Cloudflare's current model page](https://developers.cloudflare.com/workers-ai/models/llama-3.3-70b-instruct-fp8-fast/)
and [JSON-mode list](https://developers.cloudflare.com/workers-ai/features/json-mode/)
confirm this text model supports JSON mode. The direct
[OpenAI-compatible API](https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/)
uses `max_tokens=1024`, JSON object mode and the existing strict application
schemas. No Worker, AI Gateway, SDK framework or hosted proxy is deployed.
Both requests are non-streaming and send no search, browser/code-execution,
remote-tool, plugin or fallback-model definitions. OpenRouter routing, data-policy
and max-price fields are never sent to either provider.

These models are **not zero-priced**: Groq lists $0.075/$0.30 per million
input/output tokens; Cloudflare lists $0.293/$2.253. Free-use protection comes
from the account plan's enforced quota, not a portable `max_price=0` field:

- In Groq Console, select the **organization that owns the API key**, then
  **Settings → Billing**. Confirm **Free**, not Developer, paid, or a paid/trial
  credit arrangement. Check **Limits** for GPT-OSS 20B access and quota. No
  documented model-list field proves organization billing tier, so the helper
  requires a local dashboard confirmation bound to the entered key.
- In Cloudflare dashboard select the **intended Account ID**, open **Workers &
  Pages → Plans**, and confirm **Workers Free**, with no paid upgrade/billing.
  Open **Workers AI** and review daily neuron usage/free allowance. Workers Free
  hard-stops at its allowance; Workers Paid can charge above it and is excluded
  from this campaign. The AI-scoped token is not granted billing permissions to
  read/change account subscriptions; confirm the plan manually instead of
  treating model metadata as billing evidence. See
  [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/).

Do not enable paid plans, credits, paid add-ons or account-wide data sharing.
Provider-specific retention terms still apply; OpenRouter's privacy flags do
not apply to these APIs. Use only the existing non-sensitive test input. This
smoke is not a confidential-enterprise readiness claim.

## Prepared private files and credential entry

The image is prepared locally. Do not rerun initialization or bootstrap an
administrator. Files under Git-ignored `.maos/direct-smoke/` use directory 0700
and file 0600 permissions, outside the backend Docker context:

| File / field | Meaning |
| --- | --- |
| `groq-smoke/private.env`: `GROQ_API_KEY` | Actual Groq adapter credential, initially blank |
| `groq-smoke/private.env`: `GROQ_REASONING_EFFORT=low` | Host-controlled reasoning setting included in run identity |
| `cloudflare-smoke/private.env`: `CLOUDFLARE_ACCOUNT_ID` | Helper-only account value, initially blank |
| `cloudflare-smoke/private.env`: `OPENAI_COMPATIBLE_API_KEY` | Actual Workers AI token consumed by the compatible adapter, initially blank |
| `cloudflare-smoke/private.env`: `OPENAI_COMPATIBLE_BASE_URL` | Constructed from the entered Account ID, ending `/ai/v1` |
| `<profile>/plan.json` | Local free-plan confirmation bound to that key/account; identifiers are not published |

Prepared source is `44a8c42373af1320986ad78d922aa79595775dbe`; immutable image
`sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`
is pinned in the private overlay. The handoff HEAD can differ for documentation
only. See [preparation proof](release/direct-smoke-preparation.json). At that
initial handoff, credentials, Account ID and free-plan confirmation were pending;
preparation did not invoke either provider. Existing input stays at
`.maos/openrouter-free-smoke/input.txt`.

Subsequent local setup supplied both credentials and Free-plan confirmations.
The initial metadata preflight returned 403 on Groq's models list. The host
helper now sends the explicit application User-Agent
`Multi-Agent-OS/SPEC-029-metadata-preflight`; the same Groq key/URL then returned
200, followed by Cloudflare search/schema 200 and `PREFLIGHT_PASS`. See the
[bounded diagnosis](release/direct-preflight-diagnosis.json). No image inputs
changed, so the prepared image above remains pinned. No generation occurred.

Create a scoped Cloudflare token for **only the intended account**, with
**Workers AI Read + Edit** (the Workers AI REST token template), without Worker
script/deployment or billing permissions. See the official
[REST setup](https://developers.cloudflare.com/workers-ai/get-started/rest-api/).

One hidden-input command accepts the three values, then asks you to type
`GROQ_FREE` and `WORKERS_FREE` only after the exact dashboard checks above.
Credentials never go into command arguments or shell history. Other provider
keys and OpenRouter policy fields stay blank in each profile. Rotating keys or
account ID invalidates the saved plan binding. Recheck the plan before each
campaign; an attestation is not an API guarantee that an account can never change.

## Single operator workflow

Run from the repository root **only when ready to initiate the authorized live
campaign**. `preflight` performs authenticated **GET-only** model discovery and
Cloudflare schema retrieval; it never generates text. Missing credentials or
unconfirmed free plans stop it before network/generation. Both profiles must be
ready so a fallback cannot accidentally use an unconfigured/paid account.

```bash
direct() { python3 scripts/ops/direct_smoke_campaign.py "$@"; }
# First setup only; already completed for the retained environment:
direct set-credentials
direct preflight
direct start
direct compose run --rm --no-deps api python -m app.cli doctor
# Only if the existing session expired: use the EXISTING administrator account.
direct compose --profile cli run --rm cli auth login
direct compose --profile cli run --rm cli workflow list
# This is the ONE command that initiates generation and the authorized fallback:
direct run --approve
```

Stop at any failed prerequisite. Do not run `provider check`, a warm-up prompt,
a separate direct HTTP generation call or either historical OpenRouter runner.
`start` is non-inference: it reuses the same Compose project/database/volume,
JWT/application secrets, administrator, `.maos/openrouter-free-smoke/cli/` state
and `.maos/openrouter-free-smoke/input.txt`. It stops API/worker and refuses
queued jobs, live leases or executing nodes before selecting Groq. Input is
hash-bound to the existing file; do not replace it between provider runs.
The old OpenRouter env, overlays, markers and records are not edited.

If login is needed, run only the documented local login action. Do not bootstrap
or regenerate secrets. CLI state persists across the separate CLI invocations.
Resolved Compose settings are validated in memory, never printed; API and worker
must match the pinned image/profile and have no CLI credential mounts.

Each metadata GET records only sanitized fields in private
`.maos/direct-smoke/metadata-diagnostics/*.json`: target provider/operation,
method/hostname/path (Account ID masked), status, MIME type, bounded error
code/type and explicitly sourced response IDs including `header.cf-ray`.
Missing, withheld and incompletely collected fields are distinguished. A
`cf-ray` identifies an edge response, not which provider API was targeted; the
target is established from the allowlisted URL. No messages, raw body, arbitrary
headers, Authorization value or resolved configuration are logged. TLS remains
verified; redirects and retries remain disabled. A 403 is a blocker, never proof
by itself of invalid credentials, paid-plan requirements or model unavailability.

## Fallback, reservations and retained evidence

`run --approve` validates both profiles, current metadata, the running Groq
profile, valid CLI authentication and both historical records before reserving
`campaign.json` atomically. A losing/repeated invocation cannot stop the active
campaign or create a fresh budget. Every provider has its own exclusive
`<profile>/attempt.json` and normal PostgreSQL pre-dispatch reservations.

Groq success completes the existing content-bound approval, explicit resume and
pure assembly, then stops. Cloudflare is **unused, not live-verified**. Eligible
Groq HTTP 429, connection/timeout or transient HTTP 500/502/503/504 failures may
trigger one new Cloudflare run only when the Groq run is FAILED with one/two
consumed calls. Before changing profiles the runner stops API/worker and checks
no queued job, ownership/lease or executing node remains. Cloudflare starts at
the beginning from the original input; it receives no Groq checkpoint.

Configuration, credentials/auth/permissions, billing, unknown model/parameters,
invalid JSON/schema, approval/DB/integrity/state failures, cancellation or
unconfirmed terminal state are fatal, without fallback. A Cloudflare failure
ends the campaign. There is no third provider or repeated campaign.

Limits: **2 calls/provider, 4 new calls/campaign, 6 cumulative including the 2
historical OpenRouter requests**, retries 0 at application and HTTP transport,
1024 output tokens per call and the existing request timeout. Failed/uncertain
calls consume reservations. Never delete/edit guards to retry. Unreadable or
partial evidence stops safely, retaining the reservation; unknown counts/costs
are not invented as zero.

Private `live.stdout.json`, `live.stderr.json`, `api-evidence.json` and
`outcome.json` under each profile preserve run/node IDs, model/provider metadata,
outputs, usage and safe diagnostics. The campaign outcome records order, fallback
reason and consumed counts. It does not attribute account aggregates to a run or
invent unreported cost/currency. Review/redact before sharing; no raw input,
outputs, credentials or provider body belongs in publishable diagnostic logs.

The runner stops the isolated services after its execution. For an explicit stop
at any stage, including before credential entry:

```bash
python3 scripts/ops/direct_smoke_campaign.py compose stop
```

Volumes, credentials, CLI session and all old/new attempt records are retained.
AC-08/AC-29 remain BLOCKED during preparation. Genuine successful chained model
execution is needed for AC-08; the documented real-model image/CLI journey is
also needed for AC-29. Neither a new provider nor successful metadata lookup
explains the old OpenRouter 429s or establishes enterprise readiness.
