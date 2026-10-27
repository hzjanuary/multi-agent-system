"""Typed host-controlled OpenRouter routing, never accepted from workflow input."""

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpenRouterMaxPrice(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    prompt: float = Field(ge=0, allow_inf_nan=False)
    completion: float = Field(ge=0, allow_inf_nan=False)
    request: float = Field(ge=0, allow_inf_nan=False)


class OpenRouterProviderPreferences(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    data_collection: Literal["deny", "allow"] = "deny"
    zdr: bool = True
    allow_fallbacks: bool = False
    require_parameters: bool = True
    only: tuple[str, ...] = ()
    max_price: OpenRouterMaxPrice | None = None

    @field_validator("only")
    @classmethod
    def validate_routes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)) or any(
            not re.fullmatch(r"[a-z0-9][a-z0-9_./-]{0,119}", value) for value in values
        ):
            raise ValueError("provider routes must be unique canonical slugs")
        return values

    def request_dict(self) -> dict[str, Any]:
        value = self.model_dump(mode="json", exclude_none=True)
        if not self.only:
            value.pop("only")
        return value
