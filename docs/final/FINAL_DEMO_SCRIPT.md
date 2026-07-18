# Final Demo Script

This script supports an 8-12 minute graduation board demonstration for
Enterprise Multi-Agent OS. It is a speaker guide only; it does not replace the
operator runbooks or final evidence capture checklist.

## 1. Opening Pitch

Enterprise Multi-Agent OS is a state-driven procurement workflow platform that
coordinates specialized agents, deterministic business logic, human approval,
RAG evidence, and production-demo operations in one auditable system.

Enterprise procurement workflows are slow because they cross Sales, Finance,
Legal, and Management responsibilities. They also require evidence, approvals,
and audit records before customer-facing output is safe. This project shows how
a multi-agent workflow runtime can assist those roles while keeping human
governance at the high-risk decision point.

The solution is not a chatbot. It is a controlled business workflow operating
system: the frontend starts and monitors the work, the backend owns state and
policy, LangGraph coordinates the runtime stages, and human approval/resume
controls when the process can continue.

## 2. Context And Value Proposition

The demo focuses on a procurement quotation workflow. A request is processed
through planning, retrieval, quotation calculation, compliance, validation,
approval packaging, human approval, and post-approval email preview.

Several human roles are represented:

- Sales creates and tracks procurement workflows.
- Finance concerns are represented in deterministic quotation and validation
  checks.
- Legal/compliance concerns are represented in policy and contract evidence.
- Managers/Admins make approval and resume decisions.
- Viewers can observe but cannot mutate approval or resume state.

Board-level value:

- Faster cycle time: repeated procurement review steps are orchestrated in a
  consistent workflow.
- Process consistency: each stage follows explicit status transitions.
- Auditability: workflow events, approval history, and runtime state provide
  traceable evidence.
- Evidence-grounded decisions: optional RAG citations connect compliance,
  finance, and approval context to demo knowledge documents.
- Deployment readiness: production-demo Compose, health/readiness, metrics, CI
  gates, and smoke scripts make the system demonstrable outside a developer
  notebook.

## 3. Architecture Overview

Use the Mermaid source diagrams in `docs/report/diagrams/` as visual support.
The most useful diagrams for this section are:

- `SYSTEM_CONTEXT.md`
- `CONTAINER_DEPLOYMENT.md`
- `BACKEND_LAYERED_ARCHITECTURE.md`
- `WORKFLOW_RUNTIME.md`
- `RAG_KNOWLEDGE_FLOW.md`
- `CI_DEPLOYMENT_FLOW.md`

Talk track:

The dashboard is built with Next.js and communicates with the FastAPI backend
through typed REST and WebSocket clients. FastAPI exposes auth, workflow,
approval/resume, knowledge, health, readiness, and observability endpoints.

The runtime uses LangGraph to organize the procurement workflow into bounded
stages. Postgres stores users, workflow state, events, approval records, and
audit evidence. Redis supports the event streaming path. Qdrant stores vector
chunks for the knowledge base, and MinIO stores original demo knowledge
documents where appropriate.

The LLM provider abstraction is optional and feature-flagged. The default
academic evaluation path uses deterministic fake/no-key behavior so the demo
can be reproduced without paid provider access. RAG uses fake embeddings by
default and can be enabled explicitly for evidence-grounded runs.

## 4. Live Demo Steps

Use `docs/final/E2E_DEMO_VALIDATION.md` for the complete reproducible
validation flow and `docs/final/SCREENSHOT_CHECKLIST.md` for evidence capture.

1. Start from the workflow dashboard.
   - Show that the system has an authenticated dashboard and workflow list.
   - Mention that demo credentials are local-demo/board-demo only.

2. Open the procurement workflow detail.
   - Point out workflow status, customer/request context, run controls, event
     timeline, approval area, evidence panel, and knowledge search/catalog
     surfaces.

3. Run the workflow.
   - Use the existing workflow run action.
   - State that `/run` starts the pre-approval runtime and must stop at
     `WAITING_APPROVAL`.

4. Verify `WAITING_APPROVAL`.
   - Show the status and event timeline after the run.
   - Explain that the email preview has not been generated because the manager
     boundary has not been crossed.

5. Show RAG evidence if enabled.
   - Open the evidence/citations panel.
   - Show source title/type, citation label, excerpt, stage, relevance score,
     and document id.
   - Show knowledge search or document catalog if useful.
   - If RAG is disabled, say the empty evidence state is expected in the
     default no-key mode.

