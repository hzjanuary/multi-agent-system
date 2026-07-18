# Defense Q&A Bank

This bank supports the graduation defense. Answers are concise by design; use
the evidence references for deeper support during Q&A.

## Product And Business Value

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| Why procurement? | Procurement is cross-functional, rule-heavy, and approval-heavy, so it benefits from controlled workflow automation rather than a free-form chatbot. | `SPEC.md`, `docs/report/TECHNICAL_NARRATIVE.md` | Show workflow dashboard and approval boundary. |
| What problem is solved? | The system reduces manual coordination by organizing request handling, quotation calculation, compliance review, approval, and post-approval output into a traceable workflow. | `docs/report/REPORT_OUTLINE.md`, `docs/final/EVALUATION_MATRIX.md` | Run workflow to `WAITING_APPROVAL`. |
| What is the value compared with a manual workflow? | It improves consistency, auditability, evidence visibility, and repeatable execution while keeping human approval for high-stakes decisions. | `docs/report/TECHNICAL_NARRATIVE.md` | Show timeline, approval history, and evidence panel. |
| How does this generalize beyond procurement? | The architecture separates workflow state, runtime stages, services, providers, and frontend views, so other business workflows can reuse the same orchestration pattern. | `docs/report/ARCHITECTURE_AND_DESIGN.md` | Reference system context and backend layered diagrams. |

## Architecture And Technology Choices

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| Why multi-agent? | Procurement work naturally decomposes into planning, retrieval, calculation, compliance, validation, approval, and email preparation responsibilities. Specialized stages make those responsibilities explicit and testable. | `SPEC.md`, `docs/report/TECHNICAL_NARRATIVE.md` | Show workflow runtime diagram. |
| Why LangGraph? | LangGraph provides a controlled state-machine style runtime for staged orchestration, interruption at approval, and bounded resume behavior. | `.ai/specs/SPEC-006-langgraph-runtime/spec.md`, `docs/report/diagrams/WORKFLOW_RUNTIME.md` | Explain `/run` and `/resume`. |
| Why FastAPI? | FastAPI gives typed async API boundaries, Pydantic validation, dependency injection, and straightforward testability. | `.ai/project/TECH_STACK.md`, `backend/README.md` | Show API run/approval/resume endpoints in docs. |
| Why Next.js? | Next.js supports a typed dashboard with route-based workflow views, reusable components, and production build validation. | `.ai/specs/SPEC-009-frontend-dashboard/spec.md`, `frontend/README.md` | Show dashboard/detail UI. |
| Why Postgres, Redis, Qdrant, and MinIO? | Postgres owns durable business state, Redis supports event streaming, Qdrant stores searchable vector chunks, and MinIO stores source objects for the demo knowledge base. | `docs/report/ARCHITECTURE_AND_DESIGN.md`, `docs/report/diagrams/BACKEND_LAYERED_ARCHITECTURE.md` | Show architecture or RAG flow diagram. |
| Why Docker Compose for production-demo? | Compose is reproducible and bounded for a graduation demo stack. It avoids over-scoping cloud, Kubernetes, or Terraform before the product requires them. | `docs/deployment/RUNBOOK.md`, `docs/report/diagrams/CONTAINER_DEPLOYMENT.md` | Show production-demo runbook or smoke output. |

## Workflow And Runtime Correctness

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| How do you guarantee workflow state consistency? | Workflow status transitions are handled by backend services and lifecycle rules, with persisted workflow state and events in Postgres. | `.ai/specs/SPEC-005-workflow-state/spec.md`, `.ai/specs/SPEC-007-workflow-api/spec.md` | Show status and event timeline. |
| Why does `/run` stop at `WAITING_APPROVAL`? | The system intentionally prevents customer-facing continuation until a human manager/admin performs a final approval decision. | `.ai/specs/SPEC-012-human-approval-and-resume/spec.md`, `docs/report/diagrams/WORKFLOW_RUNTIME.md` | Run workflow and show waiting state. |
| How does resume work? | `/resume` validates that the workflow is approved, then executes only the bounded post-approval continuation to email preview and `COMPLETED`. | `.ai/specs/SPEC-012-human-approval-and-resume/spec.md` | Approve, then click Resume. |
| How are events persisted and streamed? | Workflow events are persisted first and then published through the existing Redis/WebSocket path so the frontend can show backlog and live updates. | `.ai/specs/SPEC-008-event-streaming/spec.md`, `docs/report/diagrams/EVENT_STREAMING_FLOW.md` | Show event timeline after run/resume. |
| What happens on failure? | Failures are represented through safe statuses, events, validation errors, readiness failures, or bounded API errors rather than hidden background mutation. | `docs/deployment/TROUBLESHOOTING.md`, `docs/final/DEMO_FAILURE_RECOVERY.md` | Use recovery docs if live failure occurs. |

