"""Test-only extensions and fault boundaries; never packaged in release image."""

import asyncio
import os
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.definitions import (
    AgentDefinition,
    NodeDefinition,
    Registry,
    ToolDefinition,
    WorkflowDefinition,
)

EXTENSION_VERSION = "test-1"


class Text(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str


class Number(BaseModel):
    value: int


def uppercase(value: Text) -> Text:
    return Text(text=value.text.upper())


async def boundary(value: Text) -> Text:
    if os.getenv("MAOS_TEST_BLOCK_NODE") == "1":
        await asyncio.sleep(120)
    return Text(text=value.text + "!")


def double(value: Number) -> Number:
    return Number(value=value.value * 2)


AGENT = AgentDefinition(
    "transform",
    "1",
    "Transform",
    "Transform text",
    "Return transformed text",
    Text,
    Text,
)


def register(registry: Registry) -> None:
    first = ToolDefinition("uppercase", "1", "Uppercase", Text, Text, uppercase)
    second = ToolDefinition("boundary", "1", "Boundary", Text, Text, boundary)
    effects: list[tuple[str, Literal["pure", "idempotent", "non_idempotent"]]] = [
        ("checkpoint", "pure"),
        ("unsafe", "non_idempotent"),
    ]
    for workflow_id, effect in effects:
        tool = ToolDefinition(
            "unsafe_boundary" if effect == "non_idempotent" else second.id,
            second.version,
            second.name,
            Text,
            Text,
            boundary,
            effect=effect,
        )
        registry.register(
            WorkflowDefinition(
                workflow_id,
                "1",
                workflow_id,
                Text,
                Text,
                (
                    NodeDefinition("upper", "tool", {"text": "input.text"}, tool=first),
                    NodeDefinition(
                        "boundary", "tool", {"text": "nodes.upper.text"}, tool=tool
                    ),
                ),
                {"text": "nodes.boundary.text"},
            )
        )
    numeric = ToolDefinition("double", "1", "Double", Number, Number, double)
    registry.register(
        WorkflowDefinition(
            "arithmetic",
            "1",
            "Arithmetic",
            Number,
            Number,
            (NodeDefinition("double", "tool", {"value": "input.value"}, tool=numeric),),
            {"value": "nodes.double.value"},
        )
    )
    registry.register(
        WorkflowDefinition(
            "approval",
            "1",
            "Approval",
            Text,
            Text,
            (
                NodeDefinition("upper", "tool", {"text": "input.text"}, tool=first),
                NodeDefinition("gate", "approval", {"text": "nodes.upper.text"}),
                NodeDefinition(
                    "boundary", "tool", {"text": "nodes.upper.text"}, tool=second
                ),
            ),
            {"text": "nodes.boundary.text"},
        )
    )
    registry.register(
        WorkflowDefinition(
            "agent",
            "1",
            "Agent",
            Text,
            Text,
            (
                NodeDefinition("agent", "agent", {"text": "input.text"}, agent=AGENT),
                NodeDefinition(
                    "later", "tool", {"text": "nodes.agent.text"}, tool=first
                ),
            ),
            {"text": "nodes.later.text"},
            max_calls=2,
        )
    )

    registry.register(
        WorkflowDefinition(
            "two_gates",
            "1",
            "Two gates",
            Text,
            Text,
            (
                NodeDefinition("upper", "tool", {"text": "input.text"}, tool=first),
                NodeDefinition("gate_one", "approval", {"text": "nodes.upper.text"}),
                NodeDefinition(
                    "boundary", "tool", {"text": "nodes.upper.text"}, tool=second
                ),
                NodeDefinition("gate_two", "approval", {"text": "nodes.boundary.text"}),
            ),
            {"text": "nodes.boundary.text"},
        )
    )
