# Graduation Report Outline

This outline is designed for a graduation project report about Enterprise
Procurement Workflow Automation using a LangGraph-based multi-agent system.

## 1. Abstract

Summarize the problem, proposed system, technical approach, evaluation method,
and expected contribution. Keep the abstract concise and avoid implementation
details that belong in later chapters.

## 2. Introduction

Introduce enterprise procurement as a workflow-heavy business process that
requires coordination across sales, finance, legal, and management roles.
Explain why manual handoffs, inconsistent evidence, and weak auditability create
delays and approval risk.

## 3. Problem Statement

Define the core problem: organizations need a controlled system that can turn a
procurement request into a quotation package while preserving deterministic
calculation, compliance evidence, human approval, and traceability.

## 4. Goals And Scope

Describe the project goals:

- automate a bounded procurement quotation workflow
- coordinate specialized workflow stages
- preserve human approval before customer-facing output
- attach policy, contract, pricing, supplier, and compliance evidence
- support deterministic no-key academic evaluation
- provide a frontend dashboard and production-demo deployment path

Clarify that advanced enterprise administration, SSO, production email sending,
and cloud deployment automation are outside the implemented scope.

## 5. Requirements

Organize requirements into:

- functional requirements
- non-functional requirements
- security and safety requirements
- demo and evaluation requirements

Use `SPEC.md` and `.ai/project/API_CONTRACT.md` as primary references.

## 6. Related Work And Background

Discuss background concepts:

- workflow orchestration
- human-in-the-loop automation
- retrieval-augmented generation
- role-based access control
- event-driven observability
- deterministic testing of AI-adjacent systems

Keep this section conceptual unless cited external research is added later by a
report-writing task.

## 7. System Architecture

Describe the overall architecture:

- Next.js dashboard
- FastAPI API boundary
- service and workflow runtime layers
- LangGraph runtime
- Postgres, Redis, Qdrant, and MinIO providers
- LLM and embedding abstraction boundaries

Do not insert diagrams in this task. Diagram source files are deferred to TASK
015.4.

## 8. Technology Stack

Explain the chosen stack:

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, Alembic
- LangGraph for controlled graph orchestration
- Postgres for durable business state
- Redis for event streaming support
- Qdrant for vector search
- MinIO for object storage
- Next.js, TypeScript, and Tailwind CSS for the dashboard
- Docker Compose for local and production-demo packaging

## 9. Multi-Agent Workflow Design

Explain the staged procurement workflow:

```text
Business Request
  -> Planner
  -> Retrieval
  -> Calculator
  -> Compliance
  -> Validation
  -> Human Approval
  -> Email Preparation
  -> Completed
```

Emphasize state transitions, stage isolation, deterministic calculator logic,
bounded LLM usage, and explicit human interruption.

## 10. Data Model And Storage Design

Explain how workflows, events, audit logs, users, roles, object storage, and
knowledge vectors are separated. Describe why workflow state stores bounded
summaries and citations rather than raw documents or provider payloads.

## 11. Authentication And RBAC

Describe JWT authentication, refresh tokens, Argon2 password hashing, and role
permissions for Admin, Manager, Sales, Legal, Finance, and Viewer. Explain that
the backend remains the source of truth for authorization.

## 12. Workflow Runtime And Event Streaming

Describe the runtime lifecycle, persisted workflow events, WebSocket streaming,
and frontend timeline behavior. Explain that events improve transparency
without exposing hidden reasoning or unsafe payloads.

## 13. Human Approval And Resume Lifecycle

Describe approve, reject, and request-changes decisions, approval history,
state transition rules, and explicit post-approval `/resume`. Emphasize that
email preparation does not happen before approval.

## 14. LLM Provider Abstraction

Explain fake/no-key default behavior, optional real provider configuration, and
feature flags. Clarify that deterministic evaluation does not require real LLM
keys.

## 15. RAG And Knowledge Base

Explain deterministic demo documents, chunking, fake embeddings, Qdrant
upsert/search, MinIO source storage, citation contracts, and runtime grounding
behind `RAG_ENABLED`.

## 16. Frontend Dashboard

Explain the dashboard, workflow list/detail, run panel, timeline, approval
panel/history, evidence/citation panel, and lightweight knowledge search/catalog
surfaces.

## 17. Deployment And Observability

Explain Docker Compose production-demo packaging, environment templates,
health/liveness/readiness endpoints, structured logs, request IDs, and bounded
metrics.

## 18. Evaluation Methodology

Reference the final evaluation matrix, acceptance evidence plan, E2E validation
script, and evidence capture template:

- `docs/final/EVALUATION_MATRIX.md`
- `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md`
- `docs/final/E2E_DEMO_VALIDATION.md`
- `docs/final/E2E_EVIDENCE_CAPTURE_TEMPLATE.md`

## 19. Evaluation Results

Placeholder for later captured results. Do not fill this section until the
final validation run has produced evidence.

## 20. Security And Safety Considerations

Discuss no-secret handling, backend RBAC authority, redaction, safe metrics,
no raw prompt/provider payload exposure, and explicit local-demo credential
boundaries.

## 21. Limitations

Summarize implemented limitations honestly. Use
`LIMITATIONS_AND_FUTURE_WORK.md` as the source asset.

## 22. Future Work

Describe deferred enterprise features, production hardening, and larger-scale
document management.

## 23. Conclusion

Summarize the project contribution: a controlled, auditable, deterministic
multi-agent procurement workflow platform with human approval, RAG evidence,
frontend visibility, and production-demo packaging.

## 24. Appendices

Use `APPENDIX_GUIDE.md` to decide appendix contents and source references.