## Human Approval And Governance

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| Why human-in-the-loop? | Procurement decisions can affect customer commitments, pricing, compliance, and financial risk, so final release should require accountable human approval. | `SPEC.md`, `.ai/specs/SPEC-012-human-approval-and-resume/spec.md` | Show approval panel. |
| How are duplicate approvals prevented? | Final approve/reject decisions are guarded by lifecycle helpers and service checks; once final, duplicate final mutations are rejected. | `.ai/specs/SPEC-012-human-approval-and-resume/spec.md`, `docs/report/diagrams/APPROVAL_RESUME_LIFECYCLE.md` | Mention 409 conflict handling. |
| How does RBAC work? | Existing roles protect routes and service-level mutations. Admin/Manager can approve/resume; Viewer remains read-only. | `.ai/specs/SPEC-003-auth-rbac/spec.md`, backend tests referenced by final matrix | Optional Viewer forbidden check. |
| How is auditability achieved? | Approval decisions, workflow events, state transitions, request IDs, and bounded logs provide a traceable record. | `docs/final/EVALUATION_MATRIX.md`, `docs/report/ARCHITECTURE_AND_DESIGN.md` | Show approval history and timeline. |
| What happens with request changes or reject? | `request_changes` is non-final and keeps the workflow waiting; `reject` is final and blocks resume. | `docs/report/diagrams/APPROVAL_RESUME_LIFECYCLE.md` | Explain lifecycle diagram. |

## LLM And Deterministic Mode

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| Why support fake/no-key mode? | It makes academic evaluation reproducible without paid providers, network dependencies, or secret handling risk. | `docs/llm/LOCAL_LLM_DEMO.md`, `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md` | Show no-key env settings. |
| How do real providers fit? | Real providers are behind existing SPEC-011 feature flags and settings. The default demo does not require them. | `.ai/specs/SPEC-011-llm-provider-abstraction/spec.md`, `docs/llm/PROVIDER_SETUP.md` | Mention optional provider setup docs. |
| What are the risks of LLMs? | Risks include nondeterminism, hallucination, unsafe output, cost, latency, and secret exposure, so the runtime keeps deterministic fallbacks and bounded contracts. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | Explain fake default mode. |
| How is unsafe provider output handled? | Structured output boundaries and feature flags limit where provider output can enter the system, and raw provider payloads/prompts are not exposed in logs/UI. | `.ai/specs/SPEC-011-llm-provider-abstraction/spec.md`, observability docs | Show safety notes. |
| Why not require live LLMs for evaluation? | The graduation proof focuses on architecture, workflow correctness, approval governance, RAG wiring, and deployability, all reproducible without live paid providers. | `docs/final/EVALUATION_MATRIX.md` | State no-key default. |

## RAG And Knowledge Grounding

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| Why RAG? | RAG connects compliance, finance, and approval review to source evidence instead of relying only on generated text. | `.ai/specs/SPEC-013-rag-document-knowledge-base/spec.md`, `docs/report/diagrams/RAG_KNOWLEDGE_FLOW.md` | Show evidence/citations panel. |
| How are documents chunked and embedded? | Demo documents are chunked deterministically, checksummed, embedded with fake hash embeddings by default, stored in MinIO, and indexed in Qdrant. | `docs/demo/DATASET_INVENTORY.md`, `backend/README.md` | Show knowledge ingestion command. |
| Why fake embeddings? | Fake embeddings keep retrieval tests and demos deterministic and no-key while preserving the provider boundary for future real embeddings. | `.ai/specs/SPEC-013-rag-document-knowledge-base/spec.md` | Mention optional RAG no-key mode. |
| How are citations shown? | Citations expose bounded fields: source title/type, label, section/page, excerpt, relevance score, stage, and document id. | `docs/final/SCREENSHOT_CHECKLIST.md`, frontend README | Show evidence panel. |
| What are RAG limitations? | It is demo-scale, has no enterprise document permissions, no upload UI, no production OCR/PDF parsing, and citations support review but are not legal advice. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | Explain during evidence panel. |
| What prevents raw payload leaks? | Contracts, UI extraction rules, redaction helpers, and event payload bounds avoid exposing raw prompts, embeddings, vector payloads, provider payloads, or secrets. | `docs/final/EVALUATION_MATRIX.md`, observability docs | Mention during RAG safety explanation. |

