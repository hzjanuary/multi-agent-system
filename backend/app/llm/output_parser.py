"""Deterministic structured LLM output parsing helpers."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

from app.llm.contracts import LLMChatResponse, LLMErrorCategory
from app.llm.errors import LLMProviderError

_FENCED_JSON_PATTERN = re.compile(
    r"^\s*```(?:json|JSON)?\s*(?P<body>.*?)\s*```\s*$",
    re.DOTALL,
)
_MAX_ERROR_SNIPPET_LENGTH = 240


def parse_structured_output[StructuredOutputT: BaseModel](
    response: LLMChatResponse,
    output_schema: type[StructuredOutputT],
) -> StructuredOutputT:
    """Parse and validate a structured JSON response into a Pydantic schema."""
    raw_content = response.content.strip()
    json_text = _strip_simple_json_fence(raw_content)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise _invalid_response_error(
            response,
            "LLM response did not contain valid JSON",
            json_text,
        ) from exc
    if not isinstance(parsed, dict):
        raise _invalid_response_error(
            response,
            "LLM response JSON must be an object",
            json_text,
        )
    try:
        return output_schema.model_validate(parsed)
    except ValidationError as exc:
        raise _invalid_response_error(
            response,
            f"LLM response did not match {output_schema.__name__}",
            json_text,
        ) from exc


def _strip_simple_json_fence(content: str) -> str:
    match = _FENCED_JSON_PATTERN.match(content)
    if match is None:
        return content
    return match.group("body").strip()


def _invalid_response_error(
    response: LLMChatResponse,
    message: str,
    raw_content: str,
) -> LLMProviderError:
    return LLMProviderError(
        message,
        category=LLMErrorCategory.INVALID_RESPONSE,
        provider=response.provider,
        request_id=response.request_id,
        details={"snippet": _safe_error_snippet(raw_content)},
    )


def _safe_error_snippet(value: str) -> str:
    normalized = " ".join(value.replace("\x00", "").split())
    if len(normalized) <= _MAX_ERROR_SNIPPET_LENGTH:
        return normalized
    return f"{normalized[:_MAX_ERROR_SNIPPET_LENGTH]}..."


__all__ = ["parse_structured_output"]
