# Backend Layered Architecture Diagram

```mermaid
flowchart TB
    Client["Frontend/API clients"]

    subgraph API["FastAPI API layer"]
        AuthRoutes["auth routes"]
        WorkflowRoutes["workflow routes"]
        KnowledgeRoutes["knowledge routes"]
        HealthRoutes["health/readiness routes"]
        ObservabilityRoutes["observability routes"]
    end

    AuthRbac["Auth + RBAC dependencies"]

    subgraph Services["Application services"]
        AuthService["authentication service"]
        WorkflowService["workflow service"]
        RuntimeService["runtime service"]
        ApprovalService["approval service"]
        RetrievalService["knowledge retrieval service"]
        LLMService["LLM service\noptional/fake default"]
        ReadinessService["readiness checker"]
        MetricsService["in-process metrics"]
    end

    subgraph Providers["Repositories and providers"]
        DbRepo["SQLAlchemy repositories/session"]
        CacheProvider["Redis cache/event provider"]
        VectorProvider["Qdrant vector store provider"]
        ObjectProvider["MinIO object storage provider"]
        EmbeddingProvider["embedding service\nfake default"]
    end

    subgraph Infra["Infrastructure"]
        Postgres[("Postgres")]
        Redis[("Redis")]
        Qdrant[("Qdrant")]
        MinIO[("MinIO")]
        LLM["Optional chat LLM providers"]
    end

    Client --> API
    API --> AuthRbac
    AuthRbac --> Services
    WorkflowRoutes --> WorkflowService
    WorkflowRoutes --> RuntimeService
    WorkflowRoutes --> ApprovalService
    KnowledgeRoutes --> RetrievalService
    AuthRoutes --> AuthService
    HealthRoutes --> ReadinessService
    ObservabilityRoutes --> MetricsService

    Services --> DbRepo
    RuntimeService --> CacheProvider
    RetrievalService --> VectorProvider
    RetrievalService --> EmbeddingProvider
    ReadinessService --> DbRepo
    ReadinessService --> CacheProvider
    ReadinessService --> VectorProvider
    ReadinessService --> ObjectProvider
    LLMService -. "LLM_RUNTIME_ENABLED=true" .-> LLM

    DbRepo --> Postgres
    CacheProvider --> Redis
    VectorProvider --> Qdrant
    ObjectProvider --> MinIO
```

This diagram shows the backend separation of concerns. API routes validate HTTP
contracts and enforce auth/RBAC; services own workflow, approval, runtime,
knowledge, readiness, and metrics behavior; providers isolate infrastructure.

It matters for the report because it explains how business rules avoid leaking
into frontend code, provider clients, or route handlers.

Related docs: `.ai/project/ARCHITECTURE.md`,
`docs/report/ARCHITECTURE_AND_DESIGN.md`, and backend route/service specs.
