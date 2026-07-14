"""Shared deterministic prompt rendering utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.llm.contracts import (
    LLMChatMessage,
    LLMChatRequest,
    LLMMessageRole,
    LLMResponseFormat,
)

PROMPT_TEMPLATE_VERSION = "2026-07-14"
MAX_PROMPT_VALUE_LENGTH = 6000
MAX_CONTEXT_VALUE_LENGTH = 4000

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "password",
    "secret",
    "token",
)


def build_structured_json_request(
    *,
    stage_name: str,
    schema_name: str,
    task_instruction: str,
    workflow_request: Mapping[str, Any] | str,
    context: Mapping[str, Any] | None = None,
    request_id: str | None = None,
    max_tokens: int = 1200,
    temperature: float = 0,
) -> LLMChatRequest:
    """Build a provider-independent structured JSON chat request."""
    system_prompt = _render_system_prompt(stage_name, schema_name)
    user_prompt = _render_user_prompt(
        task_instruction=task_instruction,
        workflow_request=workflow_request,
        context=context,
    )
    return LLMChatRequest(
        messages=(
            LLMChatMessage(role=LLMMessageRole.SYSTEM, content=system_prompt),
            LLMChatMessage(role=LLMMessageRole.USER, content=user_prompt),
        ),
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=LLMResponseFormat.JSON_OBJECT,
        structured_json=True,
        request_id=request_id,
        metadata={
            "stage": stage_name,
            "expected_schema": schema_name,
            "prompt_version": PROMPT_TEMPLATE_VERSION,
        },
    )


def safe_prompt_json(value: Mapping[str, Any] | str, *, max_length: int) -> str:
    """Render deterministic, bounded JSON-safe prompt input."""
    if isinstance(value, str):
        rendered = value
    else:
        rendered = json.dumps(
            _sanitize_prompt_value(value),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    return _truncate_text(rendered, max_length)


def _render_system_prompt(stage_name: str, schema_name: str) -> str:
    return "\n".join(
        (
            "You are an enterprise procurement workflow assistant.",
            f"Stage: {stage_name}.",
            f"Return one JSON object that validates against {schema_name}.",
            "Use only the provided workflow request and context.",
            "Do not invent unsupported facts; mark uncertainty explicitly.",
            "Do not include hidden reasoning, chain-of-thought, secrets, "
            "or raw provider payloads.",
            "Keep every field concise and bounded for audit-safe workflow state.",
        ),
    )


def _render_user_prompt(
    *,
    task_instruction: str,
    workflow_request: Mapping[str, Any] | str,
    context: Mapping[str, Any] | None,
) -> str:
    request_json = safe_prompt_json(
        workflow_request,
        max_length=MAX_PROMPT_VALUE_LENGTH,
    )
    context_json = safe_prompt_json(
        context or {},
        max_length=MAX_CONTEXT_VALUE_LENGTH,
    )
    return "\n".join(
        (
            f"Task: {task_instruction}",
            "Workflow request:",
            request_json,
            "Available context:",
            context_json,
            "Return JSON only.",
        ),
    )


def _sanitize_prompt_value(value: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return "[truncated]"
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        sorted_items = sorted(value.items(), key=lambda pair: str(pair[0]))
        for index, (key, item) in enumerate(sorted_items):
            if index >= 40:
                sanitized["truncated"] = True
                break
            key_text = str(key)
            if _is_sensitive_key(key_text):
                sanitized[key_text] = "[redacted]"
            else:
                sanitized[key_text] = _sanitize_prompt_value(item, depth=depth + 1)
        return sanitized
    if isinstance(value, list | tuple):
        return [_sanitize_prompt_value(item, depth=depth + 1) for item in value[:30]]
    if isinstance(value, str):
        return _truncate_text(value, 1000)
    if isinstance(value, bool | int | float) or value is None:
        return value
    return _truncate_text(str(value), 300)


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _SENSITIVE_KEY_PARTS)


def _truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


__all__ = [
    "MAX_CONTEXT_VALUE_LENGTH",
    "MAX_PROMPT_VALUE_LENGTH",
    "PROMPT_TEMPLATE_VERSION",
    "build_structured_json_request",
    "safe_prompt_json",
]
