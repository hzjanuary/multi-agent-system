"""Provider interface for reference price research."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.config import Settings, get_settings
from app.price_research.exceptions import (
    PriceResearchErrorCategory,
    PriceResearchProviderError,
)
from app.price_research.schemas import PriceResearchRequest, PriceResearchResult


@runtime_checkable
class PriceResearchProvider(Protocol):
    """Async provider-independent reference price research contract.

    Providers return bounded reference evidence only. They must not issue final
    quotes, promise stock or delivery, expose raw prompts/provider payloads, or
    bypass the human approval lifecycle.
    """

    @property
    def name(self) -> str:
        """Return stable provider identifier."""

    async def research_price(
        self,
        request: PriceResearchRequest,
    ) -> PriceResearchResult:
        """Return normalized reference price evidence for a supported request."""


def get_price_research_provider(
    provider_name: str,
    *,
    settings: Settings | None = None,
) -> PriceResearchProvider:
    """Return a price research provider by stable name.

    Deterministic no-network providers (``fake``, ``manual``) are returned
    directly. Network-capable providers require settings: ``tavily`` is built
    from the environment-only ``TAVILY_API_KEY`` setting and fails closed with a
    ``CONFIGURATION`` error when no key is configured. ``rag`` requires an
    injected knowledge search dependency. The returned provider performs no
    network access until ``research_price`` is called.
    """
    resolved = settings or get_settings()
    normalized = provider_name.strip().lower()
    if normalized == "fake":
        from app.price_research.fake_provider import FakePriceResearchProvider

        return FakePriceResearchProvider()
    if normalized == "manual":
        from app.price_research.manual_provider import ManualPriceResearchProvider

        return ManualPriceResearchProvider()
    if normalized == "rag":
        raise PriceResearchProviderError(
            "RAG price research provider requires an injected knowledge search "
            "dependency",
        )
    if normalized == "tavily":
        api_key = resolved.price_research_tavily_api_key.strip()
        if not api_key:
            raise PriceResearchProviderError(
                "Tavily price research provider requires an injected API key and "
                "transport",
                category=PriceResearchErrorCategory.CONFIGURATION,
            )
        from app.price_research.web_provider import TavilyPriceResearchProvider

        return TavilyPriceResearchProvider(
            api_key=api_key,
            timeout_seconds=resolved.price_research_timeout_seconds,
            max_results=resolved.tavily_max_results,
        )
    raise PriceResearchProviderError(
        f"Unsupported price research provider: {provider_name}",
    )
