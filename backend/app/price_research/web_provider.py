"""External web reference price research provider.

Web search results are reference evidence only. They are never treated as final
quotes, approved prices, authoritative catalog inventory, or purchase
decisions. Tavily snippets are unstructured prose, so this provider maps results
to bounded source citations only and never fabricates reference prices; manual
pricing review remains required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.llm.clients.http import (
    AsyncJSONHTTPTransport,
    HTTPResponse,
    HTTPTimeoutError,
    HTTPTransportError,
    UrllibAsyncJSONHTTPTransport,
)
from app.price_research.exceptions import (
    PriceResearchErrorCategory,
    PriceResearchProviderError,
)
from app.price_research.schemas import (
    PriceResearchRequest,
    PriceResearchResult,
    PriceResearchSource,
    PriceResearchSourceType,
)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
WEB_SEARCH_MAX_RESULTS = 5
WEB_SEARCH_QUERY_LIMIT = 500
WEB_SEARCH_TITLE_LIMIT = 200
WEB_SEARCH_SNIPPET_LIMIT = 300
WEB_SEARCH_URL_LIMIT = 500
WEB_SEARCH_TIMEOUT_MIN = 1
WEB_SEARCH_TIMEOUT_MAX = 120
WEB_SOURCE_CONFIDENCE = 0.5

WEB_REFERENCE_WARNING = (
    "Web search results are reference evidence only, not a final quote."
)
NO_WEB_EVIDENCE_WARNING = "No web reference evidence found for this item."
NO_STRUCTURED_PRICE_WARNING = (
    "No structured price metadata found; manual pricing review is required."
)


class TavilyPriceResearchProvider:
    """Async Tavily web search reference evidence adapter.

    The provider follows the existing price research provider protocol and the
    controlled Tavily pattern established by the Telegram bridge: bounded
    title/URL/snippet normalization, http(s)-only URLs, bounded query, explicit
    error categories, and disabled-by-default integration through the service.
    No fake provider is constructed and no live provider call happens in tests.
    """

    name = "tavily"

    def __init__(
        self,
        *,
        api_key: str,
        transport: AsyncJSONHTTPTransport | None = None,
        timeout_seconds: int = 30,
        max_results: int = WEB_SEARCH_MAX_RESULTS,
    ) -> None:
        if not api_key.strip():
            raise PriceResearchProviderError(
                "Tavily price research provider requires an API key",
                category=PriceResearchErrorCategory.CONFIGURATION,
            )
        self._api_key = api_key.strip()
        self._transport = transport or UrllibAsyncJSONHTTPTransport()
        self._timeout_seconds = max(
            WEB_SEARCH_TIMEOUT_MIN,
            min(int(timeout_seconds), WEB_SEARCH_TIMEOUT_MAX),
        )
        self._max_results = max(1, min(int(max_results), WEB_SEARCH_MAX_RESULTS))

    @property
    def endpoint_url(self) -> str:
        """Return the provider search endpoint used for requests."""
        return TAVILY_SEARCH_URL

    async def research_price(
        self,
        request: PriceResearchRequest,
    ) -> PriceResearchResult:
        """Return bounded web reference evidence for the request."""
        payload = {
            "query": _build_query(request)[:WEB_SEARCH_QUERY_LIMIT],
            "max_results": self._max_results,
            "search_depth": "basic",
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            response = await self._transport.post_json(
                url=TAVILY_SEARCH_URL,
                headers=headers,
                payload=payload,
                timeout_seconds=self._timeout_seconds,
            )
        except HTTPTimeoutError as exc:
            raise PriceResearchProviderError(
                "web search request timed out",
                category=PriceResearchErrorCategory.TIMEOUT,
            ) from exc
        except HTTPTransportError as exc:
            raise PriceResearchProviderError(
                "web search provider is unavailable",
                category=PriceResearchErrorCategory.UNAVAILABLE,
            ) from exc
        _raise_for_http_status(response)
        raw_results = _raw_results(response.payload)
        retrieved_at = datetime.now(UTC)
        sources = _map_sources(
            raw_results,
            request=request,
            retrieved_at=retrieved_at,
        )

        if not sources:
            return PriceResearchResult(
                item_name=request.item_name,
                normalized_item_name=request.normalized_item_name,
                quantity=request.quantity,
                region=request.region,
                currency=request.currency,
                reference_prices=(),
                sources=(),
                confidence=0.0,
                retrieved_at=retrieved_at,
                warnings=(NO_WEB_EVIDENCE_WARNING, WEB_REFERENCE_WARNING),
                provider=self.name,
            )

        return PriceResearchResult(
            item_name=request.item_name,
            normalized_item_name=request.normalized_item_name,
            quantity=request.quantity,
            region=request.region,
            currency=request.currency,
            reference_prices=(),
            sources=tuple(sources),
            confidence=WEB_SOURCE_CONFIDENCE,
            retrieved_at=retrieved_at,
            warnings=(NO_STRUCTURED_PRICE_WARNING, WEB_REFERENCE_WARNING),
            provider=self.name,
        )


def _build_query(request: PriceResearchRequest) -> str:
    """Build a bounded query from the normalized request without hard-coding items."""
    parts = [
        request.normalized_item_name,
        request.item_name,
        request.region,
        " ".join(request.requested_addons),
        "reference price",
    ]
    return " ".join(part for part in parts if part).strip()


def _raise_for_http_status(response: HTTPResponse) -> None:
    if response.status_code < 400:
        return
    raise PriceResearchProviderError(
        f"web search provider returned HTTP {response.status_code}",
        category=_category_for_status(response.status_code),
    )


def _category_for_status(status_code: int) -> PriceResearchErrorCategory:
    if status_code in {401, 403}:
        return PriceResearchErrorCategory.AUTHENTICATION
    if status_code == 429:
        return PriceResearchErrorCategory.RATE_LIMIT
    if 400 <= status_code < 500:
        return PriceResearchErrorCategory.INVALID_REQUEST
    return PriceResearchErrorCategory.UNAVAILABLE


def _raw_results(payload: dict[str, Any]) -> list[Any]:
    """Return a list of raw provider results or raise on malformed shape."""
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise PriceResearchProviderError(
            "web search provider returned malformed response",
            category=PriceResearchErrorCategory.INVALID_RESPONSE,
        )
    return raw_results


def _map_sources(
    raw_results: list[Any],
    *,
    request: PriceResearchRequest,
    retrieved_at: datetime,
) -> list[PriceResearchSource]:
    """Map bounded raw provider results into normalized external web sources."""
    sources: list[PriceResearchSource] = []
    for item in raw_results[:WEB_SEARCH_MAX_RESULTS]:
        if not isinstance(item, dict):
            continue
        title = _bounded_web_text(item.get("title"), WEB_SEARCH_TITLE_LIMIT)
        snippet = _bounded_web_text(item.get("content"), WEB_SEARCH_SNIPPET_LIMIT)
        url = _safe_web_url(item.get("url"))
        if not title and url is None:
            continue
        sources.append(
            PriceResearchSource(
                title=title or "Untitled reference result",
                url=url,
                snippet=snippet,
                observed_price=None,
                currency=request.currency,
                retrieved_at=retrieved_at,
                source_type=PriceResearchSourceType.EXTERNAL_WEB,
                confidence=WEB_SOURCE_CONFIDENCE,
            )
        )
    return sources


def _bounded_web_text(value: Any, limit: int) -> str:
    """Collapse whitespace/control characters and bound external web text."""
    if not isinstance(value, str):
        return ""
    collapsed = " ".join(value.split())
    return collapsed[:limit]


def _safe_web_url(value: Any) -> str | None:
    """Accept only bounded http(s) URLs from an untrusted web provider."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped.startswith(("http://", "https://")):
        return None
    return stripped[:WEB_SEARCH_URL_LIMIT]
