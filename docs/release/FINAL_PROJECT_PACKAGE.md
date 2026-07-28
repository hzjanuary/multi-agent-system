# Final Project Package

## Purpose

This document summarizes the final release package for Multi-Agent System /
Enterprise Multi-Agent OS.

Academic title:

```text
Enterprise Procurement Workflow Automation using LangGraph-based Multi-Agent System
```

The project demonstrates a workflow orchestration platform, not a chatbot. It
turns procurement requests into controlled workflows, runs deterministic agent
stages, pauses for human approval, displays bounded evidence, and resumes only
after an authorized decision.

## Completed SPEC Status

SPEC-001 through SPEC-022 are completed and approved in the current release
context. SPEC-023 provides this final release-readiness package and is ready for
closeout review once its checklist/docs are approved.

Major completed areas:

- SPEC-001 through SPEC-004: backend, database, auth/RBAC, and storage
  foundation.
- SPEC-005 through SPEC-008: workflow state, LangGraph runtime, workflow APIs,
  and event streaming.
- SPEC-009 through SPEC-010: frontend dashboard and deterministic demo dataset.
- SPEC-011 through SPEC-014: LLM abstraction, approval/resume, RAG knowledge
  base, and production-demo deployment/observability.
- SPEC-015: final evaluation, demo validation, report, diagram, screenshot,
  demo script, and Q&A assets.
- SPEC-016: conversational sales agent and external reference evidence
  foundation.
- SPEC-017: Violet Operations Console frontend redesign.
- SPEC-018: deterministic catalog expansion.
- SPEC-019: manual-only provider live verification.
- SPEC-020: approved outbound preview only.
- SPEC-021: catalog governance and provider policy.
- SPEC-022: deterministic evaluation benchmarks.
- SPEC-023: release readiness and final packaging docs.

## Architecture Overview

```text
Telegram/local UI intake
  -> FastAPI backend API
  -> JWT auth and RBAC
  -> workflow service/state
  -> LangGraph deterministic runtime
  -> planner/retrieval/calculation/compliance/validation stages
  -> WAITING_APPROVAL
  -> Manager/Admin approval
  -> explicit resume
  -> COMPLETED
  -> preview/evidence/timeline surfaces
```

Storage and infrastructure:

- Postgres stores users, workflows, events, approvals, and audit data.
- Redis supports event streaming/pub-sub paths.
- Qdrant stores vector search data for optional RAG demos.
- MinIO stores demo knowledge documents.
- Docker Compose provides local and production-demo stacks.

Detailed architecture references:

- `docs/report/ARCHITECTURE_AND_DESIGN.md`
- `docs/report/diagrams/README.md`
- `.ai/project/ARCHITECTURE.md`

## Core User Journey

1. A customer request arrives through manual UI entry or the local Telegram
   bridge.
2. The request is normalized against the deterministic demo catalog.
3. A procurement workflow is created through existing backend APIs.
4. `/run` executes deterministic runtime stages.
5. Runtime stops at `WAITING_APPROVAL`.
6. The operator observes status, Agent Activity, timeline events, catalog
   metadata, and optional reference/RAG evidence.
7. Manager/Admin reviews and approves or rejects.
8. `/resume` continues only after approval.
9. Completed workflows may expose approved communication preview if explicit
   preview evidence exists and outbound preview is enabled.

## Stable Demo Path

