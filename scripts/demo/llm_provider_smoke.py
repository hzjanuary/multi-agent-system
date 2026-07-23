#!/usr/bin/env python3
"""Optional local smoke check for the Ollama LLM provider endpoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_TIMEOUT_SECONDS = 30
SMOKE_PROMPT = "Reply with exactly: ok"


@dataclass(frozen=True)
class SmokeConfig:
    """Resolved local smoke configuration."""

    provider: str
    model: str
    base_url: str
    timeout_seconds: int
    dry_run: bool
    json_output: bool


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Manual local smoke check for the configured LLM provider. "
            "Only Ollama and fake no-call checks are supported."
        ),
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "ollama"),
        choices=("ollama", "fake"),
        help="Provider to check. Defaults to LLM_PROVIDER or ollama.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
        help="Ollama base URL. Defaults to OLLAMA_BASE_URL or localhost.",
    )
    parser.add_argument(
        "--model",
        default=(
            os.getenv("OLLAMA_MODEL")
            or os.getenv("LLM_MODEL")
            or DEFAULT_OLLAMA_MODEL
        ),
        help="Model name. Defaults to OLLAMA_MODEL, LLM_MODEL, or llama3.1:8b.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=int(os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
        help="Provider request timeout in seconds.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve configuration without calling a provider.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a bounded JSON summary.",
    )
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> SmokeConfig:
    """Build a bounded config object from parsed args."""
    timeout_seconds = max(1, min(args.timeout_seconds, 300))
    return SmokeConfig(
        provider=args.provider,
        model=str(args.model).strip(),
        base_url=str(args.base_url).strip().rstrip("/"),
        timeout_seconds=timeout_seconds,
        dry_run=bool(args.dry_run),
        json_output=bool(args.json),
    )


def run_smoke(config: SmokeConfig) -> dict[str, Any]:
    """Run the selected local smoke check and return a safe summary."""
    if config.provider == "fake":
        return {
            "provider": "fake",
            "model": config.model or "fake-deterministic-model",
            "status": "ok",
            "provider_call": False,
        }

    if config.dry_run:
        return {
            "provider": "ollama",
            "model": config.model,
            "base_url": config.base_url,
            "status": "dry_run",
            "provider_call": False,
        }

    if not config.model:
        return {
            "provider": "ollama",
            "status": "configuration_error",
            "message": "OLLAMA_MODEL or --model is required.",
        }
    if not config.base_url.startswith(("http://", "https://")):
        return {
            "provider": "ollama",
            "model": config.model,
            "status": "configuration_error",
            "message": "OLLAMA_BASE_URL must start with http:// or https://.",
        }

    return _call_ollama(config)


def _call_ollama(config: SmokeConfig) -> dict[str, Any]:
    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": SMOKE_PROMPT}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 16},
    }
    request = Request(
        f"{config.base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=config.timeout_seconds) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
            body = _decode_json_object(raw_body)
    except HTTPError as exc:
        return {
            "provider": "ollama",
            "model": config.model,
            "base_url": config.base_url,
            "status": "http_error",
            "http_status": exc.code,
        }
    except TimeoutError:
        return {
            "provider": "ollama",
            "model": config.model,
            "base_url": config.base_url,
            "status": "timeout",
        }
    except URLError:
        return {
            "provider": "ollama",
            "model": config.model,
            "base_url": config.base_url,
            "status": "unavailable",
        }

    message = body.get("message") if isinstance(body.get("message"), dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    return {
        "provider": "ollama",
        "model": str(body.get("model") or config.model)[:200],
        "base_url": config.base_url,
        "status": "ok" if isinstance(content, str) and content.strip() else "invalid_response",
        "response_chars": len(content) if isinstance(content, str) else 0,
        "provider_call": True,
    }


def _decode_json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def print_summary(summary: dict[str, Any], *, json_output: bool) -> None:
    """Print a bounded summary without prompts, tokens, keys, or response content."""
    if json_output:
        print(json.dumps(summary, sort_keys=True))
        return
    fields = [
        f"provider={summary.get('provider', 'unknown')}",
        f"model={summary.get('model', 'unknown')}",
        f"status={summary.get('status', 'unknown')}",
    ]
    if "base_url" in summary:
        fields.append(f"base_url={summary['base_url']}")
    if "response_chars" in summary:
        fields.append(f"response_chars={summary['response_chars']}")
    if "message" in summary:
        fields.append(f"message={summary['message']}")
    print(" ".join(fields))


def main(argv: list[str] | None = None) -> int:
    """Run the smoke command."""
    config = config_from_args(parse_args(argv or sys.argv[1:]))
    summary = run_smoke(config)
    print_summary(summary, json_output=config.json_output)
    return 0 if summary.get("status") in {"ok", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
