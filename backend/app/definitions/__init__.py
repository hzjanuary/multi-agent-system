"""Trusted, code-first definitions for sequential typed workflows.

Mappings are field -> dotted input/prior-node reference, never expressions.
Installed extensions execute with worker privileges and are not a sandbox.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
_FIELD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DefinitionError(ValueError):
    """An installed definition is invalid or unavailable."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def artifact_fingerprint(module_name: str) -> str:
    """Hash installed package source/resources without host paths or caches."""
    module = importlib.import_module(module_name)
    filename = getattr(module, "__file__", None)
    if not filename:
        raise DefinitionError("extension must expose a reproducible source artifact")
    source = Path(filename).resolve()
    package = importlib.import_module(module_name.split(".", 1)[0])
    locations = getattr(package, "__path__", None)
    if locations is None:
        # A standalone top-level module owns only its source file. Package
        # extensions with resources so the complete artifact can be identified.
        root = source.parent
        files = [source]
    else:
        roots = [Path(path).resolve() for path in locations]
        if len(roots) != 1 or not source.is_relative_to(roots[0]):
            raise DefinitionError("extension requires one installed package artifact")
        root = roots[0]
        excluded = {
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".git",
            ".venv",
        }
        files = []
        for candidate in root.rglob("*"):
            relative = candidate.relative_to(root)
            if any(part in excluded for part in relative.parts):
                continue
            if candidate.suffix in {".pyc", ".pyo"} or not candidate.is_file():
                continue
            if not candidate.resolve().is_relative_to(root):
                raise DefinitionError("extension resource escapes installed package")
            files.append(candidate)
        files.sort()
    return fingerprint(
        {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        }
    )


def _valid_schema(model: object) -> bool:
    return isinstance(model, type) and issubclass(model, BaseModel)


def _schema(model: type[BaseModel]) -> dict[str, Any]:
    return {
        "identity": f"{model.__module__}.{model.__qualname__}",
        "schema": model.model_json_schema(),
    }


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    version: str
    name: str
    responsibility: str
    instructions: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    profile: str = "default"
    timeout_seconds: int = 60
    max_tokens: int = 1024

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "responsibility": self.responsibility,
            "instructions": self.instructions,
            "input": _schema(self.input_schema),
            "output": _schema(self.output_schema),
            "profile": self.profile,
            "timeout_seconds": self.timeout_seconds,
            "max_tokens": self.max_tokens,
        }


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    version: str
    name: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    handler: Callable[..., Any]
    effect: Literal["pure", "idempotent", "non_idempotent"] = "pure"
    requires_approval: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "input": _schema(self.input_schema),
            "output": _schema(self.output_schema),
            "effect": self.effect,
            "requires_approval": self.requires_approval,
            "handler": f"{self.handler.__module__}.{self.handler.__qualname__}",
            "implementation": artifact_fingerprint(self.handler.__module__),
        }


@dataclass(frozen=True)
class NodeDefinition:
    id: str
    kind: Literal["agent", "tool", "approval"]
    input_mapping: dict[str, str]
    agent: AgentDefinition | None = None
    tool: ToolDefinition | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "input_mapping": self.input_mapping,
            "agent": self.agent.snapshot() if self.agent else None,
            "tool": self.tool.snapshot() if self.tool else None,
        }


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    version: str
    name: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    nodes: tuple[NodeDefinition, ...]
    output_mapping: dict[str, str]
    max_calls: int = 16
    max_nodes: int = 32
    max_input_bytes: int = 65536
    max_node_output_bytes: int = 65536
    max_total_bytes: int = 1048576
    extension_identity: dict[str, str] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "input": _schema(self.input_schema),
            "output": _schema(self.output_schema),
            "nodes": [node.snapshot() for node in self.nodes],
            "output_mapping": self.output_mapping,
            "limits": {
                "max_calls": self.max_calls,
                "max_nodes": self.max_nodes,
                "max_input_bytes": self.max_input_bytes,
                "max_node_output_bytes": self.max_node_output_bytes,
                "max_total_bytes": self.max_total_bytes,
            },
            "extension": self.extension_identity,
        }

    @property
    def definition_hash(self) -> str:
        return fingerprint(self.snapshot())


def _resolve(
    reference: str, input_value: dict[str, Any], outputs: dict[str, Any]
) -> Any:
    parts = reference.split(".")
    if parts[0] == "input":
        value: Any = input_value
        parts = parts[1:]
    elif len(parts) >= 2 and parts[0] == "nodes" and parts[1] in outputs:
        value = outputs[parts[1]]
        parts = parts[2:]
    else:
        raise DefinitionError("mapping references an unavailable input or node")
    try:
        for part in parts:
            value = value[part]
    except (KeyError, TypeError) as exc:
        raise DefinitionError("mapping references an unavailable field") from exc
    return value


