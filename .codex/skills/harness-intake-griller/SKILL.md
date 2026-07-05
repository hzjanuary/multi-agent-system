---
name: harness-intake-griller
description: Project-scoped intake workflow for Enterprise Multi-Agent OS. Use when a request needs discussion, feature intake, docs, story shaping, Harness durable records, or a stop-before-implementation gate before backend, frontend, or Symphony execution.
---

# Harness Intake Griller

## Purpose

Use this skill to turn a request into a bounded Harness work item before
implementation. It keeps `SPEC.md`, `.ai/project`, Harness docs, stories,
validation proof, and durable CLI records aligned.

## When To Use

Use this skill when the request involves:

- Discussion or clarification before implementation.
- Feature intake, story shaping, or task slicing.
- Creating or updating product docs, story packets, decisions, or validation
  expectations.
- Preparing work for Harness Symphony or another agent execution flow.
- Any implementation request where the current SPEC and project contracts must
  be confirmed first.

## Required Reading Order

Read in this order before implementation:

1. `SPEC.md`
2. `AGENTS.md`
3. `README.md`
4. `docs/HARNESS.md`
5. `docs/FEATURE_INTAKE.md`
6. `docs/ARCHITECTURE.md`
7. `docs/CONTEXT_RULES.md`
8. `docs/TOOL_REGISTRY.md`
9. `scripts/bin/harness-cli query matrix` on macOS/Linux, or
   `.\scripts\bin\harness-cli.exe query matrix` on Windows
10. Relevant `.ai/project/*.md` files, including at minimum:
    - `.ai/project/PROJECT_CONTRACT.md`
    - `.ai/project/ARCHITECTURE.md`
    - `.ai/project/TECH_STACK.md`
    - `.ai/project/CODING_STANDARD.md`
    - `.ai/project/FOLDER_STRUCTURE.md`
    - `.ai/project/STATE_CONTRACT.md`
    - `.ai/project/AGENT_CONTRACT.md`
    - `.ai/project/API_CONTRACT.md`
    - `.ai/project/DATABASE_CONTRACT.md`
11. Relevant `.ai/specs/**` files for the selected task.
12. Relevant `docs/product/*`, `docs/stories/*`, and `docs/decisions/*` files
    when product behavior, architecture, validation, or risk changes.

## Intake Checklist

Before changing files:

- Classify the input type using `docs/FEATURE_INTAKE.md`.
- Choose the lane: `tiny`, `normal`, or `high-risk`.
- Identify the selected SPEC, affected product docs, story packet, and
  validation expectations.
- Confirm the requested work does not implement future phases early.
- Confirm no approved architecture rule in `.ai/project/PROJECT_CONTRACT.md`
  or `.ai/project/ARCHITECTURE.md` is being changed.
- If an external tool might be useful, query the Harness registry first:
  `scripts/bin/harness-cli query tools --capability <name> --status present`.
- If the Harness CLI is available, record the intake:
  `scripts/bin/harness-cli intake --type <type> --summary "<summary>" --lane <lane>`.
- If the Harness CLI is unavailable, continue with a documented note in the
  final response and do not invent durable records.

## Output Format

After intake, summarize:

```text
Lane: <tiny|normal|high-risk>
Type: <new spec|spec slice|change request|new initiative|maintenance request|harness improvement>
Reason: <risk flags and why the lane was chosen>
SPEC: <selected SPEC or none>
Docs: <product, story, decision, or Harness docs affected>
Validation: <proof expected or why no executable proof exists>
Durable record: <intake/story/decision/trace id or unavailable>
Stop gate: <ready for implementation|needs review|blocked>
```

## Stop Condition Before Implementation

Stop and ask for review before implementation when:

- The lane is high-risk and the direction is ambiguous.
- The task would change approved architecture, source-of-truth hierarchy,
  risk rules, validation requirements, auth, authorization, data ownership,
  API contracts, or external provider behavior.
- The request would create backend or frontend app code before the selected
  SPEC allows it.
- Required product contracts or selected SPEC files are missing.
- The user explicitly asked to stop after intake, story shaping, or docs.

If none of these stop conditions apply, proceed only with the selected task and
record a Harness trace before the final response when the CLI is available.
