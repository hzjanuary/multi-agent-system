"""Optional Tavily external web reference evidence provider."""

from __future__ import annotations

import asyncio
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, cast

from app.price_research.exceptions import PriceResearchProviderError
from app.price_research.schemas import (
    PriceResearchRequest,
    PriceResearchResult,
    PriceResearchSource,
    PriceResearchSourceType,
)

EXTERNAL_WEB_REFERENCE_WARNING = (
    "External web evidence is reference material, not a final quote."
)
NO_STRUCTURED_WEB_PRICE_WARNING = (
    "External web evidence found, but no structured price metadata was "
    "available; manual pricing review is required."
)
NO_EXTERNAL_WEB_RESULTS_WARNING = "No external web evidence found for this item."

MAX_QUERY_CHARS = 300
DEFAULT_TAVILY_SEARCH_URL = "https://api.tavily.com/search"

TavilyTransport = Callable[
    [str, Mapping[str, str], Mapping[str, Any], float],
    Mapping[str, Any],
]


class TavilyHTTPStatusError(RuntimeError):
    """Internal transport error carrying only a safe HTTP status code."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"Tavily search failed with HTTP status {status_code}")
        self.status_code = status_code


class TavilyPriceResearchProvider:
    """Collect bounded Tavily search result evidence for manual price review.

    Tavily output is external web reference evidence only. This provider does
    not scrape arbitrary websites, infer prices from snippets, issue final
    quotes, promise stock/delivery/discounts, or store raw provider payloads.
    """

    name = "tavily"

    def __init__(
        self,
        *,
        api_key: str,
        search_url: str = DEFAULT_TAVILY_SEARCH_URL,
        timeout_seconds: int = 30,
        max_results: int = 5,
        include_raw_content: bool = False,
        search_depth: str = "basic",
        transport: TavilyTransport | None = None,
    ) -> None:
        self._api_key = api_key.strip()
        self._search_url = search_url.strip()
        self._timeout_seconds = timeout_seconds
        self._max_results = max(1, min(max_results, 10))
        self._include_raw_content = include_raw_content
        self._search_depth = _normalize_search_depth(search_depth)
        self._transport = transport or _stdlib_transport

    async def research_price(
        self,
        request: PriceResearchRequest,
    ) -> PriceResearchResult:
        """Return Tavily search results as bounded external web evidence."""
        if not self._api_key:
            raise PriceResearchProviderError(
                "Tavily price research requires TAVILY_API_KEY when selected",
            )
        payload = self.build_search_payload(request)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = await asyncio.to_thread(
                self._transport,
                self._search_url,
                headers,
                payload,
                float(self._timeout_seconds),
            )
        except TimeoutError as exc:
            raise PriceResearchProviderError("Tavily search timed out") from exc
        except TavilyHTTPStatusError as exc:
            raise PriceResearchProviderError(
                f"Tavily search failed with HTTP status {exc.status_code}",
            ) from exc
        except json.JSONDecodeError as exc:
            raise PriceResearchProviderError(
                "Tavily search returned invalid JSON",
            ) from exc
        except ValueError as exc:
            raise PriceResearchProviderError(
                "Tavily search returned invalid JSON",
            ) from exc
        except OSError as exc:
            raise PriceResearchProviderError("Tavily search request failed") from exc

        return _result_from_response(
            request,
            response=response,
            provider_name=self.name,
            max_results=self._max_results,
            retrieved_at=datetime.now(UTC),
        )

    def build_search_payload(self, request: PriceResearchRequest) -> dict[str, Any]:
        """Build the official Tavily `/search` JSON payload."""
        return {
            "query": build_tavily_query(request),
            "search_depth": self._search_depth,
            "max_results": self._max_results,
            "topic": "general",
            "include_answer": False,
            "include_raw_content": self._include_raw_content,
            "include_images": False,
            "include_image_descriptions": False,
            "include_favicon": False,
            "auto_parameters": False,
            "safe_search": False,
        }


def build_tavily_query(request: PriceResearchRequest) -> str:
    """Build a bounded query without customer context or raw chat history."""
    parts = [
        request.normalized_item_name,
        request.item_name,
        " ".join(_display_addon(addon) for addon in request.requested_addons),
        request.region,
        request.currency,
        "supplier",
        "reference price",
        "business",
    ]
    query = " ".join(_sanitize_query_part(part) for part in parts if part)
    query = re.sub(r"\s+", " ", query).strip()
    return query[:MAX_QUERY_CHARS].strip()


def _result_from_response(
    request: PriceResearchRequest,
    *,
    response: Mapping[str, Any],
    provider_name: str,
    max_results: int,
    retrieved_at: datetime,
) -> PriceResearchResult:
    raw_results = response.get("results")
    if not isinstance(raw_results, list):
        raw_results = []

    sources: list[PriceResearchSource] = []
    for raw_result in raw_results:
        if len(sources) >= max_results:
            break
        source = _source_from_tavily_result(
            raw_result,
            request=request,
            retrieved_at=retrieved_at,
        )
        if source is not None:
            sources.append(source)

    warnings = [EXTERNAL_WEB_REFERENCE_WARNING]
    if sources:
        warnings.append(NO_STRUCTURED_WEB_PRICE_WARNING)
    else:
        warnings.append(NO_EXTERNAL_WEB_RESULTS_WARNING)

    return PriceResearchResult(
        item_name=request.item_name,
        normalized_item_name=request.normalized_item_name,
        quantity=request.quantity,
        region=request.region,
        currency=request.currency,
        reference_prices=(),
        sources=tuple(sources),
        confidence=_average_source_confidence(sources),
        retrieved_at=retrieved_at,
        warnings=tuple(warnings),
        provider=provider_name,
    )


def _source_from_tavily_result(
    raw_result: object,
    *,
    request: PriceResearchRequest,
    retrieved_at: datetime,
) -> PriceResearchSource | None:
    if not isinstance(raw_result, Mapping):
        return None
    title = _bounded_optional_text(raw_result.get("title"))
    url = _bounded_optional_text(raw_result.get("url"))
    snippet = _bounded_optional_text(
        raw_result.get("content") or raw_result.get("snippet"),
    )
    if title is None and url is None and snippet is None:
        return None

    return PriceResearchSource(
        title=title or url or "Tavily search result",
        url=url,
        snippet=snippet,
        observed_price=None,
        currency=request.currency,
        retrieved_at=retrieved_at,
        source_type=PriceResearchSourceType.EXTERNAL_WEB,
        confidence=_normalize_score(raw_result.get("score")),
    )


def _stdlib_transport(
    search_url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout_seconds: float,
) -> Mapping[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        search_url,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read()
    except urllib.error.HTTPError as exc:
        raise TavilyHTTPStatusError(exc.code) from exc

    decoded = response_body.decode("utf-8")
    loaded = json.loads(decoded)
    if not isinstance(loaded, Mapping):
        raise ValueError("Tavily response must be a JSON object")
    return cast(Mapping[str, Any], loaded)


def _normalize_search_depth(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"basic", "advanced"}:
        raise PriceResearchProviderError(
            "Tavily search depth must be 'basic' or 'advanced'",
        )
    return normalized


def _display_addon(addon: str) -> str:
    if addon == "office_365":
        return "Office 365"
    if addon == "microsoft_365":
        return "Microsoft 365"
    return addon.replace("_", " ")


def _sanitize_query_part(value: str) -> str:
    sanitized = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", " ", value)
    sanitized = re.sub(
        r"(?i)\b(api[_-]?key|token|secret|password|authorization)\b\S*",
        " ",
        sanitized,
    )
    sanitized = re.sub(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b", " ", sanitized)
    return sanitized.strip()


def _bounded_optional_text(value: object, *, max_length: int = 1000) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[:max_length].strip()


def _normalize_score(value: object) -> float:
    if isinstance(value, bool):
        return 0.4
    if isinstance(value, int | float):
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return float(value)
    return 0.4


def _average_source_confidence(sources: list[PriceResearchSource]) -> float:
    if not sources:
        return 0.0
    return sum(source.confidence for source in sources) / len(sources)