def resolve_mapping(
    mapping: Mapping[str, str], input_value: dict[str, Any], outputs: dict[str, Any]
) -> dict[str, Any]:
    return {key: _resolve(ref, input_value, outputs) for key, ref in mapping.items()}


def _field_schema(model: type[BaseModel], parts: list[str]) -> dict[str, Any]:
    root = model.model_json_schema()
    current = root
    for part in parts:
        while "$ref" in current:
            reference = current["$ref"]
            if not reference.startswith("#/$defs/"):
                raise DefinitionError("external schema references are unsupported")
            current = root.get("$defs", {}).get(reference.rsplit("/", 1)[-1], {})
        if part not in current.get("properties", {}):
            raise DefinitionError(
                "mapping references a missing or untyped source field"
            )
        current = current["properties"][part]
    while "$ref" in current:
        current = root.get("$defs", {}).get(current["$ref"].rsplit("/", 1)[-1], {})
    return current


def _check_mapping(
    mapping: dict[str, str],
    available: dict[str, type[BaseModel] | None],
    target: type[BaseModel] | None = None,
) -> None:
    if not isinstance(mapping, dict) or not mapping:
        raise DefinitionError("a nonempty explicit mapping is required")
    if target:
        missing = {
            name for name, info in target.model_fields.items() if info.is_required()
        } - mapping.keys()
        if missing or (set(mapping) - target.model_fields.keys()):
            raise DefinitionError("mapping must satisfy the target schema fields")
    for key, ref in mapping.items():
        if not isinstance(key, str) or not isinstance(ref, str):
            raise DefinitionError("mapping keys and references must be strings")
        parts = ref.split(".")
        base = parts[0] if parts[0] == "input" else ".".join(parts[:2])
        if base not in available:
            raise DefinitionError("mapping must reference input or a prior node")
        remaining = parts[1:] if base == "input" else parts[2:]
        model = available[base]
        if remaining and model is None:
            raise DefinitionError(
                "approval content cannot be referenced as typed output"
            )
        source_schema = _field_schema(model, remaining) if model else {}
        if target:
            destination = _field_schema(target, [key])
            source_type, target_type = source_schema.get("type"), destination.get(
                "type"
            )
            if (
                source_type
                and target_type
                and source_type != target_type
                and not (source_type == "integer" and target_type == "number")
            ):
                raise DefinitionError(
                    "mapping source and target types are incompatible"
                )
        if any(not _FIELD.fullmatch(part) or part.startswith("__") for part in parts):
            raise DefinitionError("mapping references must use plain field identifiers")


def validate_workflow(workflow: WorkflowDefinition) -> None:
    if (
        not isinstance(workflow.input_schema, type)
        or not issubclass(workflow.input_schema, BaseModel)
        or not isinstance(workflow.output_schema, type)
        or not issubclass(workflow.output_schema, BaseModel)
    ):
        raise DefinitionError("workflow schemas must be Pydantic models")
    if not _IDENTIFIER.fullmatch(workflow.id) or not workflow.version.strip():
        raise DefinitionError("workflow identity is invalid")
    if not 1 <= len(workflow.nodes) <= workflow.max_nodes <= 32:
        raise DefinitionError("workflow node limit is invalid")
    if not 1 <= workflow.max_calls <= 256:
        raise DefinitionError("workflow call limit is invalid")
    if not (
        1 <= workflow.max_input_bytes <= 65536
        and 1 <= workflow.max_node_output_bytes <= 65536
        and 1 <= workflow.max_total_bytes <= 1048576
    ):
        raise DefinitionError("workflow byte limits are invalid")
    available: dict[str, type[BaseModel] | None] = {"input": workflow.input_schema}
    seen: set[str] = set()
    approved_mapping: dict[str, str] | None = None
    for node in workflow.nodes:
        if not _IDENTIFIER.fullmatch(node.id) or node.id in seen:
            raise DefinitionError("node IDs must be unique identifiers")
        seen.add(node.id)
        target = None
        output = None
        if node.kind == "agent" and node.agent and not node.tool:
            agent = node.agent
            if (
                not _IDENTIFIER.fullmatch(agent.id)
                or not agent.version
                or not agent.instructions
                or not agent.responsibility
                or agent.profile != "default"
                or not 1 <= agent.timeout_seconds <= 300
                or not 1 <= agent.max_tokens <= 32768
            ):
                raise DefinitionError(
                    "agent identity, profile, instructions or limits invalid"
                )
            if not _valid_schema(agent.input_schema) or not _valid_schema(
                agent.output_schema
            ):
                raise DefinitionError("agent schemas must be Pydantic models")
            target, output = agent.input_schema, agent.output_schema
        elif node.kind == "tool" and node.tool and not node.agent:
            tool = node.tool
            if (
                not _IDENTIFIER.fullmatch(tool.id)
                or not tool.version
                or tool.effect not in {"pure", "idempotent", "non_idempotent"}
            ):
                raise DefinitionError("tool identity or effect is invalid")
            if tool.requires_approval and node.input_mapping != approved_mapping:
                raise DefinitionError(
                    "approval-required tool must consume "
                    "the exact approved content mapping"
                )
            if (
                not _valid_schema(tool.input_schema)
                or not _valid_schema(tool.output_schema)
                or not callable(tool.handler)
            ):
                raise DefinitionError(
                    "tool requires Pydantic schemas and a callable handler"
                )
            target, output = tool.input_schema, tool.output_schema
        elif node.kind == "approval" and not node.agent and not node.tool:
            approved_mapping = node.input_mapping
        else:
            raise DefinitionError("unsupported node kind or mismatched implementation")
        _check_mapping(node.input_mapping, available, target)
        available[f"nodes.{node.id}"] = output
    _check_mapping(workflow.output_mapping, available, workflow.output_schema)


