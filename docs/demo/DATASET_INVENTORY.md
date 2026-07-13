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

Future seed tasks should create one local demo user for each existing RBAC role:

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

## Planned Workflow Seeds

The contract defines three workflow examples for later implementation:

1. `rfq-001-clean-created` - clean workflow in `CREATED`, ready to run.
2. `rfq-001-waiting-approval-history` - workflow already at
   `WAITING_APPROVAL` with representative persisted event history.
3. `rfq-001-completed-conflict` - optional terminal workflow for demonstrating
   existing runtime precondition/conflict behavior.

## Planned Event Seeds

The event history contract for `rfq-001-waiting-approval-history` includes:

- `workflow.runtime.started`
- `workflow.node.completed` for planner
- `workflow.node.completed` for retrieval
- `workflow.node.completed` for quotation
- `workflow.runtime.waiting_for_approval`

All event payloads must stay bounded and include `demo_reference: true` where
they carry static demo references.

## Idempotency Strategy

Future seed tasks should use stable natural keys:

- `demo:role:{role_name}`
- `demo:user:{email}`
- `demo:workflow:{workflow_key}`
- `demo:event:{workflow_key}:{event_key}`

`backend/app/demo/contracts.py` also exposes deterministic UUID helpers for
future seed implementations that need stable UUIDs. TASK 010.1 does not insert
or update database records.
