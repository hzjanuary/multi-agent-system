"""Tests for the optional Tavily external web price research provider."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Mapping
from typing import Any

import pytest

from app.price_research import (
    FakePriceResearchProvider,
    ManualPriceResearchProvider,
    PriceResearchProviderError,
    PriceResearchRequest,
    PriceResearchService,
    PriceResearchSourceType,
    get_price_research_provider,
)
from app.price_research.tavily_provider import (
    EXTERNAL_WEB_REFERENCE_WARNING,
    MAX_QUERY_CHARS,
    NO_STRUCTURED_WEB_PRICE_WARNING,
    TavilyHTTPStatusError,
    TavilyPriceResearchProvider,
    build_tavily_query,
)


class CapturingTavilyTransport:
    """In-test Tavily transport that proves no real network call is needed."""

    def __init__(
        self,
        response: Mapping[str, Any] | None = None,
        exception: BaseException | None = None,
    ) -> None:
        self.response = response or {"results": []}
        self.exception = exception
        self.calls: list[tuple[str, Mapping[str, str], Mapping[str, Any], float]] = []

    def __call__(
        self,
        search_url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls.append((search_url, headers, payload, timeout_seconds))
        if self.exception is not None:
            raise self.exception
        return self.response


def _request(**overrides: Any) -> PriceResearchRequest:
    values: dict[str, Any] = {
        "item_name": "standard business laptop",
        "normalized_item_name": "Standard business laptop",
        "quantity": 20,
        "region": "VN",
        "currency": "VND",
        "requested_addons": ("office_365",),
        "customer_context": {
            "note": "customer-secret-value should-not-enter-query buyer@example.test",
        },
        "request_text": (
            "Contact buyer@example.test or +84 901 234 567. "
            "authorization token abc123. Need laptops."
        ),
    }
    values.update(overrides)
    return PriceResearchRequest(**values)


@pytest.mark.asyncio
async def test_tavily_provider_missing_api_key_fails_safely() -> None:
    transport = CapturingTavilyTransport()
    provider = TavilyPriceResearchProvider(api_key="", transport=transport)

    with pytest.raises(PriceResearchProviderError, match="TAVILY_API_KEY"):
        await provider.research_price(_request())

    assert transport.calls == []


def test_tavily_query_is_sanitized_bounded_and_excludes_customer_context() -> None:
    request = _request()

    query = build_tavily_query(request)

    assert len(query) <= MAX_QUERY_CHARS
    assert "Standard business laptop" in query
    assert "Office 365" in query
    assert "VN" in query
    assert "VND" in query
    assert "supplier" in query
    assert "reference price" in query
    assert "customer-secret-value" not in query
    assert "buyer@example.test" not in query
    assert "+84" not in query
    assert "abc123" not in query


def test_tavily_query_is_bounded() -> None:
    request = _request(item_name="standard business laptop " * 30)

    query = build_tavily_query(request)

    assert len(query) <= MAX_QUERY_CHARS


@pytest.mark.asyncio
async def test_tavily_success_maps_results_to_external_web_sources() -> None:
    transport = CapturingTavilyTransport(
        response={
            "results": [
                {
                    "title": "Business laptop supplier",
                    "url": "https://supplier.example/laptops",
                    "content": "Supplier listing for business laptops.",
                    "score": 0.77,
                    "raw_content": "raw provider content should not be stored",
                },
            ],
        },
    )
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        max_results=5,
        transport=transport,
    )

    result = await provider.research_price(_request())

    assert result.provider == "tavily"
    assert result.is_final_quote is False
    assert result.reference_prices == ()
    assert len(result.sources) == 1
    assert result.sources[0].source_type is PriceResearchSourceType.EXTERNAL_WEB
    assert result.sources[0].title == "Business laptop supplier"
    assert result.sources[0].url == "https://supplier.example/laptops"
    assert result.sources[0].observed_price is None
    assert result.sources[0].currency == "VND"
    assert result.sources[0].confidence == 0.77
    assert EXTERNAL_WEB_REFERENCE_WARNING in result.warnings
    assert NO_STRUCTURED_WEB_PRICE_WARNING in result.warnings
    assert "raw provider content" not in str(result.model_dump(mode="json"))


@pytest.mark.asyncio
async def test_tavily_transport_receives_auth_header_but_key_is_not_in_result() -> None:
    transport = CapturingTavilyTransport(
        response={
            "results": [
                {
                    "title": "Vendor source",
                    "url": "https://vendor.example",
                    "content": "Reference evidence.",
                },
            ],
        },
    )
    provider = TavilyPriceResearchProvider(
        api_key="tvly-secret-test-key",
        transport=transport,
    )

    result = await provider.research_price(_request())

    _search_url, headers, _payload, _timeout = transport.calls[0]
    assert headers["Authorization"] == "Bearer tvly-secret-test-key"
    assert "tvly-secret-test-key" not in str(result.model_dump(mode="json"))


@pytest.mark.asyncio
async def test_tavily_payload_uses_official_search_shape() -> None:
    transport = CapturingTavilyTransport()
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        search_url="https://api.tavily.test/search",
        timeout_seconds=12,
        max_results=7,
        include_raw_content=True,
        search_depth="advanced",
        transport=transport,
    )

    await provider.research_price(_request())

    search_url, headers, payload, timeout = transport.calls[0]
    assert search_url == "https://api.tavily.test/search"
    assert timeout == 12.0
    assert headers["Content-Type"] == "application/json"
    assert payload["search_depth"] == "advanced"
    assert payload["max_results"] == 7
    assert payload["topic"] == "general"
    assert payload["include_answer"] is False
    assert payload["include_raw_content"] is True
    assert payload["include_images"] is False
    assert payload["auto_parameters"] is False


@pytest.mark.asyncio
async def test_tavily_score_normalization_handles_missing_invalid_and_bounds() -> None:
    transport = CapturingTavilyTransport(
        response={
            "results": [
                {"title": "Missing score", "content": "No score."},
                {"title": "Invalid score", "content": "Bad score.", "score": "high"},
                {"title": "High score", "content": "Bounded.", "score": 1.7},
                {"title": "Low score", "content": "Bounded.", "score": -0.4},
            ],
        },
    )
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        transport=transport,
    )

    result = await provider.research_price(_request())

    assert [source.confidence for source in result.sources] == [0.4, 0.4, 1.0, 0.0]


@pytest.mark.asyncio
async def test_tavily_timeout_maps_to_safe_provider_error() -> None:
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        transport=CapturingTavilyTransport(exception=TimeoutError("raw timeout")),
    )

    with pytest.raises(PriceResearchProviderError) as error:
        await provider.research_price(_request())

    assert str(error.value) == "Tavily search timed out"


@pytest.mark.asyncio
async def test_tavily_non_2xx_maps_to_safe_status_only_error() -> None:
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        transport=CapturingTavilyTransport(exception=TavilyHTTPStatusError(503)),
    )

    with pytest.raises(PriceResearchProviderError) as error:
        await provider.research_price(_request())

    assert str(error.value) == "Tavily search failed with HTTP status 503"
    assert "body" not in str(error.value).lower()


@pytest.mark.asyncio
async def test_tavily_invalid_json_maps_to_safe_provider_error() -> None:
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        transport=CapturingTavilyTransport(exception=ValueError("raw response body")),
    )

    with pytest.raises(PriceResearchProviderError) as error:
        await provider.research_price(_request())

    assert str(error.value) == "Tavily search returned invalid JSON"
    assert "raw response body" not in str(error.value)


@pytest.mark.asyncio
async def test_tavily_malformed_results_are_skipped_and_max_results_respected() -> None:
    transport = CapturingTavilyTransport(
        response={
            "results": [
                "not a result",
                {},
                {
                    "title": "First valid",
                    "url": "https://source1.example",
                    "content": "Source 1.",
                },
                {
                    "title": "Second valid",
                    "url": "https://source2.example",
                    "content": "Source 2.",
                },
                {
                    "title": "Third valid",
                    "url": "https://source3.example",
                    "content": "Source 3.",
                },
            ],
        },
    )
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        max_results=2,
        transport=transport,
    )

    result = await provider.research_price(_request())

    assert [source.title for source in result.sources] == [
        "First valid",
        "Second valid",
    ]


@pytest.mark.asyncio
async def test_tavily_injected_transport_avoids_default_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("default network transport must not be called")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        transport=CapturingTavilyTransport(
            response={
                "results": [
                    {
                        "title": "Safe source",
                        "url": "https://safe.example",
                        "content": "Safe source evidence.",
                    },
                ],
            },
        ),
    )

    result = await provider.research_price(_request())

    assert result.sources[0].title == "Safe source"


def test_tavily_provider_rejects_invalid_search_depth() -> None:
    with pytest.raises(PriceResearchProviderError, match="search depth"):
        TavilyPriceResearchProvider(api_key="tvly-test-key", search_depth="deep")


def test_provider_factory_rejects_tavily_without_explicit_injection() -> None:
    with pytest.raises(PriceResearchProviderError, match="explicit provider injection"):
        get_price_research_provider("tavily")


@pytest.mark.asyncio
async def test_service_tavily_without_injected_provider_fails_safely() -> None:
    service = PriceResearchService(enabled=True, provider_name="tavily")

    with pytest.raises(PriceResearchProviderError, match="explicit provider injection"):
        await service.research_price(_request())


def test_existing_no_network_factory_behavior_remains_unchanged() -> None:
    assert isinstance(get_price_research_provider("fake"), FakePriceResearchProvider)
    assert isinstance(
        get_price_research_provider("manual"),
        ManualPriceResearchProvider,
    )
    with pytest.raises(PriceResearchProviderError, match="injected knowledge"):
        get_price_research_provider("rag")


@pytest.mark.asyncio
async def test_tavily_result_contains_no_forbidden_positive_claims() -> None:
    provider = TavilyPriceResearchProvider(
        api_key="tvly-test-key",
        transport=CapturingTavilyTransport(
            response={
                "results": [
                    {
                        "title": "Supplier listing",
                        "url": "https://supplier.example",
                        "content": "Reference evidence for manual review.",
                    },
                ],
            },
        ),
    )

    result = await provider.research_price(_request())
    serialized = json.dumps(result.model_dump(mode="json")).lower()

    forbidden_claims = (
        "in stock",
        "delivery date",
        "approved quote",
        "final approved quote",
        "final quotation issued",
        "discount approved",
    )
    for claim in forbidden_claims:
        assert claim not in serialized
