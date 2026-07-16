"""Bounded in-process metrics for production-demo observability."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.observability import bound_string

DEFAULT_MAX_PATH_LABEL_LENGTH = 120


class RequestMetricSummary(BaseModel):
    """Aggregated request metrics for one low-cardinality label set."""

    model_config = ConfigDict(frozen=True)

    method: str = Field(min_length=1, max_length=12)
    path: str = Field(min_length=1, max_length=120)
    status_class: str = Field(pattern=r"^[1-5]xx$")
    count: int = Field(ge=0)
    duration_ms_min: float = Field(ge=0)
    duration_ms_max: float = Field(ge=0)
    duration_ms_avg: float = Field(ge=0)


class MetricsSnapshot(BaseModel):
    """Safe metrics endpoint response payload."""

    model_config = ConfigDict(frozen=True)

    uptime_seconds: float = Field(ge=0)
    process_start_time: datetime
    counters: dict[str, int]
    request_metrics: tuple[RequestMetricSummary, ...]


@dataclass
class _DurationStats:
    count: int = 0
    total_ms: float = 0.0
    min_ms: float | None = None
    max_ms: float | None = None

    def observe(self, duration_ms: float) -> None:
        bounded_duration = max(duration_ms, 0.0)
        self.count += 1
        self.total_ms += bounded_duration
        self.min_ms = (
            bounded_duration
            if self.min_ms is None
            else min(self.min_ms, bounded_duration)
        )
        self.max_ms = (
            bounded_duration
            if self.max_ms is None
            else max(self.max_ms, bounded_duration)
        )

    def summary(
        self,
        *,
        method: str,
        path: str,
        status_class: str,
    ) -> RequestMetricSummary:
        return RequestMetricSummary(
            method=method,
            path=path,
            status_class=status_class,
            count=self.count,
            duration_ms_min=round(self.min_ms or 0.0, 2),
            duration_ms_max=round(self.max_ms or 0.0, 2),
            duration_ms_avg=round(self.total_ms / self.count, 2) if self.count else 0.0,
        )


class InProcessMetrics:
    """Thread-safe enough in-memory metrics for a single demo process."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_path_label_length: int = DEFAULT_MAX_PATH_LABEL_LENGTH,
    ) -> None:
        self.enabled = enabled
        self.max_path_label_length = max_path_label_length
        self.process_start_time = datetime.now(UTC)
        self._lock = Lock()
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._request_stats: dict[tuple[str, str, str], _DurationStats] = {}

    def record_http_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record one HTTP request using bounded low-cardinality labels."""
        if not self.enabled:
            return

        normalized_method = method.upper()[:12]
        normalized_path = normalize_path_label(
            path,
            max_length=self.max_path_label_length,
        )
        status_class = status_class_label(status_code)
        key = (normalized_method, normalized_path, status_class)
        with self._lock:
            self._counters["http_requests_total"] += 1
            self._counters[f"http_requests_{status_class}_total"] += 1
            stats = self._request_stats.setdefault(key, _DurationStats())
            stats.observe(duration_ms)

    def increment(self, counter_name: str, amount: int = 1) -> None:
        """Increment a named counter with a bounded metric key."""
        if not self.enabled or amount <= 0:
            return
        safe_name = metric_key(counter_name)
        with self._lock:
            self._counters[safe_name] += amount

    def snapshot(self) -> MetricsSnapshot:
        """Return a deterministic safe metrics snapshot."""
        now = datetime.now(UTC)
        with self._lock:
            request_metrics = tuple(
                stats.summary(method=method, path=path, status_class=status_class)
                for (method, path, status_class), stats in sorted(
                    self._request_stats.items(),
                )
            )
            counters = dict(sorted(self._counters.items()))
        return MetricsSnapshot(
            uptime_seconds=round(
                (now - self.process_start_time).total_seconds(),
                3,
            ),
            process_start_time=self.process_start_time,
            counters=counters,
            request_metrics=request_metrics,
        )


def status_class_label(status_code: int) -> str:
    """Return a bounded status class label such as 2xx or 5xx."""
    if status_code < 100 or status_code > 599:
        return "5xx"
    return f"{status_code // 100}xx"


def route_template_for_scope(scope: Mapping[str, Any]) -> str | None:
    """Return a FastAPI route template from a request scope when available."""
    route = scope.get("route")
    route_path = getattr(route, "path", None)
    return route_path if isinstance(route_path, str) and route_path else None


def normalize_path_label(
    path: str,
    *,
    max_length: int = DEFAULT_MAX_PATH_LABEL_LENGTH,
) -> str:
    """Return a bounded low-cardinality path label."""
    clean_path = path.split("?", 1)[0] or "/"
    segments = [
        _normalize_path_segment(segment)
        for segment in clean_path.strip("/").split("/")
        if segment
    ]
    normalized = "/" + "/".join(segments) if segments else "/"
    return bound_string(normalized, max_length=max_length)


def metric_key(value: str) -> str:
    """Return a safe bounded metric key."""
    safe = "".join(char if char.isalnum() or char == "_" else "_" for char in value)
    return bound_string(safe.strip("_") or "metric", max_length=120)


def _normalize_path_segment(segment: str) -> str:
    if segment.isdigit():
        return "{id}"
    normalized = segment.lower()
    if _looks_like_uuid(normalized):
        return "{id}"
    return segment


def _looks_like_uuid(value: str) -> bool:
    if len(value) != 36:
        return False
    return all(char in "0123456789abcdef-" for char in value) and value.count("-") == 4


__all__ = [
    "DEFAULT_MAX_PATH_LABEL_LENGTH",
    "InProcessMetrics",
    "MetricsSnapshot",
    "RequestMetricSummary",
    "metric_key",
    "normalize_path_label",
    "route_template_for_scope",
    "status_class_label",
]