## Security And Safety

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| How are secrets handled? | Templates use placeholders, real secrets must be injected through deployment environments, and committed docs avoid real keys. | `docs/deployment/ENVIRONMENT.md` | Show env docs, not real env files. |
| How are endpoints protected? | Auth and RBAC protect workflow, approval/resume, knowledge, and observability routes according to their roles. | `.ai/specs/SPEC-003-auth-rbac/spec.md`, `.ai/project/API_CONTRACT.md` | Optional Viewer forbidden check. |
| What is not production-ready yet? | Enterprise SSO, secret vault, cloud automation, production email, upload/admin document UI, OCR, multi-tenant isolation, and production backups are deferred. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | State limitations honestly. |
| How are logs and metrics redacted? | Structured observability masks sensitive keys recursively, bounds values, and avoids request/response bodies. | `.ai/specs/SPEC-014-production-deployment-observability/spec.md`, deployment docs | Show metrics endpoint only if authorized. |
| Why no email sending in demo? | The demo produces a preview after approval but avoids sending real customer communication from an academic demo environment. | `SPEC.md`, `.ai/specs/SPEC-012-human-approval-and-resume/spec.md` | Show completed email preview state if available. |

## Deployment And Observability

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| How would this run outside a laptop? | The production-demo Compose stack packages frontend, backend, Postgres, Redis, Qdrant, and MinIO with explicit env templates and smoke checks. | `docs/deployment/RUNBOOK.md`, `docker-compose.prod.yml` | Show smoke script or compose docs. |
| What do `/health`, `/live`, and `/ready` mean? | `/health` and `/live` are lightweight process checks; `/ready` checks required infrastructure dependencies without mutating state. | `docs/deployment/SMOKE_CHECKS.md`, backend README | Show `/ready` if healthy. |
| What metrics are available? | The backend exposes bounded in-process HTTP and application counters through an Admin/Manager-protected JSON metrics endpoint. | `.ai/specs/SPEC-014-production-deployment-observability/spec.md`, backend README | Optional metrics endpoint check. |
| What does CI prove? | CI validates Compose config, backend tests/static checks, frontend checks, production image builds, dry-run seed/ingest, and whitespace. It does not deploy or push images. | `.github/workflows/ci.yml`, `scripts/README.md` | Show CI/local gate docs. |
| What remains for cloud production? | Cloud deployment automation, secret vault, reverse-proxy/HTTPS hardening, production backup automation, autoscaling, and enterprise SSO remain future work. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | State deferred scope. |

## Evaluation And Testing

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| What evidence proves the system works? | Evidence comes from CI/local gates, backend/frontend tests, E2E validation, smoke checks, screenshots, workflow lifecycle records, RAG citations, readiness, and metrics. | `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md` | Show final evidence docs. |
| How are tests organized? | Backend tests validate contracts, services, APIs, runtime, approvals, RAG, readiness, observability, and CLI behavior; frontend tests validate API clients and workflow UI surfaces. | `docs/final/EVALUATION_MATRIX.md` | Reference all-gates script. |
| How is the E2E demo validated? | The guarded E2E script checks health/live, optional readiness, seed/ingest, login, workflow run, approval, resume, events, optional RAG, optional RBAC, and optional metrics. | `docs/final/E2E_DEMO_VALIDATION.md`, `scripts/final/e2e-demo-validation.sh` | Mention script usage. |
| What are the limitations of evaluation? | Evaluation is demo-scale and deterministic by default; it does not include user studies, benchmark numbers, cloud deployment tests, or paid-provider dependency. | `docs/report/EVALUATION_NARRATIVE.md` | Explain no invented metrics. |
| What would you measure next? | Next measurements would include workflow cycle time, retrieval precision, approval turnaround, user workload reduction, provider latency/cost, and operational reliability under load. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | Use future-work discussion. |

## Future Work

| Question | Concise Answer | Evidence / Doc Reference | Demo Pointer |
|---|---|---|---|
| What is the next product feature? | If enterprise completeness is the goal, admin operations and approval-policy management are strong next candidates. | `.ai/specs/SPEC-015-final-evaluation-demo-report-assets/spec.md` | Discuss roadmap. |
| What is needed for production document management? | Upload/admin document UI, document permissions, OCR/PDF parsing, external connectors, and governance workflows are deferred. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | Reference RAG limitations. |
| What is needed for enterprise authentication? | Enterprise SSO, stronger production session handling, and tenant-aware policies would be later specs. | `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | Reference RBAC boundary. |
| What is needed for production operations? | Secret vault, HTTPS/reverse proxy hardening, cloud automation, backup automation, monitoring integrations, and rollback automation are future work. | `docs/deployment/RUNBOOK.md`, `docs/report/LIMITATIONS_AND_FUTURE_WORK.md` | Reference deployment scope. |
| What should not be added just for the demo? | Avoid token streaming, agent-thought streaming, fake events, real email sending, real secrets, and unbounded provider payload exposure. | `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md` | State safety boundary. |