class Registry:
    def __init__(self) -> None:
        self.workflows: dict[tuple[str, str], WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition) -> None:
        validate_workflow(workflow)
        key = (workflow.id, workflow.version)
        if key in self.workflows:
            raise DefinitionError("duplicate workflow identity")
        existing_agents = {
            (n.agent.id, n.agent.version): n.agent.snapshot()
            for w in self.workflows.values()
            for n in w.nodes
            if n.agent
        }
        existing_tools = {
            (n.tool.id, n.tool.version): n.tool.snapshot()
            for w in self.workflows.values()
            for n in w.nodes
            if n.tool
        }
        for node in workflow.nodes:
            if node.agent:
                identity = (node.agent.id, node.agent.version)
                if (
                    identity in existing_agents
                    and existing_agents[identity] != node.agent.snapshot()
                ):
                    raise DefinitionError("conflicting agent identity")
                existing_agents[identity] = node.agent.snapshot()
            if node.tool:
                identity = (node.tool.id, node.tool.version)
                if (
                    identity in existing_tools
                    and existing_tools[identity] != node.tool.snapshot()
                ):
                    raise DefinitionError("conflicting tool identity")
                existing_tools[identity] = node.tool.snapshot()
        self.workflows[key] = workflow

    def get(self, workflow_id: str, version: str | None = None) -> WorkflowDefinition:
        matches = [
            w
            for (wid, ver), w in self.workflows.items()
            if wid == workflow_id and (version is None or version == ver)
        ]
        if len(matches) != 1:
            raise DefinitionError("workflow version missing, ambiguous or unavailable")
        return matches[0]

    @property
    def agents(self) -> list[AgentDefinition]:
        unique: dict[tuple[str, str], AgentDefinition] = {}
        for workflow in self.workflows.values():
            for node in workflow.nodes:
                if node.agent:
                    key = (node.agent.id, node.agent.version)
                    if (
                        key in unique
                        and unique[key].snapshot() != node.agent.snapshot()
                    ):
                        raise DefinitionError("conflicting agent identity")
                    unique[key] = node.agent
        return list(unique.values())


def load_registry(modules: str | list[str] | tuple[str, ...] = ()) -> Registry:
    from dataclasses import replace

    registry = Registry()
    names = (
        [s.strip() for s in modules.split(",") if s.strip()]
        if isinstance(modules, str)
        else list(modules)
    )
    if len(names) != len(set(names)):
        raise DefinitionError("duplicate extension module")
    for name in names:
        if not re.fullmatch(r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*", name):
            raise DefinitionError("invalid extension module name")
        module = importlib.import_module(name)
        version = getattr(module, "EXTENSION_VERSION", None)
        register = getattr(module, "register", None)
        if not isinstance(version, str) or not version or not callable(register):
            raise DefinitionError(
                "extension requires EXTENSION_VERSION and register(registry)"
            )
        identity = {
            "module": name,
            "version": version,
            "artifact": artifact_fingerprint(name),
        }
        extension = Registry()
        register(extension)
        for workflow in extension.workflows.values():
            registry.register(replace(workflow, extension_identity=identity))
    _ = registry.agents  # validate reused agent identities before execution
    return registry
