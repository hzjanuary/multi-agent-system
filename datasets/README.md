# Demo Dataset

This dataset supports the MVP demo for Enterprise Multi-Agent OS.

## Domains

- IT equipment
- Office furniture
- Facility maintenance
- Software subscription
- Logistics equipment

## Files

- customers.csv/json
- products.csv/json
- pricing_rules.csv/json
- contracts/*.md
- policies/*.md
- rfqs/rfq_samples.json
- expected_outputs/expected_quotes.json
- index/document_index.json

## Recommended Demo Order

1. RFQ-001: IT equipment, simple and easy to explain.
2. RFQ-004: Software subscription, shows VAT 0 and seat-based pricing.
3. RFQ-005: Logistics equipment, shows multi-item quotation.
4. RFQ-003: Facility maintenance, shows compliance/SLA logic.
5. RFQ-002: Office furniture, shows multi-item and installation policy.

## Retrieval Ground Truth

Each RFQ includes an expected contract_id. Retrieval Agent should cite the relevant contract and applicable policy documents.
