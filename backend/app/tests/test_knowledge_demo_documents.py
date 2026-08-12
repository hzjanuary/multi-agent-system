"""Tests for deterministic demo knowledge document definitions."""

from __future__ import annotations

from decimal import Decimal

from app.demo.knowledge_documents import DEMO_KNOWLEDGE_DOCUMENTS
from app.knowledge.chunking import chunk_document, sha256_normalized_text
from app.knowledge.schemas import KnowledgeDocumentSourceType


def test_demo_knowledge_documents_cover_required_source_types() -> None:
    source_types = {
        document.metadata.source_type for document in DEMO_KNOWLEDGE_DOCUMENTS
    }

    assert {
        KnowledgeDocumentSourceType.POLICY,
        KnowledgeDocumentSourceType.CONTRACT,
        KnowledgeDocumentSourceType.SUPPLIER_PROFILE,
        KnowledgeDocumentSourceType.PRICING,
        KnowledgeDocumentSourceType.COMPLIANCE_CHECKLIST,
    }.issubset(source_types)


def test_demo_knowledge_documents_have_stable_safe_metadata() -> None:
    document_ids = [
        document.metadata.document_id for document in DEMO_KNOWLEDGE_DOCUMENTS
    ]
    object_keys = [
        document.metadata.object_storage_key for document in DEMO_KNOWLEDGE_DOCUMENTS
    ]

    assert len(document_ids) == len(set(document_ids))
    assert all(document_id.startswith("demo-kb-") for document_id in document_ids)
    assert all(key and key.startswith("demo/knowledge/") for key in object_keys)
    assert all(
        document.metadata.domain == "procurement"
        for document in DEMO_KNOWLEDGE_DOCUMENTS
    )
    assert all(
        document.metadata.attributes["demo_seed"] is True
        for document in DEMO_KNOWLEDGE_DOCUMENTS
    )


def test_demo_knowledge_checksums_and_chunks_are_deterministic() -> None:
    first_document = DEMO_KNOWLEDGE_DOCUMENTS[0]
    first_chunking = chunk_document(first_document)
    second_chunking = chunk_document(first_document)

    assert first_document.metadata.checksum == sha256_normalized_text(
        first_document.content
    )
    assert first_chunking == second_chunking
    assert first_chunking.chunks[0].metadata.chunk_id.startswith(
        f"kbchunk:{first_document.metadata.document_id}:0:"
    )


def test_demo_pricing_documents_have_structured_internal_catalog_prices() -> None:
    expected = {
        "Standard business laptop": Decimal("18500000"),
        "Office printer": Decimal("4500000"),
        "Office monitor": Decimal("3200000"),
    }
    pricing_documents = {
        document.metadata.attributes["normalized_item_name"]: document
        for document in DEMO_KNOWLEDGE_DOCUMENTS
        if document.metadata.attributes.get("normalized_item_name") in expected
    }

    assert set(pricing_documents) == set(expected)
    for item_name, document in pricing_documents.items():
        metadata = document.metadata
        assert metadata.source_type is KnowledgeDocumentSourceType.PRICING
        assert metadata.attributes["observed_price"] == str(expected[item_name])
        assert Decimal(str(metadata.attributes["observed_price"])) > 0
        assert metadata.attributes["currency"] == "VND"
        assert metadata.attributes["quantity_basis"] == 1
        assert metadata.attributes["price_label"] == (
            "Internal demo catalog unit price"
        )
