# Private OpenRouter free smoke

This is a preparation-first procedure for SPEC-029's packaged `text_review`
workflow. Preparation and preflight do not make inference calls. The prepared
key and input are empty. Enter a new dedicated test key and your own short,
non-sensitive text locally when ready. Do not reuse an existing installation's
key, user database, credentials, or Compose project.

The fixed selection is `google/gemma-4-31b-it:free`, canonical slug
`google/gemma-4-31b-it-20260402`, through the single `google-ai-studio` provider
tag. The helper rechecks public metadata before the live attempt and stops if
the exact free variant, provider, capabilities, availability, or zero prices
change. It never switches models/providers or removes privacy restrictions to
find an available route. OpenRouter metadata advertising `response_format`
supports the adapter's actual `json_object` mode; this is not a claim of JSON
Schema/`structured_outputs` support. Optional reasoning is checked explicitly.

Only this private profile permits data collection (`data_collection=allow`,
`zdr=false`). Public defaults remain `deny` and ZDR enabled. Treat anything sent
to this route as potentially collected/trained on. A request-level ZDR choice
cannot override an account-wide ZDR restriction. If the account restriction
prevents this route, use a separate test account; this procedure does not change
global account settings or logging. Review the [OpenRouter privacy
settings](https://openrouter.ai/settings/privacy) yourself.

Routing also requires `allow_fallbacks=false`, `require_parameters=true`,
`only=["google-ai-studio"]`, and zero `max_price` for prompt, completion, and
request. Prompt and completion prices must be explicitly zero in both model
and endpoint metadata. An omitted request fee is recorded as omitted/not
applicable for the explicitly free variant, never invented as a metadata zero.
The outgoing request still caps its price at zero. OpenRouter describes
[`:free` variants as free of cost](https://openrouter.ai/docs/guides/routing/model-variants/free)
and documents [provider routing and price caps](https://openrouter.ai/docs/guides/routing/provider-selection).
Free availability/rate limits remain external constraints; preflight is not a
promise that an inference will succeed.

Run from the repository root. First build the dedicated local image from the
reviewed checkout if it has not already been prepared. No image is published.

```bash
docker build --network=host --target runtime \
  --label org.opencontainers.image.revision="$(git rev-parse HEAD)" \
  -t multi-agent-os:openrouter-free-smoke backend
python3 scripts/ops/openrouter_free_smoke.py prepare --image multi-agent-os:openrouter-free-smoke
python3 scripts/ops/openrouter_free_smoke.py preflight --metadata-only
```

`prepare` uses the image's existing `app.cli config init` with networking
disabled. It refuses a nonempty destination and pins the image ID. Files live
only under Git-ignored `.maos/openrouter-free-smoke/` (directory 0700, files
0600): separate secrets, database name/user, random Compose project and volume,
loopback port (58031 when available), and `cli/auth.json` session. The private
overlay replaces the base CLI mount at `/cli`; API and worker receive no CLI
credential mount. The wrapper removes all private env keys and `COMPOSE_*`
overrides from its subprocess environment so exported shell keys cannot win
over `--env-file`. Resolved Compose configuration is checked in memory and is
never printed or saved. Do not invoke raw `docker compose` with this env file.

When you decide to make the bounded live attempt, use this sequence. `set-key`
prompts without echo; never put the key in command arguments, shell history, or
chat. It fills only `OPENROUTER_API_KEY` in
`.maos/openrouter-free-smoke/private.env`; you may instead edit that 0600 file
locally without printing it. CLI bootstrap/login separately prompt for the dedicated test user's
email and password. Choose a new local test user; no sample records are added.

```bash
smoke() { python3 scripts/ops/openrouter_free_smoke.py "$@"; }
smoke set-key
smoke preflight
smoke compose up -d --wait postgres redis
smoke compose run --rm --no-deps api python -m app.cli migrate
smoke compose run --rm --no-deps api python -m app.cli admin bootstrap
smoke compose up -d --wait api worker
smoke compose run --rm --no-deps api python -m app.cli doctor
smoke compose --profile cli run --rm cli auth login
smoke compose --profile cli run --rm cli workflow list
${EDITOR:-vi} .maos/openrouter-free-smoke/input.txt
smoke run --approve
smoke compose stop
```

The editor file starts empty: write your own non-sensitive text (1–16000
characters), retain mode 0600, then save and close it. The separate `workflow
list` container proves the dedicated CLI login persists. Do not run `provider
check`: that would consume inference calls outside this two-call attempt.
`doctor` checks storage/readiness and the worker; it does not run inference.
The separate README provider-probe example remains outside this two-call budget
and unverified; it needs a separate explicit budget if later required for release.
If you change the private key before the attempt after services exist, recreate
them with `smoke compose up -d --force-recreate api worker`.

`run --approve` explicitly enables remote inference and the authenticated
approval. It validates the effective running API/worker images and environment,
then reserves `attempt.json` using an exclusive create **before** invoking the
existing `scripts/ops/live_text_review.py` once. The run has at most two provider
calls, no provider retries, and at most 1024 output tokens per call (2048 total).
This bounds client generation HTTP attempts, including uncertain outcomes.
OpenRouter or an upstream provider may perform internal work the client cannot
observe; the evidence must not claim to count that internal behavior.
The approval still pauses execution, uses the content identity/revision, and
requires an explicit resume, as checked by the existing entry point.

Keep `attempt.json` after failure, timeout, or interruption. Do not delete it,
retry the live command, create another profile, or reset the budget as recovery.
Inspect the retained evidence and obtain a fresh explicit budget decision if a
new live attempt is needed. A preflight failure occurs before reservation and
makes no inference call; it can be rechecked without changing selection.

`live.stdout.json`, `live.stderr.json`, `outcome.json`, and the permanent attempt
record capture success or partial failure privately. When a run ID is observed,
the helper also attempts authenticated GET-only reads of run, nodes, events,
and approvals using the API session file, never the OpenRouter key. This raw
API evidence may contain your text and stays private. `public-metadata.json`
contains unauthenticated public metadata only. Share only reviewed, redacted
status/hash summaries; do not commit these private artifacts or print the env
file. Fixture success and metadata preflight do not prove live-provider
acceptance or clean-release-image acceptance.

`smoke compose stop` retains the dedicated database volume and evidence. The
wrapper rejects volume deletion and unsafe Compose overrides. This procedure
does not delete operator data or volumes, and does not push or deploy anything.