Stable backend defaults:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
PRICE_RESEARCH_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
```

Stable demo properties:

- deterministic workflow runtime;
- no real LLM provider keys required;
- no Tavily/live provider call;
- no database reset required by evaluation runners;
- explicit demo seed;
- explicit knowledge ingestion only for optional RAG demos;
- no automatic startup seed or ingest;
- no final customer quotation before approval and resume.

## Optional Telegram / Ollama Path

The live phone-to-workflow demo uses:

- local Telegram bot token;
- `scripts/demo/telegram_inbound_bridge.py`;
- deterministic parser and normalizer;
- optional Ollama extraction for natural Vietnamese RFQ text;
- optional sales-style reply templates;
- existing backend login, workflow create, and workflow run APIs.

The bridge:

- does not auto-approve;
- does not auto-resume;
- does not send email;
- does not call Tavily or backend price research providers;
- does not perform live price lookup;
- does not issue customer-ready quotations.

Primary references:

- `docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md`
- `docs/demo/TELEGRAM_INBOUND_DEMO.md`
- `docs/demo/FRONTEND_OPERATOR_GUIDE.md`

## Optional Provider Live Verification Path

Provider live verification is manual-only and separate from the stable demo.

Current provider smoke:

- Tavily dry-run and confirmed live smoke are documented in
  `docs/demo/PROVIDER_LIVE_VERIFICATION.md`.
- Dry-run is no-key and no-network.
- Live smoke requires local `TAVILY_API_KEY` and `--confirm-live-provider`.
- Provider output is reference evidence only.

Provider live verification:

- is not part of CI;
- is not required for release validation;
- does not create or run workflows;
- does not approve/resume;
- does not send email;
- does not write database rows.

## Catalog, Governance, And Evaluation Layers

Catalog layer:

- deterministic demo catalog supports bounded item families and aliases;
- Office 365 is modeled as an add-on, not a price;
- unsupported mixed requests are blocked instead of silently dropped;
- catalog metadata is intake evidence, not pricing, approval, stock, or
  delivery evidence.

Governance layer:

- catalog governance policy;
- provider evidence policy;
- approval/outbound policy;
- future-change checklist.

Evaluation layer:

- Telegram parser benchmark:
  `scripts/evaluation/evaluate_telegram_parser.py`;
- demo safety benchmark:
  `scripts/evaluation/evaluate_demo_safety.py`;
- regression checklist:
  `docs/evaluation/DEMO_REGRESSION_CHECKLIST.md`.

Evaluation runners are deterministic/no-key and require no backend API,
database, Telegram network, provider call, live web call, or email delivery.

## Safety Model

The release safety model is fail-closed:

- unsupported catalog requests ask for clarification;
- mixed supported/unsupported requests are blocked;
- `/run` stops at the human approval boundary;
- `/resume` is the only post-approval continuation path;
- reference evidence remains review material;
- outbound communication is preview-only;
- provider live verification is manual-only;
- frontend surfaces render explicit workflow state only and do not fabricate
  prices, evidence, catalog metadata, events, approvals, or email sends.

The release does not claim:

- final quotation before Manager/Admin approval and explicit resume;
- real email sending;
- stock availability;
- delivery date;
- discount approval;
- automatic live provider research;
- unsupported auto-pricing.

## Docs Map

Release docs:

- `docs/release/RELEASE_READINESS_CHECKLIST.md`
- `docs/release/FINAL_PROJECT_PACKAGE.md`
- `docs/release/DEMO_COMMANDS.md`
- `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md`

Demo docs:

- `docs/demo/FINAL_LIVE_DEMO_RUNBOOK.md`
- `docs/demo/TELEGRAM_INBOUND_DEMO.md`
- `docs/demo/FRONTEND_OPERATOR_GUIDE.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
- `docs/demo/PROVIDER_LIVE_VERIFICATION.md`

Evaluation and final evidence docs:

- `docs/evaluation/SPEC_022_EVALUATION_GUIDE.md`
- `docs/evaluation/DEMO_REGRESSION_CHECKLIST.md`
- `docs/final/README.md`
- `docs/final/EVALUATION_MATRIX.md`
- `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md`
- `docs/final/SCREENSHOT_CHECKLIST.md`

Report and architecture docs:

- `docs/report/README.md`
- `docs/report/ARCHITECTURE_AND_DESIGN.md`
- `docs/report/diagrams/README.md`

Governance docs:

- `docs/governance/CATALOG_GOVERNANCE_POLICY.md`
- `docs/governance/PROVIDER_EVIDENCE_POLICY.md`
- `docs/governance/APPROVAL_OUTBOUND_POLICY.md`
- `docs/governance/GOVERNANCE_CHANGE_CHECKLIST.md`

## Future Roadmap

Recommended post-release roadmap:

1. Approved outbound send spec with audit, provider configuration, and
   operator safeguards.
2. Provider policy enforcement automation and provider evidence audit storage.
3. Expanded catalog governance automation and catalog administration UI.
4. Richer evaluation reports and optional deterministic CI benchmark
   integration.
5. Production hardening for cloud deployment, secret management, monitoring,
   backups, and incident response.
6. Enterprise SSO and production RBAC administration.
7. OCR/PDF ingestion and document management UI.

Future roadmap items are not part of the current release unless explicitly
implemented in a later spec.