6. Submit approval.
   - Use a bounded manager comment.
   - Show the workflow moves to `APPROVED`.
   - Show approval history and approval timeline evidence.

7. Resume workflow.
   - Use the explicit resume action.
   - State that continuation uses `/resume`, not `/run`.
   - Verify status reaches `COMPLETED`.
   - Show resume and email-preparation preview events.
   - Clarify that no real email is sent in the demo.

8. Optional operations proof.
   - Show `/ready` behavior or the smoke script output.
   - Show `/api/v1/observability/metrics` only with an authorized Admin or
     Manager token and without exposing tokens.
   - Mention CI/local gates and the final E2E validation script.

## 5. Safety And Governance Explanation

The system keeps high-impact business actions behind explicit authorization.
RBAC uses the implemented roles: Admin, Manager, Sales, Legal, Finance, and
Viewer. Approval and resume mutations are restricted to Admin/Manager in this
slice, while read workflows remain available to allowed read roles.

The human approval lifecycle is explicit:

- `request_changes` records non-final feedback and keeps the workflow in
  `WAITING_APPROVAL`.
- `approve` is final and moves the workflow to `APPROVED`.
- `reject` is final and moves the workflow to `REJECTED`.
- duplicate final decisions are blocked.
- terminal workflows cannot be mutated through approval decisions.
- `/resume` only continues after approval and a valid final approve record.

Auditability comes from persisted workflow events, approval history, request
IDs, and bounded logs/metrics. The demo avoids automatic email sending, startup
seeding, startup ingestion, and live provider calls by default.

## 6. RAG Explanation

The knowledge base demonstrates evidence grounding without requiring real LLM
keys. Demo documents cover procurement policy, contract terms, supplier
evaluation notes, pricing guidance, and compliance checks.

The ingestion path chunks deterministic text, computes stable checksums,
generates fake embeddings by default, stores original source objects through
MinIO, and upserts chunk vectors through Qdrant. Retrieval returns bounded
results with safe citation metadata.

When `RAG_ENABLED=false`, runtime behavior remains deterministic and does not
call retrieval. When `RAG_ENABLED=true`, the runtime grounding adapter retrieves
bounded evidence for compliance, validation/finance, and approval stages and
attaches safe citations to workflow state and events. It does not expose raw
embeddings, raw vector payloads, raw prompts, provider payloads, or
chain-of-thought.

RAG limitations to state clearly:

- It is a demo-scale knowledge base, not enterprise document governance.
- There is no upload/admin document management UI in this spec.
- There is no production OCR/PDF parsing pipeline yet.
- Citations support review; they are not legal advice.

## 7. Deployment And Operations Explanation

The production-demo stack is Docker Compose based. It packages frontend,
backend, Postgres, Redis, Qdrant, and MinIO with persistent volumes and a
bounded public-port strategy. It intentionally avoids cloud-specific Terraform,
Kubernetes, image-push automation, and secret-vault integration in this phase.

Environment templates separate local-demo, CI/test, and production-demo
profiles. Real secrets are never committed. The default demo remains no-key:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

Operational proof points:

- `/health` and `/live` confirm the process is running.
- `/ready` checks Postgres, Redis, Qdrant, and MinIO readiness.
- Structured logs include request IDs and avoid request/response bodies.
- Metrics are in-process, bounded, and available to Admin/Manager.
- CI/local gates run Compose validation, backend tests/static checks, frontend
  checks, production image build, dry-run seed, dry-run knowledge ingestion,
  and whitespace checks.
- The smoke script validates a running production-demo stack without mutating
  demo data by default.

## 8. Closing Summary

This project proves a full procurement workflow path from request processing to
human approval and post-approval completion. It demonstrates stateful
multi-agent orchestration, deterministic no-key evaluation, RBAC governance,
approval/resume safety, event transparency, RAG evidence grounding, frontend
workflow usability, and production-demo operations.

The academic contribution is the integration of controlled multi-agent
workflow execution with auditable human-in-the-loop governance and
evidence-grounded review, packaged as a reproducible graduation project rather
than a prompt-only prototype.

Future work includes configurable approval chains, enterprise document upload
and governance, OCR/PDF ingestion, enterprise SSO, production secret vault,
cloud deployment automation, production email/notification delivery,
multi-tenant isolation, and deeper operational analytics.

