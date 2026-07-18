# Technical Narrative

## Project Summary

Enterprise Multi-Agent OS is an academic implementation of enterprise
procurement workflow automation. It models procurement as a controlled business
process rather than as an open-ended chatbot. A user starts a workflow from an
RFQ-like request, the backend advances the workflow through specialized stages,
the system records durable state and events, and a Manager or Admin must
approve the result before post-approval email preparation can occur.

The project demonstrates how AI-adjacent automation can be made safer by
combining deterministic services, role-based access control, human approval,
bounded retrieval evidence, and observable workflow state.

## Business Problem

Procurement quotation work requires several decisions before a response can be
sent to a customer. A team must understand the request, identify relevant
customer or contract context, calculate prices accurately, check policy and
compliance rules, validate the package, obtain approval, and prepare a
customer-facing response. In manual processes, these steps are often scattered
across email threads, spreadsheets, and informal approvals.

That fragmentation creates three practical risks:

- inconsistent or missing evidence for why a quotation is acceptable
- arithmetic and policy errors that are difficult to audit later
- customer-facing output being prepared or sent before a responsible reviewer
  approves it

Enterprise Multi-Agent OS addresses the problem by turning the procurement flow
into a state-driven workflow with explicit ownership, typed API contracts,
persisted events, and human approval gates.

## Why A Multi-Agent OS Approach Fits

The procurement process is naturally multi-stage. Each stage has a different
responsibility: planning, retrieval, calculation, compliance review,
validation, approval, and email preparation. A multi-agent design is useful
because it separates those responsibilities instead of forcing one general
assistant to reason about the entire process at once.

The project uses the phrase "multi-agent OS" to describe a controlled operating
surface for agents and tools. Agents do not own arbitrary state. They operate
inside workflow boundaries, produce structured outputs, and rely on services to
persist state, events, and audit evidence. This makes the system easier to
test, inspect, and explain.

## Why LangGraph

LangGraph is used for controlled multi-stage orchestration. It provides an
explicit graph model for the workflow stages and keeps the runtime compatible
with interruption and continuation semantics. This fits the procurement use
case because the workflow must stop at `WAITING_APPROVAL`, persist its state,
and later continue only through an explicit resume action.

The implemented runtime preserves deterministic behavior by default. The graph
can run without real LLM keys, and feature flags decide whether LLM and RAG
grounding paths participate.

## Why FastAPI

FastAPI provides a typed HTTP boundary for workflow, approval, knowledge,
authentication, health, readiness, and observability endpoints. It aligns with
the project's Pydantic contracts and async service architecture. The API layer
is intentionally thin: it validates request/response DTOs, enforces
authentication and RBAC, delegates business behavior to services, commits only
after successful mutations, and maps domain errors to safe HTTP responses.

## Why Next.js

Next.js is used for the dashboard because the project needs an interactive,
browser-based operator experience: login, workflow list, workflow detail, run
controls, approval actions, history, event timeline, evidence panels, and
knowledge search/catalog views. TypeScript DTOs mirror backend response shapes
so frontend behavior can remain explicit and testable.

## Why Postgres, Redis, Qdrant, And MinIO

Postgres stores durable business data such as users, roles, workflow state,
workflow events, and audit logs. It is the source of truth for workflow status
and persisted evidence.

Redis supports the event-streaming infrastructure used by the workflow
timeline. It enables live updates without replacing persisted event history.

Qdrant stores vectorized knowledge chunks for retrieval. It supports the RAG
knowledge base while keeping vector concerns outside the workflow database.

MinIO stores original demo knowledge/source objects where appropriate. It keeps
document objects separate from workflow state, which should contain bounded
citations and summaries rather than full documents.

## Deterministic No-Key Evaluation

A central academic requirement is reproducibility. The project therefore
supports a no-key evaluation path:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

In this mode, the workflow can run deterministically, stop at
`WAITING_APPROVAL`, accept approval, resume, and finish at `COMPLETED` without
external provider keys. Optional RAG validation can also remain no-key by using
fake embeddings and explicitly ingested demo knowledge.

## Optional Real LLM Providers

Real LLM providers are optional and feature-flagged through the provider
abstraction. The report should describe this as an extensibility boundary, not
as final production provider evaluation unless a later evidence task captures
that proof. The default evaluation path must not depend on paid providers or
live external calls.

## Human Approval And Resume

Human approval protects high-stakes business decisions. The runtime does not
produce post-approval email output during `/run`. It stops at
`WAITING_APPROVAL`. A Manager or Admin can approve, reject, or request changes.
Approval history is persisted, and only an approved workflow with a final
approval decision can continue through `/resume`.

This design makes the control point explicit: approval is not a frontend-only
state and not an automatic side effect. The backend approval and resume
services enforce lifecycle and RBAC rules.

## RAG Evidence Grounding

The RAG knowledge base grounds compliance, finance/validation, and approval
stages with bounded citations. Demo documents are chunked deterministically,
embedded with a fake provider by default, stored or indexed through MinIO and
Qdrant provider abstractions, and retrieved through a provider-independent
service.

Workflow state and frontend views show safe citation metadata: source title,
source type, citation label, section/page, bounded excerpt, relevance score,
and document id. They do not expose raw embeddings, raw vector payloads, raw
prompts, provider payloads, or full documents.

## Event Streaming And Transparency

Workflow events are persisted and streamed to the frontend timeline through the
existing event pipeline. This gives users a concrete view of runtime progress,
approval decisions, resume continuation, and RAG grounding events. The event
model supports transparency while preserving the safety boundary against hidden
reasoning and sensitive payload exposure.

## Deployment And Observability

The project includes a Docker Compose production-demo stack for backend,
frontend, Postgres, Redis, Qdrant, and MinIO. It also includes environment
templates, CI/local quality gates, smoke scripts, health/liveness/readiness
endpoints, structured logging, request ID propagation, and bounded in-process
metrics.

This operational layer makes the graduation demo credible outside a single
developer shell while avoiding premature cloud automation, secret vaults,
Kubernetes, or production backup automation.
