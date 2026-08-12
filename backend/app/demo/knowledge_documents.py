"""Deterministic local-demo knowledge documents for SPEC-013 ingestion.

This module defines static document content only. It does not open files,
connect to object storage, create Qdrant collections, or run ingestion.
"""

from __future__ import annotations

from datetime import date

from app.knowledge.chunking import sha256_normalized_text
from app.knowledge.schemas import (
    KnowledgeDocument,
    KnowledgeDocumentMetadata,
    KnowledgeDocumentSourceType,
)

DEMO_KNOWLEDGE_DOMAIN = "procurement"


def _document(
    *,
    document_id: str,
    title: str,
    source_type: KnowledgeDocumentSourceType,
    version: str,
    effective_date: date,
    owner_team: str,
    dataset_path: str,
    tags: tuple[str, ...],
    attributes: dict[str, str | bool | int | float],
    content: str,
) -> KnowledgeDocument:
    object_storage_key = f"demo/knowledge/{document_id}.txt"
    return KnowledgeDocument(
        metadata=KnowledgeDocumentMetadata(
            document_id=document_id,
            title=title,
            source_type=source_type,
            domain=DEMO_KNOWLEDGE_DOMAIN,
            version=version,
            effective_date=effective_date,
            owner_team=owner_team,
            object_storage_key=object_storage_key,
            checksum=sha256_normalized_text(content),
            content_type="text/plain",
            dataset_path=dataset_path,
            tags=tags,
            attributes={
                **attributes,
                "demo_seed": True,
                "demo_reference_only": True,
            },
        ),
        content=content,
    )


