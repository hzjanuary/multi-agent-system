# CI And Deployment Flow Diagram

```mermaid
flowchart TB
    Dev["Developer push / PR"]
    CI["GitHub Actions CI"]
    ComposeGate["Compose gate"]
    BackendGate["Backend gate\npytest, ruff, black, mypy,\nmigrations, dry-run seed/ingest"]
    FrontendGate["Frontend gate\ninstall, lint, build,\ntypecheck, tests"]
    ImageBuild["Production-demo image build\nbackend + frontend"]
    Whitespace["git diff --check"]
    LocalProd["Local production-demo Compose stack"]
    Smoke["smoke-prod-demo.sh\nhealth/live/frontend\noptional ready"]
    NoDeploy["No deploy or image push\nby default"]

    Dev --> CI
    CI --> ComposeGate
    CI --> BackendGate
    CI --> FrontendGate
    CI --> ImageBuild
    CI --> Whitespace
    ComposeGate --> LocalProd
    ImageBuild --> LocalProd
    LocalProd --> Smoke
    CI --> NoDeploy
```

This diagram shows the quality and production-demo validation flow. CI and
local scripts validate Compose files, backend and frontend gates, production
image builds, and whitespace. The smoke script checks an already-running stack
by default.

It matters for the report because it demonstrates repeatable validation without
claiming real deployment, image registry publishing, cloud resources, or
Kubernetes/Terraform automation.

Related docs: `.github/workflows/ci.yml`, `scripts/README.md`,
`docs/deployment/SMOKE_CHECKS.md`, and
`.ai/specs/SPEC-014-production-deployment-observability/spec.md`.
