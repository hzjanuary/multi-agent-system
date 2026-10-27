"""Closed, bounded error metadata; never retain provider messages or raw bodies."""

from __future__ import annotations

import json
import re
from contextlib import suppress
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.llm.clients.http import HTTPResponse
    from app.llm.contracts import LLMChatRequest

Label = Annotated[str, Field(max_length=128)]
HEADER_NAMES = frozenset(
    {
        "retry-after",
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-reset",
        "ratelimit-limit",
        "ratelimit-remaining",
        "ratelimit-reset",
    }
    | {
        f"x-ratelimit-{a}-{b}"
        for a in ("limit", "remaining", "reset")
        for b in ("requests", "tokens")
    }
)


class ProviderDiagnostics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    http_status: int = Field(ge=100, le=599)
    application_request_id: Label | None = None
    error_code: Label | int | None = None
    error_type: Label | None = None
    provider_name: Label | None = None
    upstream_error_code: Label | int | None = None
    upstream_error_type: Label | None = None
    response_identifiers: dict[str, Label] = Field(default_factory=dict, max_length=6)
    received_limit_headers: dict[str, Label] = Field(
        default_factory=dict, max_length=16
    )


def extract_diagnostics(
    response: HTTPResponse, request: LLMChatRequest, api_key: str
) -> ProviderDiagnostics:
    denied = [api_key] if api_key else []

    def leaves(value: Any, depth: int = 0) -> None:
        if depth > 8:
            return
        if isinstance(value, str) and value:
            denied.append(value)
        elif isinstance(value, dict):
            for item in list(value.values())[:128]:
                leaves(item, depth + 1)
        elif isinstance(value, list):
            for item in value[:128]:
                leaves(item, depth + 1)

    for message in request.messages:
        denied.append(message.content)
        with suppress(ValueError, TypeError):
            leaves(json.loads(message.content))

    def label(value: Any, *, header: bool = False) -> str | None:
        if not isinstance(value, str) or not 1 <= len(value) <= 128:
            return None
        if any(secret and secret in value for secret in denied):
            return None
        if re.search(r"(?i)bearer|authorization|sk-|eyJ", value):
            return None
        pattern = r"[A-Za-z0-9 .,:;=+/_-]+" if header else r"[A-Za-z0-9 ._:/-]+"
        return value if re.fullmatch(pattern, value) else None

    def code(value: Any) -> str | int | None:
        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and -999999 <= value <= 999999
        ):
            return value
        return label(value)

    body = response.payload
    error = body.get("error")
    if not isinstance(error, dict):
        errors = body.get("errors")
        error = (
            errors[0]
            if isinstance(errors, list) and errors and isinstance(errors[0], dict)
            else {}
        )
    metadata = error.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    upstream: dict[str, Any] = {}
    raw = metadata.get("raw")
    if (
        isinstance(raw, str)
        and len(raw) <= 8192
        and isinstance(metadata.get("provider_name"), str)
    ):
        with suppress(ValueError, TypeError):
            decoded = json.loads(raw)
            if isinstance(decoded, dict) and isinstance(decoded.get("error"), dict):
                upstream = decoded["error"]
    headers = {name.lower(): value for name, value in response.headers.items()}
    ids = {}
    for name, value in (
        ("body_id", body.get("id")),
        ("header_x_request_id", headers.get("x-request-id")),
        ("header_x_openrouter_request_id", headers.get("x-openrouter-request-id")),
        ("metadata_request_id", metadata.get("request_id")),
        ("metadata_provider_request_id", metadata.get("provider_request_id")),
    ):
        safe = label(value)
        if safe is not None:
            ids[name] = safe
    limits = {}
    for name in HEADER_NAMES:
        safe = label(headers.get(name), header=True)
        if safe is not None:
            limits[name] = safe
    return ProviderDiagnostics(
        http_status=response.status_code,
        application_request_id=label(request.request_id),
        error_code=code(error.get("code")),
        error_type=label(error.get("type")),
        provider_name=label(metadata.get("provider_name"))
        or label(body.get("provider")),
        upstream_error_code=code(metadata.get("upstream_error_code"))
        or code(upstream.get("code")),
        upstream_error_type=label(upstream.get("status"))
        or label(upstream.get("type")),
        response_identifiers=ids,
        received_limit_headers=limits,
    )
