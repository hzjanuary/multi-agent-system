# Architecture And Design Narrative

This document provides written architecture material for the graduation report.
It intentionally contains no diagrams; diagram source and screenshot planning
belong to TASK 015.4.

## Architectural Style

Enterprise Multi-Agent OS follows a layered, service-oriented backend design:

```text
API routes -> services/runtime adapters -> repositories/providers -> external systems
```

The API layer owns HTTP contracts, authentication dependencies, RBAC
dependencies, and safe error mapping. Service layers own business rules such as
workflow lifecycle transitions, approval decisions, retrieval normalization,
and runtime orchestration. Repository and provider layers own persistence or
external infrastructure mechanics.

This separation prevents route handlers, runtime nodes, or frontend code from
becoming the source of truth for workflow status, authorization, or persistence
behavior.

## Backend Layers

The backend is built with FastAPI and Pydantic v2. Request and response models
are typed, bounded, and designed to avoid leaking internal provider payloads.
The route modules cover authentication, workflows, knowledge, health/readiness,
and observability. Each route delegates substantive behavior to a service or
provider dependency.

Core service responsibilities:

- authentication service validates credentials and issues JWT tokens
- workflow service owns persisted workflow state and lifecycle transitions
- workflow event service appends and reads event history
- runtime service coordinates LangGraph execution and persistence
- approval service owns approval history, state transitions, events, and audit
  evidence
- knowledge ingestion and retrieval services own document chunking, embedding,
  vector upsert/search, and citation mapping
- readiness and observability components expose operational status without
  mutating business data

## Persistence Boundaries

Postgres is the durable system of record for users, roles, workflows, workflow
events, and audit logs. Workflow state is stored as structured payload data,
but large documents, raw provider payloads, raw prompts, and embeddings are not
stored in workflow state.

Redis supports event delivery. It is used as infrastructure for live workflow
updates, while persisted events remain available through REST APIs and database
records.

Qdrant stores vectorized knowledge chunks and safe chunk payload metadata. The
retrieval service converts Qdrant responses into typed citation-aware DTOs so
the API and frontend do not expose raw vector provider responses.

MinIO stores original demo knowledge/source objects through the object storage
provider boundary. Object keys are deterministic for demo ingestion, and
readiness checks do not mutate or auto-create storage.

## Workflow Runtime Boundaries

The runtime represents procurement work as ordered stages:

- planner
- retrieval
- quotation
- compliance
- validation
- approval wait
- email preparation after approval

LangGraph provides the graph structure, but workflow state and events remain
persisted through the existing services. The runtime does not mutate database
models directly. It advances lifecycle state through the workflow service and
appends events through the workflow event service.

The `/run` endpoint executes the pre-approval path and stops at
`WAITING_APPROVAL`. This makes the human approval gate a required control point.
The post-approval continuation is exposed separately through `/resume`.

## Agent Stage Boundaries

Each workflow stage has one responsibility:

- planner classifies intent and domain
- retrieval prepares business context
- quotation performs deterministic pricing calculation
- compliance checks policy and contract alignment
- validation verifies schema and business-rule consistency
- approval wait packages review material for a human decision
- email preparation creates a customer-facing draft after approval

This structure supports explainability. A failed or suspicious stage can be
identified by status, event history, and stage output instead of being hidden
inside a single opaque model response.

## Event Persistence And Streaming

Workflow events are append-only evidence records. The frontend timeline can
load persisted history and subscribe to live updates through the existing
WebSocket path. The system does not fake streamed events; live UI behavior
reflects persisted or published workflow event data.

Events are intentionally bounded. They may include stage names, status labels,
messages, event ids, citation ids, and safe summaries. They must not include
secrets, raw provider payloads, raw prompts, raw embeddings, raw vector
payloads, chain-of-thought, or full unbounded document content.

## Approval And Resume Lifecycle

Approval is a backend-enforced workflow lifecycle. Supported decisions are:

- approve
- reject
- request changes

Approve and reject are final decisions. Request changes is non-final and keeps
the workflow in `WAITING_APPROVAL`. Duplicate final decisions, terminal
workflow mutations, and invalid-state decisions are rejected. Reject decisions
require a comment.

Resume is explicit. A workflow can resume only when it is `APPROVED` and has a
final approve record. Resume moves through the bounded post-approval
continuation and reaches `COMPLETED`. It does not send real email.

## RAG Ingestion, Retrieval, And Grounding

The knowledge base is provider-independent at the domain-contract level.
Documents have typed metadata, deterministic content hashes, and bounded safe
attributes. Text is chunked deterministically with a character-based chunker.
Fake embeddings are deterministic and offline-safe by default.

Ingestion is explicit and local-demo scoped. It stores source objects through
MinIO and upserts chunk vectors through Qdrant. It is not run on backend
startup.

Retrieval embeds a search query through the embedding service, queries the
vector store through the provider abstraction, filters and bounds results, and
returns citations. Runtime grounding is behind `RAG_ENABLED`; when disabled,
runtime behavior stays unchanged and no retrieval call occurs.

When enabled, RAG evidence may be attached to compliance, validation, and
approval stages. The state stores citations and bounded excerpts, not full
documents or embeddings.

## Frontend Composition

The frontend is a Next.js dashboard. It uses typed API client functions and the
existing auth/session helpers. Workflow detail composes the operational panels:

- workflow summary/details
- run panel
- approval panel and history
- evidence/citations panel
- lightweight knowledge search/catalog
- persisted and live event timeline

The frontend improves user experience by displaying loading, empty, success,
forbidden, conflict, and generic error states. It does not become the security
authority; backend RBAC remains authoritative.

## Deployment Topology

The production-demo topology is a single Docker Compose stack:

- backend
- frontend
- Postgres
- Redis
- Qdrant
- MinIO

The stack uses environment templates and named volumes. The production-demo
Compose file is additive and does not replace the local development Compose
workflow. Postgres, Redis, Qdrant, and MinIO are not intended to be publicly
exposed without additional network and credential controls.

## Observability Model

The backend exposes:

- `/health` for process health
- `/live` for liveness
- `/ready` for non-mutating dependency readiness
- `/api/v1/observability/metrics` for bounded Admin/Manager metrics

Structured logging includes request IDs and bounded request metadata. Redaction
helpers mask sensitive keys recursively. In-process metrics provide production
demo visibility without telemetry vendor dependencies. Audit logs and workflow
events remain domain evidence rather than a replacement for operational logs.
