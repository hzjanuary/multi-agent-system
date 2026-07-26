# Catalog Governance Policy

## Purpose

This policy defines how future developers may expand the deterministic demo
catalog without weakening the current safety boundaries. Catalog support lets
the system create internal procurement workflows from known item families. It
does not create prices, stock claims, delivery promises, discounts, approvals,
or final customer quotations.

Current catalog authority:

- Planning source: `.ai/specs/SPEC-021-catalog-governance-provider-policy/spec.md`
- Implemented demo catalog: `scripts/demo/catalog.py`
- Telegram bridge integration: `scripts/demo/telegram_inbound_bridge.py`
- Current catalog version: `CATALOG_VERSION`

## Stable Boundaries

- The catalog is deterministic local-demo data.
- Catalog metadata is intake evidence only.
- Unsupported items must fail closed.
- Mixed supported and unsupported requests must not create partial workflows.
- Provider evidence and price research must not be triggered by catalog match.
- Manager/Admin approval and explicit resume remain required before any
  customer-ready final communication.

## Catalog Versioning

Every externally observable catalog behavior change requires a catalog version
review. Increment or replace the catalog version when any of these change:

- item family added, renamed, deprecated, or removed;
- item id or SKU-like slug changed;
- English or Vietnamese alias changed;
- add-on compatibility changed;
- unsupported-adjacent terms changed;
- workflow metadata shape changed;
- parser behavior changes because of catalog data.

Each version record should capture:

| Field | Requirement |
| --- | --- |
| Version id | Stable string such as `demo-catalog-v2`. |
| Effective date | Date the version becomes the active demo catalog. |
| Changed item families | Added, removed, or changed family names. |
| Changed aliases | English/Vietnamese aliases added or removed. |
| Add-on compatibility | Any compatible or incompatible add-on rule changes. |
| Reviewer | Person or role that reviewed the behavior. |
| Validation | Exact tests/gates run for the change. |
| Rollback note | How to revert safely if matching becomes too broad. |

Versioning does not imply a price list or approved quote.

## Item Family Approval Checklist

Before a new item family is treated as supported, confirm:

- [ ] Canonical display name exists.
- [ ] Stable item id or SKU-like slug exists.
- [ ] Normalized item name exists.
- [ ] Item family identifier exists.
- [ ] Unit is defined, for example `unit` or `set`.
- [ ] Domain is defined.
- [ ] English aliases are explicit.
- [ ] Vietnamese aliases are explicit when supported.
- [ ] Supported add-ons are explicit, even if empty.
- [ ] Unsupported-adjacent terms are reviewed.
- [ ] Workflow metadata remains bounded and JSON-safe.
- [ ] No price, stock, delivery, supplier credential, provider payload, or real
  customer data is added.
- [ ] Parser tests prove the item creates the expected normalized request.
- [ ] Mixed supported/unsupported tests prove no silent dropping.
- [ ] Sales and technical follow-up copy remains safe.

## SKU And Item Slug Naming Rules

Use stable snake_case identifiers:

- Good: `standard_business_laptop`, `office_monitor`,
  `wireless_keyboard_mouse_combo`
- Avoid: vendor-specific one-off names unless that vendor-specific item is
  explicitly supported and tested.
- Avoid marketing terms that imply price, discount, stock, or delivery.
- Do not include add-ons in the item slug.
- Do not include customer names, Telegram ids, provider keys, or local machine
  details.

## Alias Review Rules

Aliases are externally observable because they determine whether a customer
message creates a workflow.

Review every alias for:

- false positives against unsupported items;
- overlap with existing supported item families;
- plural and singular forms;
- abbreviations and common spelling variants;
- Vietnamese accented and unaccented forms;
- brand terms that imply unsupported SKU specificity;
- add-on terms that must remain add-ons;
- generic words that are too broad, such as `device`, `equipment`, or
  `hardware`.

Rules:

- The original customer message remains the source of truth for unsupported
  item scanning.
- LLM extraction output must still pass deterministic alias normalization.
- Aliases must not cause the bridge to create a workflow for unknown or mixed
  unsupported requests.

## Unsupported Item Handling

Unsupported item requests must not create low-quality generic workflows.

When an item is unsupported:

- technical reply should name the supported catalog scope and ask for a
  supported item;
- sales reply should explain that the current demo catalog does not contain
  that item;
- no workflow should be created unless the customer sends a supported-only
  follow-up;
- no price lookup, RAG lookup, Tavily lookup, approval, resume, or outbound
  preview should be triggered.

## Mixed Supported / Unsupported Request Policy

If one message includes both supported and unsupported items:

- do not create a partial workflow by default;
- mention the supported item that was recognized;
- mention the unsupported item that blocks the request;
- ask for a supported-only follow-up or a catalog expansion first;
- do not silently drop unsupported lines;
- do not auto-price unsupported items.

Example:

```text
báo giá 20 laptop và 5 máy chiếu
```

Expected behavior:

- laptop is recognized;
- projector is unsupported unless explicitly added in a future catalog version;
- no workflow is created until the customer sends a supported-only RFQ or the
  catalog is expanded.

## Add-On Compatibility Policy

Add-ons are not item names. A supported add-on must define:

- canonical add-on id;
- display name;
- English aliases;
- Vietnamese aliases when supported;
- compatible item families;
- incompatible item families;
- behavior for ambiguous compatibility.

Office 365 / Microsoft 365 is the current reference add-on. It may apply to
computing items such as laptops or desktop PCs, but it must not be folded into
the item name and must not imply price, license availability, delivery, or
discount approval.

If add-on compatibility is unclear:

- ask for clarification or block workflow creation;
- do not silently attach the add-on;
- do not fabricate catalog support.

## Required Tests For Catalog Expansion

Future catalog behavior changes should include focused tests for:

- supported item parsing in English;
- supported item parsing in Vietnamese when applicable;
- alias normalization;
- add-on detection and compatibility;
- incompatible add-on handling;
- unsupported-only request handling;
- mixed supported/unsupported blocking;
- LLM extraction fallback through deterministic normalization;
- sales and technical reply safety;
- workflow payload metadata shape;
- no forbidden claims: final quote, stock, delivery, discount approval, real
  email sent.

Recommended gates:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
python3 -m py_compile scripts/demo/telegram_inbound_bridge.py
git diff --check
```

Run broader backend/frontend gates when a future task touches those surfaces.

## Rollback And Removal Guidance

If a catalog change creates false positives or confusing demo behavior:

1. Revert the alias or item family change.
2. Restore the previous catalog version.
3. Add a regression test for the bad customer message.
4. Document the unsupported term if it should remain blocked.
5. Confirm the bridge no longer creates a workflow for that request.

Removing a supported item is also externally observable. Treat removal as a new
catalog version and update docs/tests so the item is clearly unsupported.

## Review Sign-Off

Before merging future catalog expansion:

- [ ] Governance owner reviewed item family and aliases.
- [ ] Safety boundary reviewed.
- [ ] Tests cover supported, unsupported, and mixed cases.
- [ ] No provider call or price lookup was introduced by catalog matching.
- [ ] No approval/resume/outbound behavior changed unless a separate spec
  explicitly scoped it.
