# Event Streaming Flow Diagram

```mermaid
sequenceDiagram
    participant Runtime as Runtime/Services
    participant Events as WorkflowEventService
    participant DB as Postgres WorkflowEvent table
    participant Redis as Redis pub/sub
    participant WS as WebSocket endpoint
    participant UI as Frontend timeline

    Runtime->>Events: append safe workflow event
    Events->>DB: persist event record
    Events->>Redis: publish event notification
    UI->>WS: subscribe to /workflows/{id}/stream
    WS->>DB: load persisted backlog
    DB-->>WS: backlog events
    WS-->>UI: send backlog messages
    Redis-->>WS: live event notification
    WS-->>UI: send live event message
```

This diagram shows how timeline evidence is produced. Runtime, approval,
resume, and RAG grounding behavior append persisted workflow events. The
frontend timeline receives both backlog events and live messages through the
existing WebSocket stream.

It matters for the report because it shows transparency without inventing a
second streaming mechanism or faking streamed events.

Related docs: `.ai/specs/SPEC-008-event-streaming/spec.md`,
`docs/demo/FRONTEND_SMOKE_FLOW.md`, and
`docs/final/E2E_DEMO_VALIDATION.md`.
