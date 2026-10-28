"""One-shot key quota observation: closed field selection, no generation endpoint."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from scripts.ops import openrouter_free_smoke as smoke

TOP_NUMBERS = (
    "limit",
    "limit_remaining",
    "usage",
    "usage_daily",
    "usage_weekly",
    "usage_monthly",
)
BUDGET_NUMBERS = ("limit_usd", "spend_usd", "remaining_usd")
INTERVALS = ("daily", "weekly", "monthly")


def numeric(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def budget(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, dict):
        return {"invalid_type": True}
    result = {
        k: v
        for k, v in value.items()
        if k in BUDGET_NUMBERS and (v is None or numeric(v))
    }
    if isinstance(value.get("include_byok"), bool):
        result["include_byok"] = value["include_byok"]
    if "reset_interval" in value and (
        value["reset_interval"] is None or value["reset_interval"] in INTERVALS
    ):
        result["reset_interval"] = value["reset_interval"]
    if "resets_at" in value:
        if value["resets_at"] is None:
            result["resets_at"] = None
        elif isinstance(value["resets_at"], str):
            try:
                when = datetime.fromisoformat(value["resets_at"].replace("Z", "+00:00"))
                if when.tzinfo is not None:
                    result["resets_at"] = when.isoformat()
            except ValueError:
                pass
    return result


def sanitize(payload: Any) -> dict[str, Any]:
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        data = {}
    fields: dict[str, Any] = {}
    invalid = []
    expected = (
        *TOP_NUMBERS,
        "limit_reset",
        "is_free_tier",
        "free_model_daily_requests",
        "budgets",
        "effective_budget",
    )
    for name in TOP_NUMBERS:
        if name in data:
            if data[name] is None or numeric(data[name]):
                fields[name] = data[name]
            else:
                invalid.append(name)
    if "limit_reset" in data:
        if data["limit_reset"] is None or data["limit_reset"] in INTERVALS:
            fields["limit_reset"] = data["limit_reset"]
        else:
            invalid.append("limit_reset")
    if isinstance(data.get("is_free_tier"), bool):
        fields["is_free_tier"] = data["is_free_tier"]
    for name in ("free_model_daily_requests", "budgets", "effective_budget"):
        if name not in data:
            continue
        value = data[name]
        if value is None:
            fields[name] = None
        elif name == "free_model_daily_requests" and isinstance(value, dict):
            fields[name] = {
                k: v
                for k, v in value.items()
                if k in ("used", "limit", "remaining") and (v is None or numeric(v))
            }
        elif name == "budgets" and isinstance(value, list) and len(value) <= 32:
            fields[name] = [budget(v) for v in value]
        elif name == "effective_budget" and isinstance(value, dict):
            fields[name] = budget(value)
        else:
            invalid.append(name)
    free = fields.get("free_model_daily_requests")
    # This reports the free-route counter, never inferred from monetary usage.
    remaining = free.get("remaining") if isinstance(free, dict) else None
    limit = free.get("limit") if isinstance(free, dict) else None
    insufficient = numeric(remaining) and numeric(limit) and limit > 0 and remaining < 2
    return {
        "quota": fields,
        "missing_fields": [k for k in expected if k not in data],
        "invalid_fields": invalid,
        "free_request_quota": (
            "INSUFFICIENT_FOR_TWO"
            if insufficient
            else (
                "REPORTED_AT_LEAST_TWO"
                if numeric(remaining) and remaining >= 2
                else "UNKNOWN"
            )
        ),
        "old_failure_cause": "not determined by this current observation",
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def lookup() -> dict[str, Any]:
    config, _ = smoke.load_private(smoke.PRIVATE)
    smoke.check(bool(config["OPENROUTER_API_KEY"].strip()), "private_key_missing")
    folder = smoke.PRIVATE / "quota-correction-20261027"
    folder.mkdir(mode=0o700, exist_ok=True)
    smoke.check(
        not folder.is_symlink() and folder.stat().st_mode & 0o077 == 0,
        "private_quota_directory_required",
    )
    now = datetime.now(timezone.utc).isoformat()
    smoke.save_json(
        folder / "request.json",
        {
            "method": "GET",
            "url": smoke.API + "/key",
            "observed_at": now,
            "maximum_requests": 1,
        },
        exclusive=True,
    )
    result: dict[str, Any] = {
        "observed_at": now,
        "authenticated_get_attempts": 1,
        "additional_generation_requests": 0,
    }
    request = Request(
        smoke.API + "/key",
        method="GET",
        headers={
            "Authorization": "Bearer " + config["OPENROUTER_API_KEY"],
            "Accept": "application/json",
        },
    )
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        try:
            response = opener.open(request, timeout=25)
        except HTTPError as error:
            response = error
        with response:
            result["http_status"] = response.status
            raw = response.read(131073)
            smoke.check(len(raw) <= 131072, "key_response_too_large")
            result.update(sanitize(json.loads(raw)))
    except Exception as error:
        result["lookup_error_class"] = type(error).__name__
        result["free_request_quota"] = "UNKNOWN"
    smoke.save_json(folder / "sanitized.json", result, exclusive=True)
    return result


if __name__ == "__main__":
    print(json.dumps(lookup(), indent=2))
