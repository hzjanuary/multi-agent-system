"""Internal knowledge/RAG reference price research provider."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.knowledge.schemas import (
    KnowledgeRetrievalResult,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.price_research.schemas import (
    PriceResearchRequest,
    PriceResearchResult,
    PriceResearchSource,
    PriceResearchSourceType,
    ReferencePrice,
)

RAG_REFERENCE_WARNING = "RAG evidence is reference material, not a final quote."
NO_STRUCTURED_PRICE_WARNING = (
    "No structured price metadata found; manual pricing review is required."
)
NO_INTERNAL_EVIDENCE_WARNING = "No internal knowledge evidence found for this item."

KnowledgeSearchCallable = Callable[
    [KnowledgeSearchRequest],
    Awaitable[KnowledgeSearchResponse],
]


class RAGPriceResearchProvider:
    """Map injected internal knowledge search results into price evidence.

    This provider performs no external network access and does not instantiate
    Qdrant, embedding, or LLM clients. It only converts already-bounded
    knowledge retrieval results into reference evidence. Prices are created
    only from explicit structured metadata; prose is never parsed for amounts.
    """

    name = "rag"

    def __init__(
        self,
        knowledge_search: KnowledgeSearchCallable,
        *,
        top_k: int = 5,
        minimum_score: float | None = None,
    ) -> None:
        self._knowledge_search = knowledge_search
        self._top_k = top_k
        self._minimum_score = minimum_score

    async def research_price(
        self,
        request: PriceResearchRequest,
    ) -> PriceResearchResult:
        """Return internal RAG reference evidence for the request."""
        search_response = await self._knowledge_search(
            _build_search_request(
                request,
                top_k=self._top_k,
                minimum_score=self._minimum_score,
            ),
        )
        results = tuple(search_response.results[: self._top_k])

        if not results:
            return PriceResearchResult(
                item_name=request.item_name,
                normalized_item_name=request.normalized_item_name,
                quantity=request.quantity,
                region=request.region,
                currency=request.currency,
                reference_prices=(),
                sources=(),
                confidence=0.0,
                retrieved_at=datetime.now(UTC),
                warnings=(NO_INTERNAL_EVIDENCE_WARNING, RAG_REFERENCE_WARNING),
                provider=self.name,
            )

        sources: list[PriceResearchSource] = []
        reference_prices: list[ReferencePrice] = []
        for result in results:
            source = _source_from_result(result, request)
            source_index = len(sources)
            sources.append(source)

            reference_price = _reference_price_from_metadata(
                result.metadata,
                request=request,
                source=source,
                source_index=source_index,
            )
            if reference_price is not None:
                reference_prices.append(reference_price)

        warnings = [RAG_REFERENCE_WARNING]
        if not reference_prices:
            warnings.append(NO_STRUCTURED_PRICE_WARNING)

        return PriceResearchResult(
            item_name=request.item_name,
            normalized_item_name=request.normalized_item_name,
            quantity=request.quantity,
            region=request.region,
            currency=request.currency,
            reference_prices=tuple(reference_prices),
            sources=tuple(sources),
            confidence=_average_confidence(results),
            retrieved_at=_latest_retrieved_at(sources),
            warnings=tuple(warnings),
            provider=self.name,
        )


def _build_search_request(
    request: PriceResearchRequest,
    *,
    top_k: int,
    minimum_score: float | None,
) -> KnowledgeSearchRequest:
    query_parts = [
        request.normalized_item_name,
        request.item_name,
        request.region,
        " ".join(request.requested_addons),
        "reference price",
    ]
    query = " ".join(part for part in query_parts if part).strip()
    return KnowledgeSearchRequest(query=query, top_k=top_k, minimum_score=minimum_score)


def _source_from_result(
    result: KnowledgeRetrievalResult,
    request: PriceResearchRequest,
) -> PriceResearchSource:
    metadata = result.metadata
    observed_price = _decimal_from_metadata(metadata, ("observed_price", "amount"))
    return PriceResearchSource(
        title=result.document_title,
        url=_optional_text_from_metadata(
            metadata, ("url", "source_url", "document_url")
        ),
        snippet=result.citation.excerpt or result.chunk_text,
        observed_price=observed_price,
        currency=_currency_from_metadata(metadata) or request.currency,
        retrieved_at=_datetime_from_metadata(metadata) or datetime.now(UTC),
        source_type=PriceResearchSourceType.RAG,
        confidence=result.score,
    )


def _reference_price_from_metadata(
    metadata: dict[str, Any],
    *,
    request: PriceResearchRequest,
    source: PriceResearchSource,
    source_index: int,
) -> ReferencePrice | None:
    amount = _decimal_from_metadata(metadata, ("observed_price", "amount"))
    if amount is None:
        return None

    return ReferencePrice(
        label=_optional_text_from_metadata(metadata, ("price_label", "label"))
        or "RAG reference price",
        amount=amount,
        currency=_currency_from_metadata(metadata)
        or source.currency
        or request.currency,
        unit=_optional_text_from_metadata(metadata, ("unit",)),
        quantity_basis=_positive_int_from_metadata(metadata, ("quantity_basis",)),
        source_index=source_index,
        notes=(
            "Internal knowledge reference evidence only; "
            "human approval remains required."
        ),
    )


def _optional_text_from_metadata(
    metadata: dict[str, Any],
    keys: tuple[str, ...],
) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _currency_from_metadata(metadata: dict[str, Any]) -> str | None:
    value = _optional_text_from_metadata(metadata, ("currency",))
    if value is None:
        return None
    normalized = value.upper()
    return normalized if len(normalized) == 3 else None


def _decimal_from_metadata(
    metadata: dict[str, Any],
    keys: tuple[str, ...],
) -> Decimal | None:
    for key in keys:
        value = metadata.get(key)
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, int | float | str):
            try:
                decimal_value = Decimal(str(value).strip())
            except (InvalidOperation, ValueError):
                continue
            if decimal_value >= 0:
                return decimal_value
    return None


def _positive_int_from_metadata(
    metadata: dict[str, Any],
    keys: tuple[str, ...],
) -> int | None:
    for key in keys:
        value = metadata.get(key)
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value if value > 0 else None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit():
                parsed = int(stripped)
                return parsed if parsed > 0 else None
    return None


def _datetime_from_metadata(metadata: dict[str, Any]) -> datetime | None:
    value = metadata.get("retrieved_at")
    if isinstance(value, datetime):
        return value if _is_timezone_aware(value) else None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if _is_timezone_aware(parsed) else None
    return None


def _is_timezone_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _average_confidence(results: tuple[KnowledgeRetrievalResult, ...]) -> float:
    if not results:
        return 0.0
    return sum(result.score for result in results) / len(results)


def _latest_retrieved_at(sources: list[PriceResearchSource]) -> datetime:
    if not sources:
        return datetime.now(UTC)
    return max(source.retrieved_at for source in sources)
