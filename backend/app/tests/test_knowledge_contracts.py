"""Tests for provider-independent knowledge base contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.knowledge.schemas import (
    MAX_ATTRIBUTE_KEYS,
    MAX_CITATION_EXCERPT_CHARS,
    MAX_SEARCH_TOP_K,
    KnowledgeChunk,
    KnowledgeChunkMetadata,
    KnowledgeCitation,
    KnowledgeDocument,
    KnowledgeDocumentMetadata,
    KnowledgeDocumentSourceType,
    KnowledgeRetrievalResult,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)


def _document_metadata() -> KnowledgeDocumentMetadata:
    return KnowledgeDocumentMetadata(
        document_id="policy-001",
        title="Procurement Policy",
        source_type=KnowledgeDocumentSourceType.POLICY,
        domain="it_equipment",
        version="2026.1",
        owner_team="Legal",
        object_storage_key="demo/policies/policy-001.md",
        checksum="abc123",
        content_type="text/markdown",
        dataset_path="datasets/policies/procurement_policy.md",
        tags=("policy", "approval", "policy"),
        attributes={"region": "APAC", "priority": 1, "flags": ["demo"]},
    )


def _citation() -> KnowledgeCitation:
    return KnowledgeCitation(
        citation_id="cite-001",
        document_id="policy-001",
        document_title="Procurement Policy",
        source_type=KnowledgeDocumentSourceType.POLICY,
        section="Approvals",
        page=2,
        excerpt="Discounts above threshold require manager approval.",
        relevance_score=0.91,
        citation_label="Procurement Policy § Approvals",
    )


def test_source_type_enum_contains_expected_values() -> None:
    assert {source_type.value for source_type in KnowledgeDocumentSourceType} >= {
        "policy",
        "contract",
        "pricing",
        "supplier_profile",
        "rfq",
        "guideline",
    }


def test_document_metadata_accepts_safe_bounded_values() -> None:
    metadata = _document_metadata()

    assert metadata.document_id == "policy-001"
    assert metadata.tags == ("policy", "approval")
    assert metadata.attributes["region"] == "APAC"


def test_document_and_chunk_contracts_validate_safe_shapes() -> None:
    metadata = _document_metadata()
    document = KnowledgeDocument(
        metadata=metadata, content="Paragraph one.\n\nParagraph two."
    )
    chunk_metadata = KnowledgeChunkMetadata(
        chunk_id="kbchunk:policy-001:0:abc123",
        document_id=metadata.document_id,
        chunk_index=0,
        citation_label="Procurement Policy chunk 1",
        source_type=metadata.source_type,
        domain=metadata.domain,
        checksum="abc123",
        character_count=11,
    )
    chunk = KnowledgeChunk(metadata=chunk_metadata, text="Chunk text.")

    assert document.metadata.source_type is KnowledgeDocumentSourceType.POLICY
    assert chunk.metadata.character_count == len(chunk.text)


def test_invalid_source_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        KnowledgeDocumentMetadata.model_validate(
            {
                "document_id": "doc-001",
                "title": "Bad Source",
                "source_type": "invoice",
                "domain": "it_equipment",
            },
        )


def test_metadata_rejects_sensitive_keys_and_non_json_values() -> None:
    with pytest.raises(ValidationError, match="sensitive"):
        KnowledgeDocumentMetadata(
            document_id="doc-001",
            title="Unsafe Metadata",
            source_type=KnowledgeDocumentSourceType.CONTRACT,
            domain="it_equipment",
            attributes={"api_key": "secret"},
        )

    with pytest.raises(ValidationError, match="JSON-compatible"):
        KnowledgeDocumentMetadata(
            document_id="doc-002",
            title="Unsafe Metadata",
            source_type=KnowledgeDocumentSourceType.CONTRACT,
            domain="it_equipment",
            attributes={"bad": object()},
        )


def test_metadata_key_count_is_bounded() -> None:
    with pytest.raises(ValidationError, match="too many keys"):
        KnowledgeDocumentMetadata(
            document_id="doc-001",
            title="Too Much Metadata",
            source_type=KnowledgeDocumentSourceType.CONTRACT,
            domain="it_equipment",
            attributes={
                f"key_{index}": index for index in range(MAX_ATTRIBUTE_KEYS + 1)
            },
        )


def test_citation_and_retrieval_result_are_bounded_and_safe() -> None:
    citation = _citation()
    result = KnowledgeRetrievalResult(
        chunk_id="kbchunk:policy-001:0:abc123",
        document_id="policy-001",
        chunk_text="Discounts above threshold require manager approval.",
        score=0.91,
        source_type=KnowledgeDocumentSourceType.POLICY,
        document_title="Procurement Policy",
        domain="it_equipment",
        citation=citation,
        metadata={"document_version": "2026.1"},
    )
    response = KnowledgeSearchResponse(query="approval discount", results=(result,))

    assert response.results == (result,)
    assert response.results[0].citation.citation_id == "cite-001"


def test_citation_excerpt_bound_is_enforced() -> None:
    with pytest.raises(ValidationError):
        KnowledgeCitation(
            citation_id="cite-001",
            document_id="policy-001",
            document_title="Procurement Policy",
            source_type=KnowledgeDocumentSourceType.POLICY,
            excerpt="x" * (MAX_CITATION_EXCERPT_CHARS + 1),
            relevance_score=0.5,
            citation_label="Policy",
        )


def test_search_request_bounds_and_filters() -> None:
    request = KnowledgeSearchRequest(
        query="  contract terms  ",
        top_k=3,
        source_types=(
            KnowledgeDocumentSourceType.CONTRACT,
            KnowledgeDocumentSourceType.POLICY,
        ),
        domain="it_equipment",
        document_ids=("contract-001",),
        minimum_score=0.2,
    )

    assert request.query == "contract terms"
    assert request.source_types == (
        KnowledgeDocumentSourceType.CONTRACT,
        KnowledgeDocumentSourceType.POLICY,
    )


def test_search_request_rejects_invalid_bounds() -> None:
    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(query="x", top_k=MAX_SEARCH_TOP_K + 1)

    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(query="   ")
