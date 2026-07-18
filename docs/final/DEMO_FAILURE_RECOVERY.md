# Demo Failure Recovery

This guide lists safe fallback moves for the final board demo. Do not debug
deep infrastructure problems live. Use bounded evidence artifacts and existing
docs when the live path is unstable.

| Failure | Likely Cause | Safe Fallback | Reference Evidence | Do Not Do Live |
|---|---|---|---|---|
| Backend unavailable | Backend container stopped, port mismatch, env issue. | Show `scripts/deployment/smoke-prod-demo.sh --help`, `docs/deployment/SMOKE_CHECKS.md`, and prior health evidence. | `docs/deployment/RUNBOOK.md`, E2E evidence template. | Do not edit env files with secrets on screen. |
| Frontend unavailable | Frontend container stopped, wrong port, failed build. | Use backend API evidence and screenshots checklist, then explain frontend route coverage. | `docs/final/SCREENSHOT_CHECKLIST.md`, `frontend/README.md`. | Do not run parallel build/typecheck while presenting. |
| Login fails | Demo seed not run, wrong URL, token endpoint unavailable. | Show documented demo seed command and seeded local-demo credential inventory. | `docs/demo/DATASET_INVENTORY.md`, `docs/demo/DEMO_RUNBOOK.md`. | Do not expose or paste tokens. |
| Workflow not found | Seed skipped, wrong database, stale environment. | Show demo seed dry-run/confirmed command and E2E checklist. | `docs/final/E2E_DEMO_VALIDATION.md`, `backend/app/demo/seed.py`. | Do not reset volumes during the board demo. |
| Run does not reach `WAITING_APPROVAL` | Backend dependency issue, invalid seeded state, runtime error. | Show workflow runtime diagram and existing validation evidence; continue with seeded approval scenario if available. | `docs/report/diagrams/WORKFLOW_RUNTIME.md`, `docs/final/EVALUATION_MATRIX.md`. | Do not force status changes manually. |
| Approval returns 403 | Wrong role or expired token. | Explain RBAC is working; log in as Manager/Admin if time allows. | `docs/final/DEFENSE_QA_BANK.md`, approval docs. | Do not weaken RBAC or use hidden tokens. |
| Approval returns 409 | Workflow already finalized, wrong state, duplicate final decision. | Explain lifecycle guard and switch to a fresh waiting workflow if available. | `docs/report/diagrams/APPROVAL_RESUME_LIFECYCLE.md`. | Do not retry duplicate final approvals as if they should succeed. |
| Resume fails | Workflow not approved, already completed, or inconsistent state. | Explain `/resume` safety gate and show lifecycle diagram. | `docs/report/diagrams/APPROVAL_RESUME_LIFECYCLE.md`, E2E checklist. | Do not call `/run` as a substitute for resume. |
| RAG evidence missing | `RAG_ENABLED=false`, knowledge not ingested, Qdrant unavailable, or no matching chunks. | Say empty evidence is honest default behavior; show RAG flow diagram and optional ingestion command. | `docs/report/diagrams/RAG_KNOWLEDGE_FLOW.md`, `docs/demo/DEMO_RUNBOOK.md`. | Do not fake citations or events. |
| Knowledge search empty | Knowledge ingestion skipped, filters too narrow, Qdrant collection unavailable. | Show deterministic document inventory and ingestion dry-run summary. | `docs/demo/DATASET_INVENTORY.md`, `docs/final/E2E_DEMO_VALIDATION.md`. | Do not claim missing results are legal evidence. |
| WebSocket/timeline does not update live | WebSocket URL mismatch, network issue, backend stream unavailable. | Refresh persisted events and explain backlog plus live stream model. | `docs/report/diagrams/EVENT_STREAMING_FLOW.md`. | Do not invent streamed events. |
| `/ready` returns 503 | Postgres, Redis, Qdrant, or MinIO dependency is not reachable. | Explain `/health` is process health and `/ready` is dependency readiness; show troubleshooting steps. | `docs/deployment/TROUBLESHOOTING.md`. | Do not auto-create buckets/collections or run migrations from startup. |
| Metrics endpoint forbidden | Role lacks Admin/Manager access or token missing. | Explain metrics are protected operational data; use docs or authorized account if available. | `docs/deployment/RUNBOOK.md`, observability docs. | Do not expose admin tokens. |
| Docker Compose service unhealthy | Dependency startup delay or bad env value. | Show compose config validation and smoke checklist. | `docs/deployment/SMOKE_CHECKS.md`, `docs/deployment/TROUBLESHOOTING.md`. | Do not delete volumes unless explicitly planned after the demo. |
| CI gate output unavailable | Network/dependency install problem or CI UI inaccessible. | Show local gate scripts and recorded acceptance evidence plan. | `scripts/README.md`, `docs/final/ACCEPTANCE_EVIDENCE_PLAN.md`. | Do not add cloud credentials or push images. |
| Windows Git Bash/WSL bash issue | `bash` resolves to a broken WSL shim on Windows. | Put Git Bash first on `PATH` or run commands from Git Bash. | `docs/final/E2E_DEMO_VALIDATION.md`, `scripts/README.md`. | Do not rewrite scripts for PowerShell during the demo. |
| Live demo time runs short | Board timing changed or recovery consumed time. | Switch to the 3-5 minute fallback summary. | `docs/final/DEMO_TIMING_PLAN.md`. | Do not rush through safety limitations or overclaim unshown evidence. |

## General Recovery Rules

- Keep the demo deterministic and no-key unless real-provider mode was
  explicitly prepared.
- Prefer previously captured evidence over live debugging.
- Do not display access tokens, cookies, provider keys, env files with real
  secrets, raw prompts, raw provider payloads, raw embeddings, vector payloads,
  or customer data.
- Do not mutate production-demo data except through the documented local-demo
  E2E flow guarded by `--confirm-local-demo`.

