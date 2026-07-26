# Provider Evidence Policy

## Purpose

This policy defines how fake, manual, RAG, Tavily, and future providers may
produce evidence for internal review. Provider evidence is reference material
only. It is not a final quotation and must not bypass Manager/Admin approval,
explicit resume, or outbound communication controls.

Current implementation references:

- Price research contracts: `backend/app/price_research/`
- Manual Tavily smoke guide: `docs/demo/PROVIDER_LIVE_VERIFICATION.md`
- Telegram bridge guide: `docs/demo/TELEGRAM_INBOUND_DEMO.md`
- SPEC authority: `.ai/specs/SPEC-021-catalog-governance-provider-policy/spec.md`

## Evidence Trust Levels

| Trust level | Source | Allowed use | Manual review |
| --- | --- | --- | --- |
| `demo_fake` | deterministic fake provider | tests and demos only | always label as fake/demo reference evidence |
| `manual_reviewed` | explicit human-entered source | internal review evidence | reviewer must be identifiable in future audit design |
| `internal_rag` | internal knowledge/RAG citations | internal review evidence with citations | verify citation relevance before approval |
| `external_unverified` | Tavily or future web/provider result | manual review only | required before using in customer-facing decisions |
| `approved_policy` | future approved internal pricing policy | may inform future approved drafts | still requires Manager/Admin approval |

Default trust for new providers is `external_unverified`.

## Universal Provider Rules

All providers must:

- return bounded normalized evidence;
- include source/citation metadata where applicable;
- set or preserve `is_final_quote=false`;
- include warnings when evidence is fake, missing, low confidence, or
  unstructured;
- avoid raw HTML, raw provider payloads, prompts, chain-of-thought, embeddings,
  vector payloads, tokens, cookies, passwords, and secrets;
- avoid customer personal data in provider queries unless explicitly approved
  in a later privacy/policy spec;
- fail closed on timeout, malformed response, missing key, or unsafe output.

Providers must not:

- infer prices from prose unless a future structured extraction policy approves
  and tests it;
- claim stock availability;
- promise delivery dates;
- approve discounts;
- create workflows;
- approve or resume workflows;
- send email or Telegram final quotes;
- mutate workflow state unless a future integration task explicitly scopes it.

## Fake Provider Policy

The fake provider is deterministic demo/test evidence only.

Allowed:

- unit and integration tests;
- local demo evidence placeholders that are clearly labeled fake;
- no-network proof of schema and UI behavior.

Required warning:

```text
Fake provider output is deterministic demo reference evidence, not a final quote.
```

Forbidden:

- treating fake values as market prices;
- using fake values as approved quotation data;
- presenting fake values without a fake/demo label.

## Manual Provider Policy

The manual provider may return evidence only from explicit supplied source data.

Manual evidence must include:

- source title or description;
- retrieved or supplied date;
- currency when an amount is present;
- reviewer warning or note;
- confidence appropriate to the source.

Manual evidence does not bypass approval/resume. If manual data is absent, the
provider should return empty prices with a manual-review warning.

## RAG Evidence Policy

RAG evidence is internal knowledge evidence.

Allowed:

- cite internal documents already ingested through the knowledge system;
- create reference prices only from explicit structured metadata such as
  `observed_price` or `amount`;
- return sources without prices when documents are relevant but unstructured.

Required warnings:

- RAG evidence is reference material, not a final quote.
- No structured price metadata found; manual pricing review is required.

Forbidden:

- regex price extraction from prose unless a later approved policy adds it;
- LLM price extraction in this policy;
- raw document or vector payload display;
- raw prompts, provider payloads, embeddings, or chain-of-thought.

## Tavily / External Web Evidence Policy

Tavily is currently available only as an optional adapter and manual live smoke
path. It is not connected to Telegram, workflows, frontend pages, approval,
resume, or email.

Live verification requires:

- local `TAVILY_API_KEY`;
- explicit `--confirm-live-provider`;
- provider terms and acceptable use reviewed;
- rate limits understood;
- dry-run available without key/network;
- output redacted and bounded;
- no CI live key requirement.

Tavily/external evidence is `external_unverified` unless a future review
promotes it. External snippets are citations for manual review only. They must
not be used to infer a price from prose or produce a final quote.

## No CI Live Key Policy

Automated tests and CI must not require:

- `TAVILY_API_KEY`;
- Telegram bot token;
- paid LLM provider key;
- SMTP/Gmail credentials;
- live network provider access.

Tests should use:

- injected transports;
- mocked provider output;
- deterministic fake providers;
- dry-run commands.

## Reference Evidence vs Final Quote

Reference evidence can support internal review. It cannot become a final
customer quotation until the workflow has:

1. supported catalog item and safe request normalization;
2. deterministic workflow run to `WAITING_APPROVAL`;
3. Manager/Admin approval;
4. explicit `/resume`;
5. completed state and approved preview rules satisfied;
6. no unresolved unsupported item or manual-review blocker.

Even after completion, sending remains unavailable unless a future send spec
implements it behind explicit policy and audit controls.

## Source Citation, Bounding, And Redaction

Evidence display should bound:

- source count;
- title length;
- URL length;
- snippets or excerpts;
- warnings;
- reference prices.

Evidence must redact or reject:

- API keys;
- Authorization headers;
- Bearer tokens;
- cookies;
- passwords;
- raw provider payload markers;
- raw prompt markers;
- secrets;
- chain-of-thought.

## Provider Failure And Degradation

Provider failure must not block stable deterministic demo operation.

Failure behavior:

- missing key: safe configuration error;
- timeout: safe timeout error;
- invalid JSON: safe parse error;
- non-2xx: safe status-only error;
- no sources: warning and manual review;
- sources but no structured price: warning and manual review;
- low confidence: caution and manual review.

Do not expose raw provider responses or internal stack traces in customer-facing
messages.

## Change Checklist

Before a provider behavior change:

- [ ] Trust level is assigned.
- [ ] Manual-review requirements are documented.
- [ ] No CI live key is required.
- [ ] No provider call is connected to Telegram/workflow/runtime unless a
  specific implementation spec authorizes it.
- [ ] Tests prove no raw payloads/secrets are displayed.
- [ ] Tests prove no final quote, stock, delivery, discount approval, approval,
  resume, or email-sent claim is introduced.
