# Architecture Diagram Index

This folder contains report-ready Mermaid diagram source files for Enterprise
Multi-Agent OS. The files are Markdown source only. No PNG, SVG, PDF, DOCX,
slides, screenshots, or generated image assets are produced in TASK 015.4.

## Diagram Files

- `SYSTEM_CONTEXT.md` - user roles, frontend, backend, runtime, infrastructure,
  and optional LLM providers.
- `CONTAINER_DEPLOYMENT.md` - production-demo Docker Compose stack, internal
  network, bounded public ports, and persistent volumes.
- `BACKEND_LAYERED_ARCHITECTURE.md` - API, auth/RBAC, services, repositories,
  providers, and infrastructure dependencies.
- `WORKFLOW_RUNTIME.md` - `/run` workflow path to `WAITING_APPROVAL` and
  explicit `/resume` continuation after approval.
- `APPROVAL_RESUME_LIFECYCLE.md` - approval decision and resume state machine.
- `RAG_KNOWLEDGE_FLOW.md` - demo knowledge ingestion, retrieval, grounding, and
  frontend evidence/search/catalog flow.
- `EVENT_STREAMING_FLOW.md` - persisted event backlog, Redis pub/sub,
  WebSocket streaming, and frontend timeline.
- `CI_DEPLOYMENT_FLOW.md` - CI/local gates, production-demo image build, Compose
  stack, and smoke validation without deploy/push behavior.

## Usage Notes

- Keep Mermaid blocks in Markdown so diagrams remain maintainable in source
  control.
- Use these diagrams as source material for `docs/report/REPORT_OUTLINE.md`
  sections 7, 9, 12, 13, 15, and 17.
- Do not edit diagrams to show unimplemented capabilities such as Kubernetes,
  Terraform, secret vault integration, production OCR, upload UI, real email
  sending, token streaming, or agent thought streaming.
- Do not include secrets, tokens, raw prompts, raw provider payloads, raw
  embeddings, raw vector payloads, chain-of-thought, or real customer data.