DEMO_KNOWLEDGE_DOCUMENTS: tuple[KnowledgeDocument, ...] = (
    _document(
        document_id="demo-kb-procurement-policy",
        title="Demo Procurement Policy",
        source_type=KnowledgeDocumentSourceType.POLICY,
        version="2026.1",
        effective_date=date(2026, 1, 1),
        owner_team="Procurement Operations",
        dataset_path="datasets/policies/POLICY-DISCOUNT-APPROVAL.md",
        tags=("demo", "policy", "approval", "discount"),
        attributes={"policy_id": "POLICY-DISCOUNT-APPROVAL"},
        content=(
            "Any discount above the contract framework discount must be approved "
            "by a Manager.\n\n"
            "Any discount above 15 percent must be approved by a Director.\n\n"
            "Discounts must not reduce gross margin below the product minimum "
            "margin.\n\n"
            "The quotation must explicitly show subtotal, discount amount, "
            "taxable amount, VAT and total."
        ),
    ),
    _document(
        document_id="demo-kb-acme-contract-terms",
        title="Acme IT Equipment Contract Terms",
        source_type=KnowledgeDocumentSourceType.CONTRACT,
        version="2026.05",
        effective_date=date(2026, 5, 1),
        owner_team="Legal",
        dataset_path="datasets/contracts/CON-2026-ACME-IT.md",
        tags=("demo", "contract", "acme", "it_equipment"),
        attributes={"contract_id": "CON-2026-ACME-IT", "customer_id": "CUST-001"},
        content=(
            "Customer: Acme Manufacturing Group.\n\n"
            "Domain: IT Equipment.\n\n"
            "Effective Date: 2026-05-01.\n\n"
            "Payment Terms: Net 30.\n\n"
            "Framework Discount: 10 percent for laptop orders of 50 units or "
            "more.\n\n"
            "Maximum Discount Without Director Approval: 12 percent.\n\n"
            "Warranty Requirement: Minimum 24 months.\n\n"
            "Penalty Clause: Late delivery penalty of 1 percent of order value "
            "per delayed week, capped at 5 percent.\n\n"
            "Compliance Note: Quotes must include warranty, delivery schedule "
            "and payment terms."
        ),
    ),
    _document(
        document_id="demo-kb-supplier-evaluation-notes",
        title="Demo Supplier Evaluation Notes",
        source_type=KnowledgeDocumentSourceType.SUPPLIER_PROFILE,
        version="2026.1",
        effective_date=date(2026, 3, 15),
        owner_team="Supplier Management",
        dataset_path="datasets/index/document_index.json",
        tags=("demo", "supplier", "evaluation", "it_equipment"),
        attributes={"supplier_tier": "preferred", "risk_rating": "low"},
        content=(
            "Preferred IT equipment suppliers should provide business laptop "
            "models with at least 24 months warranty.\n\n"
            "Delivery plans should include shipment window, support contact, "
            "and replacement procedure.\n\n"
            "For Acme Manufacturing Group quotations, supplier evidence should "
            "align with the master agreement warranty and delivery obligations."
        ),
    ),
    _document(
        document_id="demo-kb-pricing-guideline",
        title="Demo Pricing Guideline",
        source_type=KnowledgeDocumentSourceType.PRICING,
        version="2026.1",
        effective_date=date(2026, 1, 1),
        owner_team="Finance",
        dataset_path="datasets/pricing_rules.json",
        tags=("demo", "pricing", "discount", "it_equipment"),
        attributes={"rule_id": "PR-IT-001", "currency": "USD"},
        content=(
            "For IT equipment orders, pricing rule PR-IT-001 applies when the "
            "minimum quantity is 50 units.\n\n"
            "The applicable framework discount is 10 percent and the quotation "
            "requires manager approval.\n\n"
            "The business laptop reference product IT-LAP-001 has unit price "
            "980 USD, VAT 8 percent, and minimum margin 12 percent."
        ),
    ),
    _document(
        document_id="demo-kb-standard-business-laptop-price",
        title="Internal Demo Catalog - Standard Business Laptop",
        source_type=KnowledgeDocumentSourceType.PRICING,
        version="demo-2026.1",
        effective_date=date(2026, 1, 1),
        owner_team="Demo Catalog",
        dataset_path="datasets/demo/internal_catalog_pricing.json",
        tags=("demo", "pricing", "internal_catalog", "laptop"),
        attributes={
            "catalog_item_id": "standard_business_laptop",
            "normalized_item_name": "Standard business laptop",
            "observed_price": "18500000",
            "currency": "VND",
            "unit": "unit",
            "quantity_basis": 1,
            "price_label": "Internal demo catalog unit price",
        },
        content=(
            "Internal demo catalog reference for Standard business laptop. "
            "This local demo value is not a live vendor price and requires "
            "human approval before any quotation release."
        ),
    ),
    _document(
        document_id="demo-kb-office-printer-price",
        title="Internal Demo Catalog - Office Printer",
        source_type=KnowledgeDocumentSourceType.PRICING,
        version="demo-2026.1",
        effective_date=date(2026, 1, 1),
        owner_team="Demo Catalog",
        dataset_path="datasets/demo/internal_catalog_pricing.json",
        tags=("demo", "pricing", "internal_catalog", "printer"),
        attributes={
            "catalog_item_id": "office_printer",
            "normalized_item_name": "Office printer",
            "observed_price": "4500000",
            "currency": "VND",
            "unit": "unit",
            "quantity_basis": 1,
            "price_label": "Internal demo catalog unit price",
        },
        content=(
            "Internal demo catalog reference for Office printer. This local "
            "demo value is not a live vendor price and requires human approval "
            "before any quotation release."
        ),
    ),
    _document(
        document_id="demo-kb-office-monitor-price",
        title="Internal Demo Catalog - Office Monitor",
        source_type=KnowledgeDocumentSourceType.PRICING,
        version="demo-2026.1",
        effective_date=date(2026, 1, 1),
        owner_team="Demo Catalog",
        dataset_path="datasets/demo/internal_catalog_pricing.json",
        tags=("demo", "pricing", "internal_catalog", "monitor"),
        attributes={
            "catalog_item_id": "office_monitor",
            "normalized_item_name": "Office monitor",
            "observed_price": "3200000",
            "currency": "VND",
            "unit": "unit",
            "quantity_basis": 1,
            "price_label": "Internal demo catalog unit price",
        },
        content=(
            "Internal demo catalog reference for Office monitor. This local "
            "demo value is not a live vendor price and requires human approval "
            "before any quotation release."
        ),
    ),
    _document(
        document_id="demo-kb-compliance-checklist",
        title="Demo Compliance Checklist",
        source_type=KnowledgeDocumentSourceType.COMPLIANCE_CHECKLIST,
        version="2026.1",
        effective_date=date(2026, 2, 1),
        owner_team="Compliance",
        dataset_path="datasets/policies/POLICY-DOMAIN-COMPLIANCE.md",
        tags=("demo", "compliance", "checklist", "approval"),
        attributes={"checklist_id": "DEMO-COMPLIANCE-IT-001"},
        content=(
            "IT equipment quotations must include warranty terms, delivery "
            "schedule, payment terms, and discount explanation.\n\n"
            "The compliance reviewer should confirm that manager approval is "
            "present when a discount requires human review.\n\n"
            "Customer-facing email preview must not be prepared before final "
            "human approval."
        ),
    ),
)

__all__ = ["DEMO_KNOWLEDGE_DOCUMENTS", "DEMO_KNOWLEDGE_DOMAIN"]
