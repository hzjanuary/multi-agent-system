# 0014 Observability Metrics Boundary

Date: 2026-07-16

## Status

Accepted

## Context

TASK 014.4 adds backend operational observability foundations for the
production-demo stack. The work needs a metrics surface without adding a
telemetry vendor, leaking sensitive runtime data, or weakening existing API and
RBAC boundaries.

## Decision

Expose bounded in-process backend metrics through
`GET /api/v1/observability/metrics` and protect the route with existing
Admin/Manager RBAC. Keep metrics vendor-neutral JSON and limit labels to
low-cardinality request metadata: method, route/path label, and status class.
Do not expose environment variables, request bodies, response bodies,
authorization headers, cookies, workflow IDs, user IDs, document IDs, query
text, embeddings, vector payloads, prompts, provider payloads, or secrets.

Use the same redaction helpers for operational log payloads and structured log
processors. Keep Prometheus, OpenTelemetry exporters, telemetry vendor SDKs,
cost dashboards, token streaming, and agent-thought streaming deferred to later
specs.

## Alternatives Considered

1. Expose unauthenticated `/metrics`.
2. Add Prometheus/OpenTelemetry dependencies now.
3. Instrument domain service counters in every workflow, approval, RAG, and LLM
   service during this task.

## Consequences

Positive:

- Production-demo operators get safe operational visibility without new
  infrastructure dependencies.
- Metrics access follows existing authenticated RBAC.
- The implementation avoids high-cardinality labels and sensitive payloads.

Tradeoffs:

- In-process metrics reset on backend restart and are not suitable as a
  production monitoring store.
- Domain-specific counters remain limited until a later observability task adds
  carefully scoped service-level instrumentation.

## Follow-Up

- Plan external metrics scraping/export and long-term retention in a later
  production observability spec.
- Add service-level domain counters only where they can be tested without
  widening workflow/API behavior.
