# Demo Dataset Inventory

SPEC-010 uses the existing `datasets/` folder as static reference data for a
local board-ready procurement workflow demo. This document inventories the
assets and ties them to the seed contract in `backend/app/demo/contracts.py`.

## Source Files

| Dataset | Path | Use |
| --- | --- | --- |
| Customers | `datasets/customers.json` and `datasets/customers.csv` | Customer metadata for workflow state and demo copy |
| Products | `datasets/products.json` and `datasets/products.csv` | Product references for RFQ items |
| Pricing rules | `datasets/pricing_rules.json` and `datasets/pricing_rules.csv` | Static discount/reference metadata only |
| Contracts | `datasets/contracts/*.md` | Static contract references for future retrieval demos |
| Policies | `datasets/policies/*.md` | Static policy references for future compliance demos |
| RFQs | `datasets/rfqs/rfq_samples.json` | Procurement request inputs |
| Expected outputs | `datasets/expected_outputs/expected_quotes.json` | Static quotation reference outputs |
| Document index | `datasets/index/document_index.json` | Static lookup index for later retrieval work |

## Primary Demo Path

The primary board demo uses RFQ-001:

- Domain: `it_equipment`
- Customer: `CUST-001` / Acme Manufacturing Group
- Product: `IT-LAP-001`
- Quantity: `50`
- Contract reference: `CON-2026-ACME-IT`
- Expected static total: `47628 USD`
- Runtime stopping point: `WAITING_APPROVAL`

The expected total and contract references are demo seed metadata only in
SPEC-010. They do not mean real retrieval, pricing, compliance, approval, email,
LLM, or RAG behavior has been implemented.

## Demo User Contract

TASK 010.2 provides an explicit local/demo seed helper for one user per
existing RBAC role:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@example.test` | `DemoPassword123!` |
| Manager | `manager@example.test` | `DemoPassword123!` |
| Sales | `sales@example.test` | `DemoPassword123!` |
| Legal | `legal@example.test` | `DemoPassword123!` |
| Finance | `finance@example.test` | `DemoPassword123!` |
| Viewer | `viewer@example.test` | `DemoPassword123!` |

These credentials are local-demo only. They are intentionally obvious and must
not be reused as production defaults.

The helper lives in `backend/app/demo/user_seed.py` and exposes
`seed_demo_roles_and_users(session)`. It uses existing `User` and `Role` models,
hashes passwords through the existing Argon2 password utility, flushes changes,
and leaves commit/rollback to the caller. It does not seed workflows or events,
does not expose a public API, and does not run automatically.

## Demo Workflow Seeds

TASK 010.3 and SPEC-012 provide an explicit local/demo seed helper for the
workflow examples defined by the contract:

1. `rfq-001-clean-created` - clean workflow in `CREATED`, ready to run.
2. `rfq-001-waiting-approval-history` - workflow already at
   `WAITING_APPROVAL` with representative persisted event history and no final
   approval decision, so Manager/Admin can approve it live.
3. `rfq-001-approved-ready-to-resume` - workflow in `APPROVED` with a final
   approval record and `approval_state.can_resume=true` for explicit resume.
4. `rfq-001-completed-resumed-history` - workflow in `COMPLETED` with
   request-changes, approval, email-preparation, and resume event history.
5. `rfq-001-rejected-history` - workflow in `REJECTED` with read-only approval
   rejection history.
6. `rfq-001-completed-conflict` - optional terminal workflow for demonstrating
   existing runtime precondition/conflict behavior.

The helper lives in `backend/app/demo/workflow_seed.py` and exposes
`seed_demo_workflows_and_events(session)`. It ensures demo users/roles through
the TASK 010.2 helper, creates deterministic workflow IDs from the seed
contract, stores demo idempotency keys in workflow metadata, flushes changes,
and leaves commit/rollback to the caller. It does not run workflows, expose a
public API, publish live events, or run automatically.

## Demo Event Seeds

The event history contract for `rfq-001-waiting-approval-history` includes:

- `workflow.runtime.started`
- `workflow.node.completed` for planner
- `workflow.node.completed` for retrieval
- `workflow.node.completed` for quotation
- `workflow.runtime.waiting_for_approval`

Additional SPEC-012 demo examples include persisted approval and resume events:

- `workflow.approval.approved`
- `workflow.approval.rejected`
- `workflow.approval.changes_requested`
- `workflow.resume_requested`
- `workflow.node.started` for `email_preparation`
- `workflow.node.completed` for `email_preparation`
- `workflow.resumed`

All event payloads must stay bounded and include `demo_reference: true` where
they carry static demo references.

TASK 010.3 persists these as deterministic `WorkflowEvent` records with stable
event IDs and stable event timestamps so timeline readback order is repeatable.

## Idempotency Strategy

Future seed tasks should use stable natural keys:

- `demo:role:{role_name}`
- `demo:user:{email}`
- `demo:workflow:{workflow_key}`
- `demo:event:{workflow_key}:{event_key}`

`backend/app/demo/contracts.py` also exposes deterministic UUID helpers for
seed implementations that need stable UUIDs.

## Demo Seed Command

TASK 010.4 provides an explicit local/demo seed command:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --confirm-local-demo
```

