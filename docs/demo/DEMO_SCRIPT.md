# Demo Script

## Demo Title

Enterprise Multi-Agent OS: Automated Business Workflow Orchestration

## Scenario

A Sales user receives a procurement request from a customer. The system runs a multi-agent workflow to generate a compliant quotation and an email preview.

## Recommended First Demo Input

RFQ-001 from datasets/rfqs/rfq_samples.json.

## Expected Workflow

1. Planner identifies domain: it_equipment.
2. Retrieval finds CON-2026-ACME-IT.
3. Retrieval finds POLICY-DISCOUNT-APPROVAL and POLICY-DOMAIN-COMPLIANCE.
4. Calculator generates quote with 10% discount and 8% VAT.
5. Compliance validates warranty and payment terms.
6. Validation confirms totals.
7. Workflow waits for Manager approval.
8. Manager approves.
9. Email Agent generates preview.
10. Workflow completes.

## Expected Quote

Grand total: USD 47,628
