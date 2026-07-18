# System Context Diagram

```mermaid
flowchart LR
    Admin["Admin"]
    Manager["Manager"]
    Sales["Sales"]
    Legal["Legal"]
    Finance["Finance"]
    Viewer["Viewer"]

    Frontend["Next.js dashboard"]
    Backend["FastAPI backend API"]
    Runtime["LangGraph multi-agent workflow runtime"]
    Postgres[("Postgres business state")]
    Redis[("Redis event pub/sub")]
    Qdrant[("Qdrant vector store")]
    MinIO[("MinIO object storage")]
    LLM["Optional LLM providers\nfeature-flagged"]

    Admin --> Frontend
    Manager --> Frontend
    Sales --> Frontend
    Legal --> Frontend
    Finance --> Frontend
    Viewer --> Frontend

    Frontend -->|"REST API + WebSocket"| Backend
    Backend --> Runtime
    Backend --> Postgres
    Backend --> Redis
    Backend --> Qdrant
    Backend --> MinIO
    Runtime --> Postgres
    Runtime --> Redis
    Runtime -. "LLM_RUNTIME_ENABLED=true only" .-> LLM
```

This diagram shows the user-facing system boundary. Business users interact
through the Next.js dashboard, while the FastAPI backend remains the authority
for authentication, RBAC, workflow state, approval, retrieval, and operational
metrics.

It matters for the report because it distinguishes implemented infrastructure
from optional provider integrations. LLM provider calls are feature-flagged and
not required for deterministic no-key evaluation.

Related docs: `SPEC.md`, `docs/report/TECHNICAL_NARRATIVE.md`,
`docs/report/ARCHITECTURE_AND_DESIGN.md`, and
`.ai/specs/SPEC-011-llm-provider-abstraction/spec.md`.
