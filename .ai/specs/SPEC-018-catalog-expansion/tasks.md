# SPEC-018 Tasks - Catalog Expansion

## Task List

### TASK 018.1 - Catalog Data Model / Contract Planning

Status: Implemented in Sprint 1.

Goal: Define the deterministic catalog contract before implementing expanded
item parsing or workflow payload changes.

Scope:

- Define item family, SKU/code, alias, add-on, compatibility, and version
  fields.
- Decide whether the first implementation is code fixture, JSON fixture, or
  configuration file.
- Identify how catalog metadata maps into workflow create payloads without
  changing API contracts unnecessarily.
- Preserve SPEC-016 safety boundaries.

Acceptance criteria:

- Catalog contract is documented and reviewable.
- Supported item families and add-ons are explicit.
- No database migration or backend behavior is implemented in this planning
  task unless a later approved task scopes it.

Validation:

```bash
git diff --check
git status --short
```

Sprint 1 implementation:

- Added `scripts/demo/catalog.py` as the deterministic local-demo catalog
  contract.
- Catalog records include item id, display name, normalized item name, item
  family, English/Vietnamese aliases, supported add-ons, unit, domain,
  `demo_only`, and safe workflow metadata.
- Kept catalog ownership local to `scripts/demo/` to avoid backend API,
  runtime, database, or frontend behavior changes.

### TASK 018.2 - Deterministic Catalog Fixture And Tests

Status: Implemented in Sprint 1.

Goal: Add versioned deterministic catalog data and tests for the approved item
families.

Scope:

- Add catalog fixture/contract implementation.
- Cover canonical names, SKU/codes, domains, display names, aliases, and
  add-on compatibility.
- Test English and Vietnamese aliases.
- Test unsupported-adjacent terms that must not normalize accidentally.

Acceptance criteria:

- Catalog fixture is deterministic and contains no real secrets/customer data.
- Each supported item family has tested aliases.
- Office 365 / Microsoft 365 is modeled as an add-on.

Validation:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
docker compose run --rm backend-test pytest -q
git diff --check
```

Sprint 1 implementation:

- Added deterministic catalog fixture entries for:
  - Standard business laptop
  - Business desktop PC
  - Office monitor
  - Office printer
  - Wireless keyboard and mouse combo
  - Office 365 / Microsoft 365 add-on
- Added unittest coverage for required item families, English/Vietnamese alias
  normalization, and Office 365 add-on compatibility.
- Catalog contains no prices, stock, delivery promises, provider keys, or real
  customer data.

### TASK 018.3 - Parser Alias Expansion For Supported Catalog Items

Status: Implemented in Sprint 1.

Goal: Expand deterministic Telegram/parser normalization to use the catalog
fixture for supported items.

Scope:

- Preserve existing laptop and Office 365 behavior.
- Add aliases for desktop PC, monitor, printer, and keyboard/mouse combo.
- Preserve greeting, missing quantity, unknown item, and unsupported item
  behavior.
- Do not add LLM dependency or web lookup.

Acceptance criteria:

- Supported catalog item messages create normalized parse results.
- Unsupported messages still ask follow-up.
- Existing Vietnamese/English laptop tests still pass.

Validation:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
python3 -m py_compile scripts/demo/telegram_inbound_bridge.py
git diff --check
```

Sprint 1 implementation:

- Updated `scripts/demo/telegram_inbound_bridge.py` to use the deterministic
  catalog for quantity/item parsing and LLM-result canonicalization.
- Preserved existing laptop and Office 365 behavior.
- Added supported parser examples for desktop PCs, office monitors, office
  printers, and wireless keyboard/mouse combos in English and Vietnamese.
- Added catalog metadata to existing workflow payload metadata attributes only;
  no backend API/schema change was required.

### TASK 018.4 - Mixed-Item Safety Hardening

Status: Implemented in Sprint 1.

Goal: Ensure expanded catalog support does not reintroduce silent item dropping.

Scope:

- Extend mixed supported/unsupported detection for the expanded item set.
- Add tests for multiple supported items, supported plus unsupported items, and
  unsupported-only items.
- Require explicit follow-up when item support is ambiguous.

Acceptance criteria:

- Mixed supported/unsupported messages do not create partial workflows.
- Technical and sales reply modes explain the supported and unsupported parts
  safely.
- No price, stock, delivery, approval, or email claim is introduced.

Validation:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
git diff --check
```

Sprint 1 implementation:

- Replaced the old printer-specific unsupported guard now that printers are
  supported catalog items.
- Added unsupported detection for projector / `máy chiếu`, server / `máy chủ`,
  phone / `điện thoại`, camera / `camera giám sát`, and router /
  `bộ định tuyến`.
- Preserved original customer text as the source of truth for mixed-item
  safety, including LLM extraction paths.
- Added tests proving supported plus unsupported requests do not create partial
  workflows and unsupported-only requests do not create workflows.

### TASK 018.5 - Workflow Payload Catalog Metadata

Status: Planned. Sprint 1 added bounded catalog metadata to existing Telegram
workflow payload attributes only; broader workflow metadata design remains
planned.

Goal: Attach bounded catalog metadata to workflow create payloads when parser
normalization succeeds.

Scope:

- Include catalog version, normalized item family, SKU/code, and add-on metadata
  where existing workflow schemas safely allow it.
- Do not include raw prompts, raw provider payloads, secrets, or fabricated
  evidence.
- Do not require API contract changes unless explicitly approved during the
  task.

Acceptance criteria:

- Workflow payload metadata is bounded and JSON-safe.
- Existing workflow creation remains compatible.
- Manager/Admin approval boundary remains unchanged.

Validation:

```bash
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
docker compose run --rm backend-test pytest -q
git diff --check
```

### TASK 018.6 - Frontend Catalog Display Polish If Needed

Status: Planned.

Goal: Show normalized catalog metadata where it already exists in workflow
state without fabricating catalog data.

Scope:

- Update Agent Monitor/workflow detail only if workflow state exposes catalog
  metadata.
- Keep empty states honest.
- Preserve approval/resume controls and reference evidence panels.

Acceptance criteria:

- Frontend displays catalog metadata as intake evidence, not pricing proof.
- No fake records, fake prices, stock/delivery claims, or final quote wording.

Validation:

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
git diff --check
```

### TASK 018.7 - Final Validation And Docs

Status: Planned.

Goal: Close SPEC-018 with updated docs, runbooks, and full validation.

Scope:

- Update Telegram/demo/operator docs for expanded catalog behavior.
- Document supported item families and examples.
- Confirm deterministic no-key demo remains stable.
- Run relevant backend/script/frontend gates.

Acceptance criteria:

- SPEC-018 is ready for review/closure.
- Expanded catalog behavior is documented honestly.
- No final quote, stock, delivery, fake external price, provider call, or
  unsupported item dropping is introduced.

Validation:

```bash
git status --short
python3 -m unittest scripts.demo.test_telegram_inbound_bridge
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/ci/all-gates.sh
git diff --check
```
