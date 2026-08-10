"""Tests for the external web search reference price research provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.config import Settings
from app.llm.clients.http import (
    HTTPResponse,
    HTTPTimeoutError,
    HTTPTransportError,
)
from app.price_research import (
    PriceResearchDisabledError,
    PriceResearchErrorCategory,
    PriceResearchProvider,
    PriceResearchProviderError,
    PriceResearchRequest,
    PriceResearchResult,
    PriceResearchService,
    PriceResearchSourceType,
    TavilyPriceResearchProvider,
    get_price_research_provider,
)
from app.price_research.web_provider import (
    NO_STRUCTURED_PRICE_WARNING,
    NO_WEB_EVIDENCE_WARNING,
    TAVILY_SEARCH_URL,
    WEB_REFERENCE_WARNING,
    WEB_SEARCH_MAX_RESULTS,
    WEB_SEARCH_SNIPPET_LIMIT,
    WEB_SEARCH_TITLE_LIMIT,
    WEB_SEARCH_URL_LIMIT,
)


@dataclass
class CapturedRequest:
    """Captured transport request for assertions."""

    url: str
    headers: dict[str, str]
    payload: dict[str, Any]
    timeout_seconds: int


@dataclass
class FakeTransport:
    """In-memory JSON transport returning queued responses."""

    responses: list[HTTPResponse | Exception] = field(default_factory=list)
    requests: list[CapturedRequest] = field(default_factory=list)

    async def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: int,
    ) -> HTTPResponse:
        self.requests.append(
            CapturedRequest(
                url=url,
                headers=headers,
                payload=payload,
                timeout_seconds=timeout_seconds,
            ),
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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


def _unsupported_item_request() -> PriceResearchRequest:
    return PriceResearchRequest(
        item_name="office chair",
        normalized_item_name="Office chair",
        quantity=5,
        region="VN",
        currency="VND",
        request_text="bao gia 5 ghe van phong",
    )


def _success_response() -> HTTPResponse:
    return HTTPResponse(
        status_code=200,
        payload={
            "query": "Standard business laptop",
            "results": [
                {
                    "title": "Business laptop pricing guide",
                    "url": "https://example.test/laptop-pricing",
                    "content": "Standard business laptop reference overview.",
                },
                {
                    "title": "VN laptop vendor",
                    "url": "http://example.test/vendor",
                    "content": "Local vendor listing without structured pricing.",
                },
            ],
        },
    )


def _provider(
    transport: FakeTransport | None = None,
    *,
    api_key: str = "sk-test-key",
) -> TavilyPriceResearchProvider:
    return TavilyPriceResearchProvider(
        api_key=api_key,
        transport=transport or FakeTransport(),
        timeout_seconds=10,
    )


@pytest.mark.asyncio
async def test_provider_implements_price_research_protocol() -> None:
    assert isinstance(_provider(), PriceResearchProvider)
    assert _provider().name == "tavily"


def test_provider_requires_api_key_at_construction() -> None:
    with pytest.raises(
        PriceResearchProviderError,
        match="requires an API key",
    ) as exc_info:
        TavilyPriceResearchProvider(api_key="  ")
    assert exc_info.value.category is PriceResearchErrorCategory.CONFIGURATION


def test_provider_factory_requires_injected_api_key_and_transport() -> None:
    with pytest.raises(
        PriceResearchProviderError,
        match="injected API key and transport",
    ) as exc_info:
        get_price_research_provider("tavily")
    assert exc_info.value.category is PriceResearchErrorCategory.CONFIGURATION


@pytest.mark.asyncio
async def test_service_is_disabled_by_default_with_tavily_provider() -> None:
    service = PriceResearchService(enabled=False, provider=_provider())

    with pytest.raises(PriceResearchDisabledError):
        await service.research_price(_request())


@pytest.mark.asyncio
async def test_service_rejects_tavily_provider_name_without_injection() -> None:
    service = PriceResearchService(enabled=True, provider_name="tavily")

    with pytest.raises(PriceResearchProviderError, match="injected API key"):
        await service.research_price(_request())


@pytest.mark.asyncio
async def test_successful_provider_response_maps_citations() -> None:
    transport = FakeTransport(responses=[_success_response()])
    provider = _provider(transport)

    result = await provider.research_price(_request())

    captured = transport.requests[0]
    assert captured.url == TAVILY_SEARCH_URL
    assert captured.headers["Authorization"] == "Bearer sk-test-key"
    assert "Standard business laptop" in captured.payload["query"]
    assert "office_365" in captured.payload["query"]
    assert captured.payload["max_results"] == WEB_SEARCH_MAX_RESULTS
    assert captured.timeout_seconds == 10

    assert result.provider == "tavily"
    assert result.is_final_quote is False
    assert result.evidence_label == "reference_price_research"
    assert len(result.sources) == 2
    assert result.sources[0].source_type is PriceResearchSourceType.EXTERNAL_WEB
    assert result.sources[0].title == "Business laptop pricing guide"
    assert result.sources[0].url == "https://example.test/laptop-pricing"
    assert result.sources[0].snippet == "Standard business laptop reference overview."
    assert result.sources[0].observed_price is None
    assert result.sources[1].title == "VN laptop vendor"
    assert result.sources[1].url == "http://example.test/vendor"
    assert result.reference_prices == ()
    assert NO_STRUCTURED_PRICE_WARNING in result.warnings
    assert WEB_REFERENCE_WARNING in result.warnings
    _assert_no_forbidden_positive_claims(result)


@pytest.mark.asyncio
async def test_timeout_is_categorized_and_raised_safely() -> None:
    provider = _provider(FakeTransport(responses=[HTTPTimeoutError("timeout")]))

    with pytest.raises(
        PriceResearchProviderError,
        match="timed out",
    ) as exc_info:
        await provider.research_price(_request())
    assert exc_info.value.category is PriceResearchErrorCategory.TIMEOUT


@pytest.mark.asyncio
async def test_transport_failure_is_categorized_as_unavailable() -> None:
    provider = _provider(FakeTransport(responses=[HTTPTransportError("down")]))

    with pytest.raises(
        PriceResearchProviderError,
        match="unavailable",
    ) as exc_info:
        await provider.research_price(_request())
    assert exc_info.value.category is PriceResearchErrorCategory.UNAVAILABLE


@pytest.mark.asyncio
async def test_http_failure_categories_are_explicit() -> None:
    for status_code, expected in (
        (401, PriceResearchErrorCategory.AUTHENTICATION),
        (403, PriceResearchErrorCategory.AUTHENTICATION),
        (429, PriceResearchErrorCategory.RATE_LIMIT),
        (400, PriceResearchErrorCategory.INVALID_REQUEST),
        (404, PriceResearchErrorCategory.INVALID_REQUEST),
        (500, PriceResearchErrorCategory.UNAVAILABLE),
        (503, PriceResearchErrorCategory.UNAVAILABLE),
    ):
        provider = _provider(
            FakeTransport(
                responses=[HTTPResponse(status_code=status_code, payload={})],
            ),
        )

        with pytest.raises(
            PriceResearchProviderError,
            match=f"HTTP {status_code}",
        ) as exc_info:
            await provider.research_price(_request())
        assert exc_info.value.category is expected


@pytest.mark.asyncio
async def test_malformed_response_is_categorized_as_invalid() -> None:
    provider = _provider(
        FakeTransport(
            responses=[HTTPResponse(status_code=200, payload={"results": "oops"})],
        ),
    )

    with pytest.raises(
        PriceResearchProviderError,
        match="malformed response",
    ) as exc_info:
        await provider.research_price(_request())
    assert exc_info.value.category is PriceResearchErrorCategory.INVALID_RESPONSE


@pytest.mark.asyncio
async def test_oversized_response_is_bounded_to_max_results() -> None:
    many_results = [
        {
            "title": f"Reference result {index}",
            "url": f"https://example.test/result/{index}",
            "content": f"Reference content {index}",
        }
        for index in range(100)
    ]
    provider = _provider(
        FakeTransport(
            responses=[
                HTTPResponse(status_code=200, payload={"results": many_results}),
            ],
        ),
    )

    result = await provider.research_price(_request())

    assert len(result.sources) == WEB_SEARCH_MAX_RESULTS
    assert result.sources[-1].title == f"Reference result {WEB_SEARCH_MAX_RESULTS - 1}"


@pytest.mark.asyncio
async def test_result_fields_are_bounded_and_untrusted_items_skipped() -> None:
    oversized_title = "x" * 5000
    oversized_snippet = "y" * 5000
    oversized_url = "z" * 5000
    response = HTTPResponse(
        status_code=200,
        payload={
            "results": [
                {
                    "title": f"{oversized_title}\n\n{oversized_snippet}",
                    "url": f"https://example.test/{oversized_url}",
                    "content": oversized_snippet,
                },
                "not-a-dict",
                {"title": "   ", "url": "javascript:alert(1)"},
            ],
        },
    )
    provider = _provider(FakeTransport(responses=[response]))

    result = await provider.research_price(_request())

    source = result.sources[0]
    assert source.title == "x" * WEB_SEARCH_TITLE_LIMIT
    assert source.snippet == "y" * WEB_SEARCH_SNIPPET_LIMIT
    if source.url is not None:
        assert len(source.url) <= WEB_SEARCH_URL_LIMIT
        assert "javascript:" not in source.url


@pytest.mark.asyncio
async def test_no_results_returns_empty_warning() -> None:
    provider = _provider(
        FakeTransport(
            responses=[HTTPResponse(status_code=200, payload={"results": []})],
        ),
    )

    result = await provider.research_price(_request())

    assert result.sources == ()
    assert result.reference_prices == ()
    assert result.confidence == 0.0
    assert NO_WEB_EVIDENCE_WARNING in result.warnings
    assert WEB_REFERENCE_WARNING in result.warnings


@pytest.mark.asyncio
async def test_unsupported_item_is_not_silently_priced() -> None:
    provider = _provider(FakeTransport(responses=[_success_response()]))

    result = await provider.research_price(_unsupported_item_request())

    assert result.reference_prices == ()
    assert result.is_final_quote is False
    assert NO_STRUCTURED_PRICE_WARNING in result.warnings
    assert result.sources[0].source_type is PriceResearchSourceType.EXTERNAL_WEB
    _assert_no_forbidden_positive_claims(result)


@pytest.mark.asyncio
async def test_service_integrates_injected_tavily_provider() -> None:
    provider = _provider(FakeTransport(responses=[_success_response()]))
    service = PriceResearchService(enabled=True, provider=provider, max_sources=5)

    result = await service.research_price(_request())

    assert result.provider == "tavily"
    assert result.sources[0].source_type is PriceResearchSourceType.EXTERNAL_WEB


def test_error_safe_details_are_bounded() -> None:
    error = PriceResearchProviderError(
        "web search request timed out",
        category=PriceResearchErrorCategory.TIMEOUT,
    )

    assert error.safe_details() == {"category": "timeout"}


def test_settings_defaults_keep_web_search_off_and_keyless() -> None:
    settings = Settings()

    assert settings.price_research_enabled is False
    assert settings.price_research_provider == "fake"
    assert settings.price_research_tavily_api_key == ""


def test_settings_read_tavily_api_key_without_exposing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PRICE_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("PRICE_RESEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("TAVILY_API_KEY", "sk-live-key")

    settings = Settings()

    assert settings.price_research_enabled is True
    assert settings.price_research_provider == "tavily"
    assert settings.price_research_tavily_api_key == "sk-live-key"


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