The command runs the demo user/role seed helper and the demo workflow/event
seed helper in one transaction. It commits once after all seed steps succeed
and rolls back on failure. It does not run on import, backend startup, or
through any public API endpoint.

For a non-persisting check, run:

```bash
docker-compose run --rm backend-test python -m app.demo.seed --dry-run
```

The mutating command requires `--confirm-local-demo` to make the local/demo-only
scope explicit. It prints a bounded summary of created/reused roles, users,
workflows, and events without printing password hashes.

## Demo Knowledge Documents

TASK 013.3 adds deterministic local-demo knowledge documents for future RAG
retrieval and citation demos. The definitions live in
`backend/app/demo/knowledge_documents.py` and are ingested explicitly by the
knowledge ingestion CLI. They cover:

| Document ID | Source type | Source dataset reference |
| --- | --- | --- |
| `demo-kb-procurement-policy` | `policy` | `datasets/policies/POLICY-DISCOUNT-APPROVAL.md` |
| `demo-kb-acme-contract-terms` | `contract` | `datasets/contracts/CON-2026-ACME-IT.md` |
| `demo-kb-supplier-evaluation-notes` | `supplier_profile` | `datasets/index/document_index.json` |
| `demo-kb-pricing-guideline` | `pricing` | `datasets/pricing_rules.json` |
| `demo-kb-compliance-checklist` | `compliance_checklist` | `datasets/policies/POLICY-DOMAIN-COMPLIANCE.md` |

Each document has a stable document ID, deterministic checksum, bounded demo
content, and deterministic object storage key under `demo/knowledge/`.

## Demo Knowledge Ingestion Command

TASK 013.3 provides an explicit local-demo knowledge ingestion command:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

The command chunks the deterministic demo knowledge documents, embeds chunks
with the default fake embedding provider, stores original source text in MinIO,
and upserts chunk vectors and safe metadata into Qdrant. It does not run on
backend startup and is not exposed through a public API endpoint.

For a non-persisting check:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo --dry-run --json
```

Rerunning the confirmed ingestion command is safe: object keys and vector point
IDs are deterministic, so MinIO objects are overwritten/reused and Qdrant points
are upserted without duplicate chunks.

TASK 013.4 adds read-only authenticated knowledge APIs for the ingested demo
knowledge:

```text
POST /api/v1/knowledge/search
GET  /api/v1/knowledge/documents
GET  /api/v1/knowledge/documents/{document_id}
```

Search uses the configured embedding service, which defaults to deterministic
fake embeddings for local/demo use, and queries Qdrant through the existing
vector store abstraction. Results include bounded chunk text and citation
metadata only; raw embeddings and raw vector payloads are not API responses.

Runtime RAG grounding, frontend evidence panels, upload UI, migrations, and
database models remain deferred to later SPEC-013 tasks.
