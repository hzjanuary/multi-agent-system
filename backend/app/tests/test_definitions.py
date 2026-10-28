"""Registry identities, mapping validation and opt-in extension contracts."""

from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.definitions import (
    DefinitionError,
    NodeDefinition,
    Registry,
    WorkflowDefinition,
    load_registry,
    resolve_mapping,
    validate_workflow,
)


class Input(BaseModel):
    text: str


class Output(BaseModel):
    approved_text: str


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="unrelated",
        version="1",
        name="Unrelated schema",
        input_schema=Input,
        output_schema=Output,
        nodes=(
            NodeDefinition(
                id="gate", kind="approval", input_mapping={"text": "input.text"}
            ),
        ),
        output_mapping={"approved_text": "input.text"},
    )


def test_default_registry_is_empty_and_example_is_explicit() -> None:
    assert load_registry().workflows == {}
    registry = load_registry("maos_examples.text_review")
    definition = registry.get("text_review", "1.0.0")
    assert [n.kind for n in definition.nodes] == ["agent", "agent", "approval", "tool"]
    assert len(registry.agents) == 2
    assert definition.extension_identity["artifact"]
    assert (
        definition.snapshot()["nodes"][1]["input_mapping"]["analysis"]
        == "nodes.analyze"
    )


def test_identity_is_reproducible_and_tracks_instructions_mapping_and_limits() -> None:
    first = load_registry("maos_examples.text_review").get("text_review")
    second = load_registry("maos_examples.text_review").get("text_review")
    assert first.definition_hash == second.definition_hash
    agent = first.nodes[0].agent
    assert agent is not None
    changed = replace(
        first,
        nodes=(
            replace(first.nodes[0], agent=replace(agent, instructions="changed")),
            *first.nodes[1:],
        ),
    )
    assert changed.definition_hash != first.definition_hash
    assert replace(first, max_calls=15).definition_hash != first.definition_hash


def test_two_unrelated_typed_definitions_register_without_core_modification() -> None:
    registry = load_registry("maos_examples.text_review")
    registry.register(workflow())
    assert set(w.id for w in registry.workflows.values()) == {
        "text_review",
        "unrelated",
    }
    value = resolve_mapping(workflow().output_mapping, {"text": "real input"}, {})
    assert Output.model_validate(value).approved_text == "real input"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda w: replace(w, nodes=w.nodes * 2),
        lambda w: replace(w, nodes=(replace(w.nodes[0], kind="shell"),)),
        lambda w: replace(w, output_mapping={"approved_text": "nodes.missing.result"}),
        lambda w: replace(w, output_mapping={"approved_text": "input.no_such_field"}),
        lambda w: replace(w, output_mapping={"approved_text": "input.__class__()"}),
        lambda w: replace(w, output_mapping={"wrong": "input.text"}),
        lambda w: replace(w, max_calls=0),
    ],
)
def test_malformed_definitions_are_rejected(mutation: object) -> None:
    with pytest.raises(DefinitionError):
        validate_workflow(mutation(workflow()))  # type: ignore[operator]


def test_duplicate_workflow_and_extension_identities_are_rejected() -> None:
    registry = Registry()
    registry.register(workflow())
    with pytest.raises(DefinitionError):
        registry.register(workflow())
    with pytest.raises(DefinitionError):
        load_registry("maos_examples.text_review,maos_examples.text_review")


def test_top_level_package_fingerprint_includes_resources_and_ignores_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.definitions import artifact_fingerprint

    package = tmp_path / "installed_extension"
    package.mkdir()
    (package / "__init__.py").write_text('EXTENSION_VERSION = "1"\n')
    (package / "handlers.py").write_text("def handler(): return 1\n")
    resource = package / "instructions.txt"
    resource.write_text("first instructions")
    monkeypatch.syspath_prepend(str(tmp_path))
    original = artifact_fingerprint("installed_extension")
    assert artifact_fingerprint("installed_extension.handlers") == original
    cache = package / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "ignored.pyc").write_bytes(b"bytecode cache")
    assert artifact_fingerprint("installed_extension") == original
    resource.write_text("changed instructions")
    assert artifact_fingerprint("installed_extension") != original


def test_conflicting_component_identity_within_one_workflow_is_rejected() -> None:
    from app.definitions import AgentDefinition

    first = AgentDefinition(
        id="shared",
        version="1",
        name="Shared",
        responsibility="Single task",
        instructions="First behavior",
        input_schema=Input,
        output_schema=Input,
    )
    definition = WorkflowDefinition(
        id="conflict",
        version="1",
        name="Conflict rejection",
        input_schema=Input,
        output_schema=Input,
        nodes=(
            NodeDefinition(
                id="first",
                kind="agent",
                agent=first,
                input_mapping={"text": "input.text"},
            ),
            NodeDefinition(
                id="second",
                kind="agent",
                agent=replace(first, instructions="Different behavior"),
                input_mapping={"text": "nodes.first.text"},
            ),
        ),
        output_mapping={"text": "nodes.second.text"},
    )
    with pytest.raises(DefinitionError, match="conflicting agent identity"):
        Registry().register(definition)

    example = load_registry("maos_examples.text_review").get("text_review")
    tool_node = example.nodes[-1]
    assert tool_node.tool is not None
    duplicate = replace(
        tool_node,
        id="assemble_again",
        tool=replace(tool_node.tool, effect="idempotent"),
    )
    with pytest.raises(DefinitionError, match="conflicting tool identity"):
        Registry().register(replace(example, nodes=(*example.nodes, duplicate)))
