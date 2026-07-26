"""Tests for reference price research provider and service interfaces."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.config import Settings
from app.price_research import (
    FakePriceResearchProvider,
    ManualPriceResearchProvider,
    PriceResearchDisabledError,
    PriceResearchProvider,
    PriceResearchProviderError,
    PriceResearchRequest,
    PriceResearchResult,
    PriceResearchService,
    PriceResearchSource,
    PriceResearchSourceType,
    ReferencePrice,
    get_price_research_provider,
)


class InTestFakePriceResearchProvider:
    """Tiny in-test provider proving the async protocol contract."""

    name = "in_test_fake"

    async def research_price(
        self,
        request: PriceResearchRequest,
    ) -> PriceResearchResult:
        source = PriceResearchSource(
            title="Manual fixture",
            observed_price=Decimal("12000000"),
            currency=request.currency,
            retrieved_at=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
            source_type=PriceResearchSourceType.FAKE,
            confidence=0.9,
        )
        return PriceResearchResult(
            item_name=request.item_name,
            normalized_item_name=request.normalized_item_name,
            quantity=request.quantity,
            region=request.region,
            currency=request.currency,
            reference_prices=(
                ReferencePrice(
                    label="Reference unit price",
                    amount=Decimal("12000000"),
                    currency=request.currency,
                    unit="unit",
                    quantity_basis=1,
                    source_index=0,
                    notes="In-test fake reference evidence only.",
                ),
            ),
            sources=(source,),
            confidence=0.9,
            retrieved_at=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
            warnings=(),
            provider=self.name,
        )


def _request() -> PriceResearchRequest:
    return PriceResearchRequest(
        item_name="laptop",
        normalized_item_name="Standard business laptop",
        quantity=20,
        region="VN",
        currency="VND",
        requested_addons=("office_365",),
    )


def _unknown_item_request() -> PriceResearchRequest:
    return PriceResearchRequest(
        item_name="printer",
        normalized_item_name="HP printer",
        quantity=5,
        region="VN",
        currency="VND",
    )


def _manual_source() -> PriceResearchSource:
    return PriceResearchSource(
        title="Manual operator reference",
        observed_price=Decimal("13000000"),
        currency="VND",
        retrieved_at=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
        source_type=PriceResearchSourceType.FAKE,
        confidence=0.75,
    )


def _manual_reference_price() -> ReferencePrice:
    return ReferencePrice(
        label="Manual reference unit price",
        amount=Decimal("13000000"),
        currency="VND",
        unit="unit",
        quantity_basis=1,
        source_index=0,
        notes="Manual reference evidence only.",
    )


def test_provider_protocol_accepts_async_provider() -> None:
    provider = InTestFakePriceResearchProvider()

    assert isinstance(provider, PriceResearchProvider)
    assert provider.name == "in_test_fake"


@pytest.mark.asyncio
async def test_service_is_disabled_by_default() -> None:
    service = PriceResearchService(provider=InTestFakePriceResearchProvider())

    with pytest.raises(PriceResearchDisabledError):
        await service.research_price(_request())


@pytest.mark.asyncio
async def test_service_delegates_to_provider_when_enabled() -> None:
    service = PriceResearchService(
        enabled=True,
        provider=InTestFakePriceResearchProvider(),
        max_sources=5,
    )

    result = await service.research_price(_request())

    assert result.provider == "in_test_fake"
    assert result.is_final_quote is False
    assert result.reference_prices[0].label == "Reference unit price"


@pytest.mark.asyncio
async def test_service_requires_provider_when_enabled() -> None:
    service = PriceResearchService(enabled=True)

    result = await service.research_price(_request())

    assert result.provider == "fake"
    assert result.sources[0].source_type is PriceResearchSourceType.FAKE


@pytest.mark.asyncio
async def test_service_rejects_provider_source_overflow() -> None:
    service = PriceResearchService(
        enabled=True,
        provider=InTestFakePriceResearchProvider(),
        max_sources=0,
    )

    with pytest.raises(PriceResearchProviderError, match="too many sources"):
        await service.research_price(_request())


@pytest.mark.asyncio
async def test_fake_provider_returns_deterministic_laptop_reference() -> None:
    result = await FakePriceResearchProvider().research_price(_request())

    assert result.provider == "fake"
    assert result.evidence_label == "reference_price_research"
    assert result.is_final_quote is False
    assert result.sources[0].source_type is PriceResearchSourceType.FAKE
    assert result.reference_prices[0].amount == Decimal("12000000")
    assert result.reference_prices[0].source_index == 0
    assert any("not a final quote" in warning for warning in result.warnings)
    _assert_no_forbidden_positive_claims(result)


@pytest.mark.asyncio
async def test_fake_provider_unknown_item_returns_empty_warning() -> None:
    result = await FakePriceResearchProvider().research_price(_unknown_item_request())

    assert result.provider == "fake"
    assert result.reference_prices == ()
    assert result.sources == ()
    assert result.confidence == 0.1
    assert any("No fake catalog match" in warning for warning in result.warnings)
    _assert_no_forbidden_positive_claims(result)


@pytest.mark.asyncio
async def test_manual_provider_without_data_returns_manual_warning() -> None:
    result = await ManualPriceResearchProvider().research_price(_request())

    assert result.provider == "manual"
    assert result.reference_prices == ()
    assert result.sources == ()
    assert result.confidence == 0.0
    assert any(
        "Manual price research is required" in warning for warning in result.warnings
    )
    _assert_no_forbidden_positive_claims(result)


@pytest.mark.asyncio
async def test_manual_provider_with_configured_data_returns_manual_source() -> None:
    provider = ManualPriceResearchProvider(
        sources=(_manual_source(),),
        reference_prices=(_manual_reference_price(),),
        confidence=0.75,
        warnings=("Manual reference evidence only; not approved quotation.",),
        retrieved_at=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
    )

    result = await provider.research_price(_request())

    assert result.provider == "manual"
    assert result.is_final_quote is False
    assert result.sources[0].source_type is PriceResearchSourceType.MANUAL
    assert result.reference_prices[0].amount == Decimal("13000000")
    _assert_no_forbidden_positive_claims(result)


def test_provider_factory_returns_fake_and_manual() -> None:
    assert isinstance(get_price_research_provider("FAKE"), FakePriceResearchProvider)
    assert isinstance(
        get_price_research_provider(" manual "),
        ManualPriceResearchProvider,
    )


def test_provider_factory_rejects_unknown_provider() -> None:
    with pytest.raises(PriceResearchProviderError, match="Unsupported"):
        get_price_research_provider("external_web")


def test_provider_factory_rejects_tavily_without_explicit_injection() -> None:
    with pytest.raises(PriceResearchProviderError, match="explicit provider injection"):
        get_price_research_provider("tavily")


@pytest.mark.asyncio
async def test_service_enabled_with_fake_provider_name_delegates_successfully() -> None:
    service = PriceResearchService(enabled=True, provider_name="fake")

    result = await service.research_price(_request())

    assert result.provider == "fake"
    assert result.sources[0].source_type is PriceResearchSourceType.FAKE


@pytest.mark.asyncio
async def test_service_enabled_with_manual_delegates_successfully() -> None:
    service = PriceResearchService(enabled=True, provider_name="manual")

    result = await service.research_price(_request())

    assert result.provider == "manual"
    assert result.reference_prices == ()
    assert any(
        "Manual price research is required" in warning for warning in result.warnings
    )


@pytest.mark.asyncio
async def test_fake_and_manual_providers_do_not_attempt_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import http.client
    import urllib.request

    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    monkeypatch.setattr(http.client.HTTPConnection, "request", fail_network)

    fake_result = await FakePriceResearchProvider().research_price(_request())
    manual_result = await ManualPriceResearchProvider().research_price(_request())

    assert fake_result.provider == "fake"
    assert manual_result.provider == "manual"


def test_settings_defaults_are_safe_and_disabled() -> None:
    settings = Settings()

    assert settings.price_research_enabled is False
    assert settings.price_research_provider == "fake"
    assert settings.price_research_timeout_seconds == 30
    assert settings.price_research_max_sources == 5
    assert settings.price_research_default_region == "VN"
    assert settings.price_research_default_currency == "VND"
    assert settings.tavily_api_key == ""
    assert settings.tavily_search_url == "https://api.tavily.com/search"
    assert settings.tavily_max_results == 5
    assert settings.tavily_include_raw_content is False
    assert settings.tavily_search_depth == "basic"


def test_settings_allow_safe_price_research_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PRICE_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("PRICE_RESEARCH_PROVIDER", "MANUAL")
    monkeypatch.setenv("PRICE_RESEARCH_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("PRICE_RESEARCH_MAX_SOURCES", "3")
    monkeypatch.setenv("PRICE_RESEARCH_DEFAULT_REGION", "vn")
    monkeypatch.setenv("PRICE_RESEARCH_DEFAULT_CURRENCY", "usd")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
    monkeypatch.setenv("TAVILY_SEARCH_URL", "https://api.tavily.test/search")
    monkeypatch.setenv("TAVILY_MAX_RESULTS", "7")
    monkeypatch.setenv("TAVILY_INCLUDE_RAW_CONTENT", "true")
    monkeypatch.setenv("TAVILY_SEARCH_DEPTH", "ADVANCED")

    settings = Settings()

    assert settings.price_research_enabled is True
    assert settings.price_research_provider == "manual"
    assert settings.price_research_timeout_seconds == 12
    assert settings.price_research_max_sources == 3
    assert settings.price_research_default_region == "VN"
    assert settings.price_research_default_currency == "USD"
    assert settings.tavily_api_key == "tvly-test-key"
    assert settings.tavily_search_url == "https://api.tavily.test/search"
    assert settings.tavily_max_results == 7
    assert settings.tavily_include_raw_content is True
    assert settings.tavily_search_depth == "advanced"


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
