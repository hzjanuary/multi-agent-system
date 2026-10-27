"""Cancellable asynchronous JSON transport with bounded response bodies."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field


class HTTPResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    status_code: int = Field(ge=100, le=599)
    payload: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)


class HTTPTransportError(Exception):
    pass


class HTTPTimeoutError(HTTPTransportError):
    pass


class AsyncJSONHTTPTransport(Protocol):
    async def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: int,
    ) -> HTTPResponse: ...


class HTTPXAsyncJSONHTTPTransport:
    async def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: int,
    ) -> HTTPResponse:
        try:
            async with (
                asyncio.timeout(timeout_seconds),
                httpx.AsyncClient(
                    timeout=timeout_seconds,
                    follow_redirects=False,
                    trust_env=False,
                    transport=httpx.AsyncHTTPTransport(retries=0),
                ) as client,
                client.stream("POST", url, headers=headers, json=payload) as response,
            ):
                chunks = bytearray()
                async for chunk in response.aiter_bytes():
                    chunks.extend(chunk)
                    if len(chunks) > 1048576:
                        raise HTTPTransportError(
                            "provider response exceeds transport limit"
                        )
                try:
                    body = json.loads(chunks) if chunks else {}
                except (ValueError, UnicodeDecodeError):
                    body = {}
                return HTTPResponse(
                    status_code=response.status_code,
                    payload=body if isinstance(body, dict) else {},
                    headers=dict(response.headers),
                )
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise HTTPTimeoutError("provider request timed out") from exc
        except httpx.HTTPError as exc:
            raise HTTPTransportError("provider request failed") from exc


def retry_after_seconds(response: HTTPResponse) -> float | None:
    """Honor only bounded numeric Retry-After values; never expose header text."""
    raw = next(
        (v for k, v in response.headers.items() if k.lower() == "retry-after"), ""
    )
    try:
        return max(0.0, min(8.0, float(raw))) if raw else None
    except ValueError:
        return None
