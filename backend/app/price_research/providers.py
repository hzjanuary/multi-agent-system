"""Provider interface for reference price research."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

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


def get_price_research_provider(provider_name: str) -> PriceResearchProvider:
    """Return a no-network price research provider by stable name."""
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
        raise PriceResearchProviderError(
            "Tavily price research provider requires an injected API key and "
            "transport",
            category=PriceResearchErrorCategory.CONFIGURATION,
        )
    raise PriceResearchProviderError(
        f"Unsupported price research provider: {provider_name}",
    )
