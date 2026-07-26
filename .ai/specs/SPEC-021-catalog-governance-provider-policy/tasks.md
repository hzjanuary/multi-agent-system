# SPEC-021 Tasks - Catalog Governance and Provider Policy

## Task List

### TASK 021.1 - Catalog Governance Policy And Version Contract

Status: Implemented as documentation.

Goal: Define the catalog governance model before any future catalog expansion
or persistence work.

Scope:

- Define catalog version identifiers, change records, review ownership, and
  validation expectations.
- Define required fields for supported item families and SKU-like demo codes.
- Define deprecation/removal policy for catalog items.
- Preserve deterministic demo defaults.

Acceptance criteria:

- Catalog versioning policy is documented.
- Supported item requirements are explicit.
- Unsupported item fail-closed behavior is preserved.
- No backend/frontend/API/database behavior is implemented in this task.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added `docs/governance/CATALOG_GOVERNANCE_POLICY.md` with catalog versioning,
  item family approval, slug naming, unsupported/mixed request handling,
  add-on compatibility, required tests, and rollback guidance.

### TASK 021.2 - Alias And Add-On Review Checklist

Status: Implemented as documentation.

Goal: Create a review checklist for customer-facing aliases and add-on
compatibility rules.

Scope:

- Define review criteria for English/Vietnamese aliases.
- Define unsupported-adjacent and false-positive checks.
- Define add-on compatibility, incompatibility, and ambiguity handling.
- Include Office 365 / Microsoft 365 as an add-on example.

Acceptance criteria:

- Alias review policy is documented.
- Add-on compatibility policy is documented.
- Mixed supported/unsupported requests remain blocked by default.
- No Telegram parser behavior changes are implemented in this task.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added alias and add-on review rules in
  `docs/governance/CATALOG_GOVERNANCE_POLICY.md`.
- Added future-change checklist items in
  `docs/governance/GOVERNANCE_CHANGE_CHECKLIST.md`.

### TASK 021.3 - Provider Evidence Trust-Level Policy

Status: Implemented as documentation.

Goal: Define trust levels for fake, manual, RAG, Tavily, and future provider
evidence.

Scope:

- Define evidence trust levels.
- Define allowed use for each trust level.
- Define warnings and manual-review requirements.
- Define criteria for promoting provider evidence from external/unverified to
  stronger internal policy status.

Acceptance criteria:

- Fake/manual/RAG/Tavily evidence policies are documented.
- Reference evidence remains separate from final quotation.
- No provider calls, live web calls, or service integrations are implemented.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added `docs/governance/PROVIDER_EVIDENCE_POLICY.md` covering trust levels,
  fake/manual/RAG/Tavily policies, no CI live key policy, no price inference
  from prose, bounding/redaction, and provider degradation.

### TASK 021.4 - Manual Review And Approval Boundary Policy

Status: Implemented as documentation.

Goal: Document how catalog/provider evidence interacts with Manager/Admin
approval and explicit resume.

Scope:

- Define manual review requirements for low-confidence, external, missing, or
  conflicting evidence.
- Preserve `/run -> WAITING_APPROVAL -> approve -> /resume -> COMPLETED`.
- Define policy-blocking or warning behavior for future implementation without
  changing current runtime behavior.

Acceptance criteria:

- Manager/Admin approval remains the final decision boundary.
- No auto-approval or auto-resume is authorized.
- No final quote, stock, delivery, or discount approval can be claimed before
  approval/resume.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added approval and resume boundaries in
  `docs/governance/APPROVAL_OUTBOUND_POLICY.md`.
- Added manual review and lifecycle checks in
  `docs/governance/GOVERNANCE_CHANGE_CHECKLIST.md`.

### TASK 021.5 - Outbound Preview/Send Governance Policy

Status: Implemented as documentation.

Goal: Define governance required before approved outbound preview can evolve
into real send-provider behavior.

Scope:

- Preserve SPEC-020 preview-only baseline.
- Define future send policy requirements for RBAC, audit, confirmation,
  provider credentials, retry/failure, and redaction.
- Keep `OUTBOUND_SEND_ENABLED=false` as the stable default.

Acceptance criteria:

- Preview and send boundaries are documented.
- Future Gmail/SMTP/provider behavior requires a separate implementation spec.
- No send endpoint, provider call, or email behavior is implemented.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added `docs/governance/APPROVAL_OUTBOUND_POLICY.md` covering preview-only
  current state, no send endpoint/button, future send requirements, audit,
  recipient/content safety, Telegram boundary, and no real email default.

### TASK 021.6 - Audit Event Requirements Planning

Status: Implemented as documentation.

Goal: Plan audit/event requirements for future catalog, evidence, review, and
outbound governance actions.

Scope:

- Define candidate event types.
- Define bounded payload requirements.
- Define forbidden payload fields.
- Define which future actions are reads and which would become mutations if
  audited.

Acceptance criteria:

- Audit requirements are documented.
- Secret/raw-payload exclusions are explicit.
- Read-only preview behavior is not changed in this planning task.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Added audit/event requirements in
  `docs/governance/APPROVAL_OUTBOUND_POLICY.md`.
- Added catalog/provider audit expectations in
  `docs/governance/CATALOG_GOVERNANCE_POLICY.md` and
  `docs/governance/PROVIDER_EVIDENCE_POLICY.md`.

### TASK 021.7 - Documentation, Validation, And Closeout

Status: Implemented / ready for closeout review.

Goal: Close SPEC-021 planning with updated index, handoff, and validation
evidence.

Scope:

- Update `.ai/specs/SPEC_INDEX.md`.
- Update `.codex/HANDOFF.md`.
- Confirm documentation is internally consistent with SPEC-018, SPEC-019, and
  SPEC-020.
- Run planning validation.

Acceptance criteria:

- SPEC-021 planning docs exist.
- SPEC index references SPEC-021 without reopening closed specs.
- Handoff points to SPEC-021 as the active planning spec.
- No product behavior is implemented.
- Governance docs exist under `docs/governance/`.

Validation:

```bash
git diff --check
git status --short
```

Implementation:

- Updated SPEC-021 status to implemented / ready for closeout review.
- Updated `.codex/HANDOFF.md` with governance docs and validation scope.
- Added a concise README link to the governance docs.

## SPEC-021 Planning Closeout Checklist

- [x] Catalog versioning policy defined.
- [x] Supported vs unsupported item governance defined.
- [x] Alias review policy defined.
- [x] Add-on compatibility policy defined.
- [x] Provider evidence trust levels defined.
- [x] Fake/manual/RAG/Tavily evidence policy defined.
- [x] Reference evidence vs final quotation boundary preserved.
- [x] Approval/resume boundary preserved.
- [x] Outbound preview/send boundary preserved.
- [x] Audit requirements planned.
- [x] Future live provider integration policy planned.
- [x] Future real email/send policy planned.
- [x] Non-goals and safety boundaries documented.
- [x] No backend behavior changed.
- [x] No frontend behavior changed.
- [x] No Telegram behavior changed.
- [x] No API behavior changed.
- [x] No database models or migrations changed.
- [x] No Docker/Compose/CI behavior changed.
- [x] No provider calls added.
