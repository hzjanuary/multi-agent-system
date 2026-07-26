"""Tests for internal RAG price research evidence mapping."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.knowledge.schemas import (
    KnowledgeCitation,
    KnowledgeDocumentSourceType,
    KnowledgeRetrievalResult,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.price_research import (
    FakePriceResearchProvider,
    ManualPriceResearchProvider,
    PriceResearchProviderError,
    PriceResearchRequest,
    PriceResearchResult,
    PriceResearchService,
    PriceResearchSourceType,
    RAGPriceResearchProvider,
    get_price_research_provider,
)
from app.price_research.rag_provider import (
    NO_INTERNAL_EVIDENCE_WARNING,
    NO_STRUCTURED_PRICE_WARNING,
    RAG_REFERENCE_WARNING,
)


def _request() -> PriceResearchRequest:
    return PriceResearchRequest(
        item_name="laptop",
        normalized_item_name="Standard business laptop",
        quantity=20,
        region="VN",
        currency="VND",
        requested_addons=("office_365",),
        request_text="bao gia 20 laptop office 365",
    )


def _retrieval_result(
    *,
    metadata: dict[str, object] | None = None,
    chunk_text: str = "Internal laptop pricing note.",
    score: float = 0.82,
) -> KnowledgeRetrievalResult:
    citation = KnowledgeCitation(
        citation_id="citation-laptop-pricing-1",
        document_id="pricing-laptop-2026",
        document_title="Laptop pricing policy",
        source_type=KnowledgeDocumentSourceType.PRICING,
        section="reference-prices",
        page=1,
        excerpt="Standard business laptop reference evidence.",
        relevance_score=score,
        citation_label="Laptop pricing policy, reference-prices",
    )
    return KnowledgeRetrievalResult(
        chunk_id="chunk-laptop-pricing-1",
        document_id="pricing-laptop-2026",
        chunk_text=chunk_text,
        score=score,
        source_type=KnowledgeDocumentSourceType.PRICING,
        document_title="Laptop pricing policy",
        domain="it_equipment",
        citation=citation,
        metadata=metadata or {},
    )


def _search_response(
    results: tuple[KnowledgeRetrievalResult, ...],
) -> KnowledgeSearchResponse:
    return KnowledgeSearchResponse(query="Standard business laptop", results=results)


@pytest.mark.asyncio
async def test_rag_provider_returns_sources_from_internal_knowledge() -> None:
    seen_request: KnowledgeSearchRequest | None = None

    async def knowledge_search(
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        nonlocal seen_request
        seen_request = request
        return _search_response((_retrieval_result(),))

    result = await RAGPriceResearchProvider(knowledge_search).research_price(_request())

    assert seen_request is not None
    assert "Standard business laptop" in seen_request.query
    assert "office_365" in seen_request.query
    assert result.provider == "rag"
    assert result.is_final_quote is False
    assert result.sources[0].source_type is PriceResearchSourceType.RAG
    assert result.sources[0].title == "Laptop pricing policy"
    assert result.sources[0].snippet == "Standard business laptop reference evidence."
    assert result.reference_prices == ()
    assert NO_STRUCTURED_PRICE_WARNING in result.warnings
    assert RAG_REFERENCE_WARNING in result.warnings


@pytest.mark.asyncio
async def test_rag_provider_structured_metadata_produces_reference_price() -> None:
    metadata = {
        "observed_price": "12500000",
        "currency": "vnd",
        "unit": "unit",
        "quantity_basis": 1,
        "price_label": "Internal catalog reference unit price",
        "retrieved_at": "2026-07-24T12:00:00+00:00",
        "source_url": "https://example.test/internal-laptop-policy",
    }

    async def knowledge_search(
        _request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        return _search_response((_retrieval_result(metadata=metadata),))

    result = await RAGPriceResearchProvider(knowledge_search).research_price(_request())

    assert result.sources[0].source_type is PriceResearchSourceType.RAG
    assert result.sources[0].observed_price == Decimal("12500000")
    assert result.sources[0].currency == "VND"
    assert result.sources[0].url == "https://example.test/internal-laptop-policy"
    assert result.reference_prices[0].label == "Internal catalog reference unit price"
    assert result.reference_prices[0].amount == Decimal("12500000")
    assert result.reference_prices[0].currency == "VND"
    assert result.reference_prices[0].source_index == 0
    assert result.retrieved_at == datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
    assert NO_STRUCTURED_PRICE_WARNING not in result.warnings
    _assert_no_forbidden_positive_claims(result)


@pytest.mark.asyncio
async def test_rag_provider_unstructured_only_result_does_not_infer_price() -> None:
    async def knowledge_search(
        _request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        return _search_response(
            (
                _retrieval_result(
                    chunk_text=(
                        "Supplier note says the laptop may cost 12,500,000 VND, "
                        "but this is unstructured prose."
                    ),
                ),
            ),
        )

    result = await RAGPriceResearchProvider(knowledge_search).research_price(_request())

    assert len(result.sources) == 1
    assert result.reference_prices == ()
    assert NO_STRUCTURED_PRICE_WARNING in result.warnings


@pytest.mark.asyncio
async def test_rag_provider_no_results_returns_empty_warning() -> None:
    async def knowledge_search(
        _request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        return _search_response(())

    result = await RAGPriceResearchProvider(knowledge_search).research_price(_request())

    assert result.provider == "rag"
    assert result.sources == ()
    assert result.reference_prices == ()
    assert result.confidence == 0.0
    assert NO_INTERNAL_EVIDENCE_WARNING in result.warnings
    assert RAG_REFERENCE_WARNING in result.warnings
    _assert_no_forbidden_positive_claims(result)


def test_provider_factory_rejects_rag_without_injected_dependency() -> None:
    with pytest.raises(PriceResearchProviderError, match="injected knowledge search"):
        get_price_research_provider("rag")


@pytest.mark.asyncio
async def test_service_rejects_rag_provider_name_without_dependency() -> None:
    service = PriceResearchService(enabled=True, provider_name="rag")

    with pytest.raises(PriceResearchProviderError, match="injected knowledge search"):
        await service.research_price(_request())


@pytest.mark.asyncio
async def test_service_accepts_injected_rag_provider() -> None:
    async def knowledge_search(
        _request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        return _search_response((_retrieval_result(metadata={"amount": 12500000}),))

    provider = RAGPriceResearchProvider(knowledge_search)
    service = PriceResearchService(enabled=True, provider=provider)

    result = await service.research_price(_request())

    assert result.provider == "rag"
    assert result.reference_prices[0].amount == Decimal("12500000")
    assert result.sources[0].source_type is PriceResearchSourceType.RAG


@pytest.mark.asyncio
async def test_fake_and_manual_provider_behavior_remains_available() -> None:
    fake_result = await FakePriceResearchProvider().research_price(_request())
    manual_result = await ManualPriceResearchProvider().research_price(_request())

    assert fake_result.provider == "fake"
    assert fake_result.sources[0].source_type is PriceResearchSourceType.FAKE
    assert manual_result.provider == "manual"
    assert manual_result.reference_prices == ()


@pytest.mark.asyncio
async def test_rag_provider_does_not_attempt_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import http.client
    import urllib.request

    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    monkeypatch.setattr(http.client.HTTPConnection, "request", fail_network)

    async def knowledge_search(
        _request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        return _search_response((_retrieval_result(metadata={"amount": "12500000"}),))

    result = await RAGPriceResearchProvider(knowledge_search).research_price(_request())

    assert result.provider == "rag"
    assert result.reference_prices[0].amount == Decimal("12500000")


def _assert_no_forbidden_positive_claims(result: PriceResearchResult) -> None:
    serialized = str(result.model_dump(mode="json")).lower()

    forbidden_positive_claims = (
        "in stock",
        "stock available",
        "delivery date",
        "will deliver",
        "approved quote",
        "final approved quote",
        "final quotation issued",
    )
    for claim in forbidden_positive_claims:
        assert claim not in serialized
