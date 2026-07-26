#!/usr/bin/env python3
"""Manual-only Tavily live smoke utility for reference evidence verification.

This command is intentionally isolated from Telegram, workflows, frontend
routes, backend APIs, and CI. Live provider calls require both a local
`TAVILY_API_KEY` and the explicit `--confirm-live-provider` flag.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"

DEFAULT_PROVIDER = "tavily"
DEFAULT_TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DEFAULT_REGION = "VN"
DEFAULT_CURRENCY = "VND"
DEFAULT_QUANTITY = 1
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RESULTS = 5
MAX_TEXT_CHARS = 320
MAX_URL_CHARS = 300
MAX_SOURCES = 5
MAX_REFERENCE_PRICES = 5
MAX_WARNINGS = 8
SENSITIVE_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "chain_of_thought",
    "cookie",
    "jwt",
    "password",
    "provider_payload",
    "raw_html",
    "raw_model",
    "raw_prompt",
    "raw_provider",
    "secret",
    "token",
)

ProviderRunner = Callable[["LiveSmokeConfig", "SmokeRequest"], Awaitable[object]]


@dataclass(frozen=True)
class LiveSmokeConfig:
    """Resolved manual provider live-smoke configuration."""

    provider: str
    item: str
    normalized_item: str
    quantity: int
    region: str
    currency: str
    requested_addons: tuple[str, ...]
    confirm_live_provider: bool
    dry_run: bool
    pretty: bool
    timeout_seconds: int
    max_results: int
    tavily_api_key: str
    tavily_search_url: str
    tavily_include_raw_content: bool
    tavily_search_depth: str


@dataclass(frozen=True)
class SmokeRequest:
    """Dependency-light provider-independent request shape for smoke output."""

    item_name: str
    normalized_item_name: str
    quantity: int
    region: str
    currency: str
    requested_addons: tuple[str, ...]


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Manual-only Tavily provider live smoke. Dry-run is no-key and "
            "no-network; live mode requires --confirm-live-provider and "
            "TAVILY_API_KEY."
        ),
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("PRICE_RESEARCH_PROVIDER", DEFAULT_PROVIDER),
        help="Provider to verify. Currently only tavily is supported.",
    )
    parser.add_argument(
        "--item",
        required=True,
        help="Catalog item or query input, for example 'Standard business laptop'.",
    )
    parser.add_argument(
        "--normalized-item",
        default="",
        help="Optional normalized item name. Defaults to --item.",
    )
    parser.add_argument(
        "--quantity",
        type=int,
        default=DEFAULT_QUANTITY,
        help="Positive quantity basis for the request. Defaults to 1.",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("PRICE_RESEARCH_DEFAULT_REGION", DEFAULT_REGION),
        help="Research region. Defaults to VN.",
    )
    parser.add_argument(
        "--currency",
        default=os.getenv("PRICE_RESEARCH_DEFAULT_CURRENCY", DEFAULT_CURRENCY),
        help="Currency code. Defaults to VND.",
    )
    parser.add_argument(
        "--requested-addon",
        action="append",
        default=[],
        help="Optional requested add-on. Can be passed multiple times.",
    )
    parser.add_argument(
        "--confirm-live-provider",
        action="store_true",
        help="Required before any live provider network call.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print request shape and safety notes without calling Tavily.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=int(
            os.getenv("PRICE_RESEARCH_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)),
        ),
        help="Provider timeout in seconds.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=int(os.getenv("TAVILY_MAX_RESULTS", str(DEFAULT_MAX_RESULTS))),
        help="Maximum Tavily results to request, bounded 1..10.",
    )
    parser.add_argument(
        "--search-url",
        default=os.getenv("TAVILY_SEARCH_URL", DEFAULT_TAVILY_SEARCH_URL),
        help="Tavily search URL. Defaults to the official search endpoint.",
    )
    parser.add_argument(
        "--search-depth",
        default=os.getenv("TAVILY_SEARCH_DEPTH", "basic"),
        help="Tavily search depth: basic or advanced.",
    )
    parser.add_argument(
        "--include-raw-content",
        action="store_true",
        default=os.getenv("TAVILY_INCLUDE_RAW_CONTENT", "false").lower() == "true",
        help="Forward include_raw_content to Tavily. Output still never prints raw payloads.",
    )
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> LiveSmokeConfig:
    """Build a normalized smoke config from parsed arguments and environment."""
    provider = str(args.provider).strip().lower()
    item = str(args.item).strip()
    normalized_item = str(args.normalized_item or item).strip()
    return LiveSmokeConfig(
        provider=provider,
        item=item,
        normalized_item=normalized_item,
        quantity=max(1, int(args.quantity)),
        region=str(args.region).strip().upper(),
        currency=str(args.currency).strip().upper(),
        requested_addons=tuple(
            dict.fromkeys(
                addon.strip().lower()
                for addon in args.requested_addon
                if str(addon).strip()
            ),
        ),
        confirm_live_provider=bool(args.confirm_live_provider),
        dry_run=bool(args.dry_run),
        pretty=bool(args.pretty),
        timeout_seconds=max(1, min(int(args.timeout_seconds), 120)),
        max_results=max(1, min(int(args.max_results), 10)),
        tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
        tavily_search_url=str(args.search_url).strip(),
        tavily_include_raw_content=bool(args.include_raw_content),
        tavily_search_depth=str(args.search_depth).strip().lower(),
    )


async def run_smoke(
    config: LiveSmokeConfig,
    *,
    provider_runner: ProviderRunner | None = None,
) -> tuple[int, dict[str, Any]]:
    """Run dry-run or live smoke and return `(exit_code, safe_summary)`."""
    if config.provider != "tavily":
        return 2, error_summary(
            "unsupported_provider",
            f"Unsupported provider '{safe_text(config.provider)}'. Only tavily is supported.",
            config=config,
        )

    request = build_smoke_request(config)

    if config.dry_run:
        return 0, dry_run_summary(config, request)

    if not config.confirm_live_provider:
        return 2, error_summary(
            "missing_confirmation",
            "Live provider smoke requires --confirm-live-provider.",
            config=config,
        )

    if not config.tavily_api_key:
        return 2, error_summary(
            "missing_api_key",
            "A local Tavily provider key is required for live Tavily smoke.",
            config=config,
        )

    try:
        result = await (provider_runner or run_tavily_provider)(config, request)
    except TimeoutError:
        return 1, error_summary(
            "provider_timeout",
            "Tavily live smoke timed out.",
            config=config,
        )
    except Exception as exc:  # provider errors must remain safe and bounded
        return 1, error_summary(
            "provider_error",
            safe_provider_error_message(exc),
            config=config,
        )

    return 0, success_summary(config, request, result)


def build_smoke_request(config: LiveSmokeConfig) -> SmokeRequest:
    """Create dependency-light provider-independent request from CLI input."""
    return SmokeRequest(
        item_name=config.item,
        normalized_item_name=config.normalized_item,
        quantity=config.quantity,
        region=config.region,
        currency=config.currency,
        requested_addons=config.requested_addons,
    )


async def run_tavily_provider(
    config: LiveSmokeConfig,
    request: SmokeRequest,
) -> object:
    """Run the Tavily provider through the existing adapter."""
    if str(BACKEND_PATH) not in sys.path:
        sys.path.insert(0, str(BACKEND_PATH))

    from app.price_research.schemas import PriceResearchRequest
    from app.price_research.tavily_provider import TavilyPriceResearchProvider

    provider_request = PriceResearchRequest(
        item_name=request.item_name,
        normalized_item_name=request.normalized_item_name,
        quantity=request.quantity,
        region=request.region,
        currency=request.currency,
        requested_addons=request.requested_addons,
        customer_context={"source": "manual_provider_live_smoke"},
    )
    provider = TavilyPriceResearchProvider(
        api_key=config.tavily_api_key,
        search_url=config.tavily_search_url,
        timeout_seconds=config.timeout_seconds,
        max_results=config.max_results,
        include_raw_content=config.tavily_include_raw_content,
        search_depth=config.tavily_search_depth,
    )
    return await provider.research_price(provider_request)


def dry_run_summary(
    config: LiveSmokeConfig,
    request: SmokeRequest,
) -> dict[str, Any]:
    """Return a no-network request summary."""
    return {
        "status": "dry_run",
        "dry_run": True,
        "provider_call": False,
        "provider": config.provider,
        "request": request_summary(request),
        "safety": safety_notes(),
    }


def success_summary(
    config: LiveSmokeConfig,
    request: SmokeRequest,
    result: object,
) -> dict[str, Any]:
    """Return bounded live smoke result output."""
    return {
        "status": "ok",
        "dry_run": False,
        "provider_call": True,
        "provider": config.provider,
        "request": request_summary(request),
        "result": result_summary(result),
        "safety": safety_notes(),
    }


def error_summary(
    code: str,
    message: str,
    *,
    config: LiveSmokeConfig | None = None,
) -> dict[str, Any]:
    """Return a safe error summary."""
    summary: dict[str, Any] = {
        "status": "error",
        "error_code": code,
        "message": safe_text(message),
        "provider_call": False,
        "safety": safety_notes(),
    }
    if config is not None:
        summary["provider"] = safe_text(config.provider, 80)
        summary["dry_run"] = config.dry_run
    return summary


def request_summary(request: SmokeRequest) -> dict[str, Any]:
    """Return bounded request metadata without raw customer context."""
    return {
        "item_name": safe_text(request.item_name),
        "normalized_item_name": safe_text(request.normalized_item_name),
        "quantity": request.quantity,
        "region": safe_text(request.region, 80),
        "currency": safe_text(request.currency, 16),
        "requested_addons": [safe_text(addon, 80) for addon in request.requested_addons],
    }


def result_summary(result: object) -> dict[str, Any]:
    """Return bounded normalized reference evidence output."""
    data = result_mapping(result)
    return {
        "provider": safe_text(data.get("provider"), 80),
        "evidence_label": safe_text(
            data.get("evidence_label") or "reference_price_research",
            80,
        ),
        "is_final_quote": False,
        "confidence": safe_confidence(data.get("confidence")),
        "retrieved_at": safe_text(data.get("retrieved_at"), 120),
        "reference_prices": [
            {
                "label": safe_text(as_mapping(price).get("label")),
                "amount": safe_text(as_mapping(price).get("amount"), 80),
                "currency": safe_text(as_mapping(price).get("currency"), 16),
                "unit": safe_text(as_mapping(price).get("unit"), 80),
                "quantity_basis": as_mapping(price).get("quantity_basis"),
                "notes": safe_text(as_mapping(price).get("notes")),
            }
            for price in as_list(data.get("reference_prices"))[:MAX_REFERENCE_PRICES]
        ],
        "sources": [
            {
                "title": safe_text(as_mapping(source).get("title")),
                "url": safe_url(as_mapping(source).get("url")),
                "snippet": safe_text(as_mapping(source).get("snippet")),
                "source_type": safe_text(as_mapping(source).get("source_type"), 80),
                "confidence": safe_confidence(as_mapping(source).get("confidence")),
            }
            for source in as_list(data.get("sources"))[:MAX_SOURCES]
        ],
        "warnings": [
            safe_text(warning)
            for warning in as_list(data.get("warnings"))[:MAX_WARNINGS]
        ],
    }


def result_mapping(result: object) -> Mapping[str, Any]:
    """Return a JSON-like mapping from a Pydantic model or injected test dict."""
    if isinstance(result, Mapping):
        return result
    model_dump = getattr(result, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def as_mapping(value: object) -> Mapping[str, Any]:
    """Return mapping values only."""
    return value if isinstance(value, Mapping) else {}


def as_list(value: object) -> list[object]:
    """Return list-like values as a list."""
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


def safe_confidence(value: object) -> float:
    """Normalize confidence values into 0..1."""
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return max(0.0, min(float(value), 1.0))
    return 0.0


def safety_notes() -> list[str]:
    """Return stable smoke safety notes."""
    return [
        "Manual provider smoke only; not part of CI.",
        "Reference evidence only; not a customer quotation.",
        "No Telegram, workflow, frontend, approval, resume, or email side effects.",
    ]


def safe_provider_error_message(exc: Exception) -> str:
    """Return provider error text without raw payloads or secrets."""
    return safe_text(str(exc), 240)


def safe_url(value: str | None) -> str | None:
    """Return a bounded safe URL string."""
    text = safe_text(value, MAX_URL_CHARS)
    if text == "[redacted]":
        return text
    return text


def safe_text(value: object, limit: int = MAX_TEXT_CHARS) -> str:
    """Return bounded text with HTML stripped and sensitive markers redacted."""
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if contains_sensitive_marker(text):
        return "[redacted]"
    return text[:limit].strip()


def contains_sensitive_marker(value: str) -> bool:
    """Return true when a value appears to contain secrets or raw payload markers."""
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_MARKERS)


def print_json(summary: dict[str, Any], *, pretty: bool) -> None:
    """Print bounded JSON output."""
    if pretty:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    print(json.dumps(summary, separators=(",", ":"), sort_keys=True))


def main(
    argv: list[str] | None = None,
    *,
    provider_runner: ProviderRunner | None = None,
) -> int:
    """Run the manual smoke command."""
    config = config_from_args(parse_args(argv or sys.argv[1:]))
    exit_code, summary = asyncio.run(run_smoke(config, provider_runner=provider_runner))
    print_json(summary, pretty=config.pretty)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
