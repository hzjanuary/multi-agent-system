# Governance Change Checklist

## Purpose

Use this checklist before changing catalog, provider evidence, approval,
outbound preview, future send behavior, or frontend evidence/catalog display.
It is intentionally conservative: if an item is unclear, stop and create or
update a bounded SPEC before implementation.

## Universal Safety Questions

- [ ] Does the change preserve deterministic/no-key demo defaults?
- [ ] Does the change avoid real provider keys in CI?
- [ ] Does the change avoid backend/frontend/API/database/Docker/CI behavior
  unless a specific implementation task authorizes it?
- [ ] Does the change avoid raw prompts, provider payloads, embeddings, vector
  payloads, tokens, cookies, passwords, and secrets?
- [ ] Does the change avoid final quote, stock, delivery, discount approval,
  approval, resume, real email, or email-sent claims before the approved
  lifecycle allows them?
- [ ] Does the change preserve Manager/Admin approval and explicit resume?
- [ ] Does the change preserve no auto-approval and no auto-resume?

## Catalog Item Addition

- [ ] Canonical display name defined.
- [ ] Stable item id or SKU-like slug defined.
- [ ] Normalized item name defined.
- [ ] Item family defined.
- [ ] Unit and domain defined.
- [ ] Supported add-ons listed, even if empty.
- [ ] English aliases reviewed.
- [ ] Vietnamese aliases reviewed when applicable.
- [ ] Unsupported-adjacent terms reviewed.
- [ ] Catalog version updated.
- [ ] Workflow metadata remains bounded and JSON-safe.
- [ ] No price, stock, delivery, discount, supplier credential, or real
  customer data added.
- [ ] Parser tests added.
- [ ] Mixed supported/unsupported tests added.

## Alias Addition

- [ ] Alias is not too broad.
- [ ] Alias does not overlap another supported family unexpectedly.
- [ ] Alias does not hide an add-on.
- [ ] Alias does not imply unsupported SKU specificity.
- [ ] Vietnamese accented/unaccented behavior is tested when applicable.
- [ ] False-positive regression tests are added.
- [ ] Original-text unsupported scanning remains authoritative.

## Add-On Addition

- [ ] Canonical add-on id defined.
- [ ] Display name defined.
- [ ] Aliases reviewed.
- [ ] Compatible item families listed.
- [ ] Incompatible item families listed.
- [ ] Ambiguous compatibility behavior defined.
- [ ] Add-on remains separate from item name.
- [ ] Tests cover compatible and incompatible requests.

## Provider Behavior Change

- [ ] Evidence trust level assigned.
- [ ] Provider output remains reference evidence only.
- [ ] `is_final_quote=false` preserved.
- [ ] No price inference from prose unless a future approved policy adds it.
- [ ] Source count, URLs, snippets, warnings, and prices are bounded.
- [ ] Sensitive markers are redacted or rejected.
- [ ] Missing/low-confidence evidence fails to manual review.
- [ ] No workflow, Telegram, approval, resume, frontend, or outbound side effect
  is introduced without a specific implementation spec.

## Live Provider Verification

- [ ] Live verification is manual-only.
- [ ] Explicit confirmation flag required.
- [ ] Local provider key required only for confirmed live mode.
- [ ] Dry-run path remains no-key/no-network.
- [ ] CI tests use mocked/injected transports.
- [ ] Output is bounded and redacted.
- [ ] Provider terms, rate limits, and privacy posture reviewed.
- [ ] No arbitrary scraping is introduced.

## Outbound Preview / Send Change

- [ ] Preview and send remain separate.
- [ ] `OUTBOUND_SEND_ENABLED=false` remains the default.
- [ ] No send endpoint is added without a separate approved spec.
- [ ] No send button is added without backend send support and policy.
- [ ] Preview requires completed approval/resume evidence.
- [ ] Future send requires RBAC, explicit confirmation, audit, retries, and
  credential handling.
- [ ] Telegram does not auto-send final quotes.
- [ ] Tests prove no email-sent claim without send evidence.

## Frontend Evidence / Catalog Display Change

- [ ] UI renders only explicit workflow state fields.
- [ ] UI does not infer catalog matches from prose, events, or agent summaries.
- [ ] UI does not fabricate prices, sources, catalog records, or evidence.
- [ ] UI labels catalog metadata as intake evidence.
- [ ] UI labels reference evidence as reference-only, not final quotation.
- [ ] UI hides or redacts sensitive markers.
- [ ] UI keeps approval/resume controls visible.
- [ ] UI does not add send controls unless future send behavior exists.

## Required Tests And Gates

Use the smallest relevant set for the changed surface, then broaden when shared
contracts are touched.

Script/parser changes:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
python3 -m py_compile scripts/demo/telegram_inbound_bridge.py
```

Backend/provider/outbound changes:

```bash
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
```

Frontend display changes:

```bash
cd frontend
npm run lint
npm run build
npm run typecheck
npm test
```

Repository gates:

```bash
docker compose config
docker compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config
bash scripts/ci/all-gates.sh
git diff --check
git status --short
```

## Stop Conditions

Stop before implementation when:

- a change would enable live provider calls in product flows;
- a change would add or alter API contracts;
- a change would add database models or migrations;
- a change would alter approval/resume semantics;
- a change would add outbound send behavior;
- a change requires real provider keys in CI;
- the policy owner cannot explain whether evidence is reference-only or final
  quotation material.
