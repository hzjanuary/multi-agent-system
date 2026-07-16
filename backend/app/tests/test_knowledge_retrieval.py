"""Tests for provider-independent knowledge retrieval service."""

from __future__ import annotations

import pytest

from app.demo.knowledge_documents import DEMO_KNOWLEDGE_DOCUMENTS
from app.knowledge.embeddings import (
    EmbeddingService,
    EmbeddingSettings,
    FakeEmbeddingClient,
)
from app.knowledge.retrieval import KnowledgeRetrievalService
from app.knowledge.schemas import (
    KnowledgeDocumentSourceType,
    KnowledgeSearchRequest,
)
from app.vectorstore import VectorPoint, VectorSearchResult


class FakeVectorStore:
    def __init__(
        self,
        *,
        results: list[VectorSearchResult] | None = None,
        collection_exists: bool = True,
    ) -> None:
        self.results = results or []
        self.collection_exists_value = collection_exists
        self.search_calls = 0
        self.last_query_vector: list[float] | None = None
        self.last_limit: int | None = None
        self.last_filters: dict[str, object] | None = None

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
    ) -> None:
        return None

    async def collection_exists(self, collection_name: str) -> bool:
        return self.collection_exists_value

    async def upsert(
        self,
        collection_name: str,
        points: list[VectorPoint],
    ) -> None:
        return None

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, object] | None = None,
    ) -> list[VectorSearchResult]:
        self.search_calls += 1
        self.last_query_vector = query_vector
        self.last_limit = limit
        self.last_filters = filters
        return self.results

    async def delete(self, collection_name: str, point_ids: list[str]) -> None:
        return None

    async def close(self) -> None:
        return None


def _service(vector_store: FakeVectorStore) -> KnowledgeRetrievalService:
    return KnowledgeRetrievalService(
        vector_store=vector_store,
        embedding_service=EmbeddingService(
            FakeEmbeddingClient(EmbeddingSettings(dimensions=8)),
        ),
        collection_name="test_demo_knowledge",
    )


def _result(
    *,
    document_id: str = "demo-kb-acme-contract-terms",
    source_type: str = "contract",
    domain: str = "procurement",
    score: float = 0.82,
    chunk_id: str = "kbchunk:demo-kb-acme-contract-terms:0:abc123",
    text: str = "Framework Discount: 10 percent for laptop orders.",
) -> VectorSearchResult:
    return VectorSearchResult(
        id="point-1",
        score=score,
        payload={
            "document_id": document_id,
            "title": "Acme IT Equipment Contract Terms",
            "source_type": source_type,
            "domain": domain,
            "checksum": "abc123",
            "chunk_id": chunk_id,
            "chunk_index": 0,
            "citation_label": "Acme IT Equipment Contract Terms chunk 1",
            "character_count": len(text),
            "text": text,
            "embedding_provider": "fake",
            "embedding_model": "fake-hash-embedding",
            "embedding_dimensions": 8,
            "demo_seed": True,
            "demo_reference_only": True,
            "raw_prompt": "must-not-leak",
        },
    )


@pytest.mark.asyncio
async def test_search_embeds_query_and_maps_safe_citation_result() -> None:
    vector_store = FakeVectorStore(results=[_result()])
    service = _service(vector_store)

    response = await service.search(KnowledgeSearchRequest(query="discount terms"))

    assert vector_store.search_calls == 1
    assert vector_store.last_query_vector is not None
    assert len(vector_store.last_query_vector) == 8
    assert vector_store.last_limit == 5
    assert response.query == "discount terms"
    assert len(response.results) == 1
    result = response.results[0]
    assert result.document_id == "demo-kb-acme-contract-terms"
    assert result.source_type is KnowledgeDocumentSourceType.CONTRACT
    assert result.citation.document_title == "Acme IT Equipment Contract Terms"
    assert result.citation.relevance_score == 0.82
    assert "raw_prompt" not in result.metadata
    assert "raw_prompt" not in result.model_dump_json().lower()


@pytest.mark.asyncio
async def test_search_returns_empty_when_collection_is_absent() -> None:
    vector_store = FakeVectorStore(collection_exists=False)
    service = _service(vector_store)

    response = await service.search(KnowledgeSearchRequest(query="policy"))

    assert response.results == ()
    assert vector_store.search_calls == 0


@pytest.mark.asyncio
async def test_search_respects_native_and_service_side_filters() -> None:
    vector_store = FakeVectorStore(
        results=[
            _result(source_type="contract", score=0.75),
            _result(
                document_id="demo-kb-pricing-guideline",
                source_type="pricing",
                score=0.6,
                chunk_id="kbchunk:demo-kb-pricing-guideline:0:def456",
            ),
            _result(
                document_id="other-doc",
                source_type="pricing",
                score=0.2,
                chunk_id="kbchunk:other-doc:0:def456",
            ),
        ],
    )
    service = _service(vector_store)

    response = await service.search(
        KnowledgeSearchRequest(
            query="pricing discount",
            top_k=2,
            source_types=(
                KnowledgeDocumentSourceType.CONTRACT,
                KnowledgeDocumentSourceType.PRICING,
            ),
            domain="procurement",
            document_ids=(
                "demo-kb-acme-contract-terms",
                "demo-kb-pricing-guideline",
            ),
            minimum_score=0.5,
        ),
    )

    assert vector_store.last_filters == {"domain": "procurement"}
    assert vector_store.last_limit == 8
    assert [result.document_id for result in response.results] == [
        "demo-kb-acme-contract-terms",
        "demo-kb-pricing-guideline",
    ]


@pytest.mark.asyncio
async def test_single_value_filters_are_sent_to_vector_store() -> None:
    vector_store = FakeVectorStore(results=[_result()])
    service = _service(vector_store)

    await service.search(
        KnowledgeSearchRequest(
            query="contract",
            top_k=3,
            source_types=(KnowledgeDocumentSourceType.CONTRACT,),
            domain="procurement",
            document_ids=("demo-kb-acme-contract-terms",),
        ),
    )

    assert vector_store.last_filters == {
        "source_type": "contract",
        "domain": "procurement",
        "document_id": "demo-kb-acme-contract-terms",
    }
    assert vector_store.last_limit == 3


@pytest.mark.asyncio
async def test_malformed_vector_payload_is_skipped_safely() -> None:
    vector_store = FakeVectorStore(
        results=[
            VectorSearchResult(id="bad", score=0.9, payload={"raw_payload": "bad"}),
            _result(),
        ],
    )
    service = _service(vector_store)

    response = await service.search(KnowledgeSearchRequest(query="contract"))

    assert len(response.results) == 1
    assert response.results[0].document_id == "demo-kb-acme-contract-terms"


@pytest.mark.asyncio
async def test_catalog_list_and_detail_return_bounded_demo_metadata() -> None:
    service = _service(FakeVectorStore())

    list_response = await service.list_documents()
    detail_response = await service.get_document("demo-kb-procurement-policy")

    assert list_response.count == len(DEMO_KNOWLEDGE_DOCUMENTS)
    assert list_response.documents[0].document_id == "demo-kb-procurement-policy"
    assert detail_response.document.document_id == "demo-kb-procurement-policy"
    assert detail_response.content_preview is not None
    assert len(detail_response.content_preview) <= 1200
