"""Provider-independent LLM request and response contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LLMProvider(StrEnum):
    """Supported LLM provider identifiers."""

    OPENAI_COMPATIBLE = "openai_compatible"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    GEMINI = "gemini"


class LLMMessageRole(StrEnum):
    """Provider-independent chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMResponseFormat(StrEnum):
    """Requested response format."""

    TEXT = "text"
    JSON_OBJECT = "json_object"


class LLMFinishReason(StrEnum):
    """Normalized provider finish reasons."""

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"
    UNKNOWN = "unknown"


class LLMErrorCategory(StrEnum):
    """Safe provider error categories."""

    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    SAFETY = "safety"
    CANCELLATION = "cancellation"
    UNKNOWN = "unknown"


class LLMChatMessage(BaseModel):
    """Provider-independent chat message."""

    model_config = ConfigDict(frozen=True)

    role: LLMMessageRole
    content: str = Field(min_length=1, max_length=1048576)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMUsage(BaseModel):
    """Normalized token and cost usage metadata when providers expose it."""

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_total_tokens(self) -> LLMUsage:
        """Ensure total tokens is not lower than known token components."""
        if self.total_tokens is None:
            return self
        component_total = sum(
            token_count
            for token_count in (self.prompt_tokens, self.completion_tokens)
            if token_count is not None
        )
        if component_total and self.total_tokens < component_total:
            raise ValueError("total_tokens cannot be lower than token components")
        return self


class LLMStructuredResponseMetadata(BaseModel):
    """Metadata describing a validated structured response."""

    model_config = ConfigDict(frozen=True)

    schema_name: str = Field(min_length=1, max_length=120)
    schema_version: str | None = Field(default=None, min_length=1, max_length=40)
    validated: bool = True


class LLMChatRequest(BaseModel):
    """Provider-independent chat completion request."""

    model_config = ConfigDict(frozen=True)

    messages: tuple[LLMChatMessage, ...] = Field(min_length=1)
    provider: LLMProvider | None = None
    model: str | None = Field(default=None, min_length=1, max_length=200)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=200000)
    response_format: LLMResponseFormat = LLMResponseFormat.TEXT
    structured_json: bool = False
    request_id: str | None = Field(default=None, min_length=1, max_length=120)
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("messages", mode="before")
    @classmethod
    def coerce_messages(
        cls,
        value: tuple[LLMChatMessage, ...] | list[LLMChatMessage],
    ) -> tuple[LLMChatMessage, ...] | list[LLMChatMessage]:
        """Accept list input while storing messages immutably."""
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_structured_format(self) -> LLMChatRequest:
        """Keep structured JSON requests aligned with JSON response format."""
        if (
            self.structured_json
            and self.response_format is not LLMResponseFormat.JSON_OBJECT
        ):
            raise ValueError(
                "structured_json requests require JSON_OBJECT response format",
            )
        return self


class LLMChatResponse(BaseModel):
    """Provider-independent chat completion response."""

    model_config = ConfigDict(frozen=True)

    provider: LLMProvider
    model: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=10485760)
    structured_json: dict[str, Any] | None = None
    structured_metadata: LLMStructuredResponseMetadata | None = None
    finish_reason: LLMFinishReason = LLMFinishReason.UNKNOWN
    usage: LLMUsage | None = None
    request_id: str | None = Field(default=None, min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMModelCapabilities(BaseModel):
    """Provider-independent model capability metadata."""

    model_config = ConfigDict(frozen=True)

    provider: LLMProvider
    model: str = Field(min_length=1, max_length=200)
    supports_chat: bool = True
    supports_json_mode: bool = False
    supports_structured_output: bool = False
    supports_tools: bool = False
    supports_streaming: bool = False
    is_local: bool = False
    max_input_tokens: int | None = Field(default=None, ge=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
