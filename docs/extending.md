# Trusted workflow extensions

Extensions are installed Python code running with the worker's privileges. This
release has no untrusted-code sandbox, arbitrary module API, remote installer,
autonomous planner or arbitrary DAG execution. The registry supports a bounded
ordered sequence of agent, deterministic tool and approval nodes.

The default registry is empty. Enable the shipped real example explicitly in
`.maos/.env`, using the same value for API and worker:

```dotenv
MAOS_EXTENSION_MODULES=maos_examples.text_review
```

That package lives under `backend/maos_examples/` and ships in the release image.
It takes user-supplied text, invokes distinct analyst and reviewer agents, pauses
for a human decision, and runs a pure assembly tool only after approval and
explicit resume. Enabling it creates no database records and starts no runs.

For another extension, put a trusted package under the backend build context,
include it in your custom application image, and enable its module name through
`MAOS_EXTENSION_MODULES`. Each module exports `EXTENSION_VERSION` and
`register(registry)`. Installed code and configuration must match in API and
worker. Do not edit the runtime graph or core schemas.

A complete small deterministic workflow illustrates the interface:

```python
# my_extensions/arithmetic.py (include this package in your custom image)
from pydantic import BaseModel, ConfigDict
from app.definitions import NodeDefinition, Registry, ToolDefinition, WorkflowDefinition

EXTENSION_VERSION = "1.0.0"

class Numbers(BaseModel):
    model_config = ConfigDict(extra="forbid")
    left: int
    right: int

class Total(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total: int

def add(value: Numbers) -> Total:
    return Total(total=value.left + value.right)

def register(registry: Registry) -> None:
    tool = ToolDefinition(
        id="integer_addition", version="1.0.0", name="Add integers",
        input_schema=Numbers, output_schema=Total, handler=add, effect="pure",
    )
    registry.register(WorkflowDefinition(
        id="arithmetic", version="1.0.0", name="Integer addition",
        input_schema=Numbers, output_schema=Total,
        nodes=(NodeDefinition(
            id="add", kind="tool", tool=tool,
            input_mapping={"left": "input.left", "right": "input.right"},
        ),),
        output_mapping={"total": "nodes.add.total"},
    ))
```

This is extension authoring source, not a claim that `my_extensions` is bundled.
The shipped executable authoring example is
[`text_review.py`](../backend/maos_examples/text_review.py). Test extensions use
unrelated schemas to exercise the same engine.

An `AgentDefinition` supplies `id`, `version`, `name`, `responsibility`,
`instructions`, Pydantic `input_schema`/`output_schema`, `profile="default"`,
`timeout_seconds` (1–300) and `max_tokens` (1–32768). The installed instructions
and output JSON schema are sent as a system message; the validated mapped input
is a user message. The runtime validates the returned JSON object before storing
success. Both agents can use the same operator-selected model. Do not embed
credentials in instructions, schemas or definition defaults.

A `ToolDefinition` supplies `id`, `version`, `name`, input/output schemas, a
handler and `effect` (`pure`, `idempotent` or `non_idempotent`). Its handler accepts
a validated input-model instance and returns an output-model instance or mapping;
async handlers are supported. Set `requires_approval=True` when a human gate is
required. Such a tool must consume the exact mapping of the preceding approval
node so its input is the approved content. Do not install shell, arbitrary
HTTP-fetch, filesystem-write or messaging tools as general-purpose capabilities.
An interrupted non-idempotent attempt cannot resume: reconcile externally,
cancel, and create a new run if appropriate.

Mappings are dictionaries from destination field to a plain dotted reference:
`input.text`, `nodes.analyze.summary`, or `nodes.analyze` for its whole validated
object. They are not Python expressions; there is no `eval`, indexing, import or
function invocation. Each source must be run input or an earlier node. Required
target fields, source fields and incompatible primitive types are checked at
registration; actual mapped values and final output are validated at execution.
Approval nodes use their mapping as the exact persisted content for the decision.

Workflow IDs and node IDs are lowercase identifiers. Node IDs are unique in a
workflow. A workflow has a stable version, typed input/output, ordered nodes,
final `output_mapping` and bounded `max_calls`, `max_nodes`, `max_input_bytes`,
`max_node_output_bytes`, `max_total_bytes`. API and worker reject malformed
registrations before executing runs. If more than one version of a workflow is
installed, discovery by ID must include an exact version.

Each run stores a serializable snapshot and hash covering instructions, schema
identities, mappings, kinds, limits, handler identity and source fingerprint.
Extension fingerprints hash the installed top-level package's source/resources
with relative filenames; caches and bytecode are excluded. Standalone top-level
modules identify only their source file: package resource-dependent extensions
so their complete artifact is included. Process addresses and function `repr`
are not identities. Keep all
extension implementation dependencies in the versioned artifact/package and use
an immutable release image. Change the version when behavior changes. Missing or
changed artifacts block existing run execution/resume; executable Python is
never serialized into PostgreSQL.

To inspect definitions without invoking a provider:

```bash
docker compose --env-file .maos/.env --profile cli run --rm cli workflow list
docker compose --env-file .maos/.env --profile cli run --rm cli workflow show text_review --version 1.0.0
docker compose --env-file .maos/.env --profile cli run --rm cli workflow validate
```

Follow the [API/CLI guide](api.md) for authenticated create, start, approval,
explicit resume, cancellation and event replay.
