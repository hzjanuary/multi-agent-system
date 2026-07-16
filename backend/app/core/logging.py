"""Structured logging configuration."""

import logging
from typing import Any, Literal

import structlog

from app.core.observability import redacted_log_event

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["json", "text"]


def configure_logging(
    log_level: LogLevel,
    *,
    log_format: LogFormat = "json",
    redaction_enabled: bool = True,
) -> None:
    """Configure standard logging and structlog JSON output."""
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level),
    )
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if redaction_enabled:
        processors.append(redacted_log_event)
    processors.append(
        (
            structlog.processors.JSONRenderer()
            if log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ),
    )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level),
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
