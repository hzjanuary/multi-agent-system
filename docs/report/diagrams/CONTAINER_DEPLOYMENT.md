# Container Deployment Diagram

```mermaid
flowchart TB
    Operator["Demo operator / evaluator"]

    subgraph Public["Bounded public demo access"]
        FrontendPort["Frontend port 3000"]
        BackendPort["Backend API port 8000"]
    end

    subgraph Compose["Docker Compose production-demo stack"]
        direction TB
        subgraph Net["enterprise-os-internal network"]
            Frontend["frontend\nNext.js production container"]
            Backend["backend\nFastAPI runtime container"]
            Postgres["postgres\ninternal only"]
            Redis["redis\ninternal only"]
            Qdrant["qdrant\ninternal only"]
            MinIO["minio\ninternal demo/admin only"]
        end

        PgVol[("postgres_prod_data")]
        RedisVol[("redis_prod_data")]
        QdrantVol[("qdrant_prod_data")]
        MinioVol[("minio_prod_data")]
    end

    Operator --> FrontendPort --> Frontend
    Operator --> BackendPort --> Backend
    Frontend -->|"NEXT_PUBLIC_API_BASE_URL / WS URL"| Backend
    Backend --> Postgres
    Backend --> Redis
    Backend --> Qdrant
    Backend --> MinIO
    Postgres --- PgVol
    Redis --- RedisVol
    Qdrant --- QdrantVol
    MinIO --- MinioVol
```

This diagram shows the implemented production-demo topology. The stack is a
single Docker Compose deployment with backend, frontend, and required
infrastructure services on an internal network. Persistent named volumes store
stateful service data.

It matters for the report because it shows a reproducible deployment path
without claiming cloud, Kubernetes, Terraform, autoscaling, or secret-vault
automation.

Related docs: `docker-compose.prod.yml`, `docs/deployment/RUNBOOK.md`,
`docs/deployment/ENVIRONMENT.md`, and `docs/deployment/SMOKE_CHECKS.md`.
