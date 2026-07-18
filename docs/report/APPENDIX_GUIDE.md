# Appendix Guide

This guide lists appendix material that can support the final graduation
report. It is a planning/narrative asset only; it does not collect final
evidence.

## Appendix A: Setup And Environment

Recommended source references:

- `README.md`
- `backend/README.md`
- `frontend/README.md`
- `docs/deployment/ENVIRONMENT.md`
- `docs/deployment/.env.production.example`
- `docs/deployment/.env.ci.example`

Suggested appendix content:

- local-demo environment profile
- CI/test environment profile
- production-demo environment profile
- no-key default configuration
- optional RAG-enabled configuration
- secret-handling rules

## Appendix B: Deployment Commands

Recommended source references:

- `docs/deployment/RUNBOOK.md`
- `docs/deployment/SMOKE_CHECKS.md`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `scripts/deployment/smoke-prod-demo.sh`

Suggested appendix content:

- Compose validation command
- production-demo image build command
- stack startup command
- smoke check command
- health/readiness endpoint summary

## Appendix C: CI And Local Quality Gates

Recommended source references:

- `.github/workflows/ci.yml`
- `scripts/README.md`
- `scripts/ci/compose-gate.sh`
- `scripts/ci/backend-gate.sh`
- `scripts/ci/frontend-gate.sh`
- `scripts/ci/all-gates.sh`

Suggested appendix content:

- backend gate command list
- frontend gate command list
- production image build gate
- no-key CI behavior
- frontend build/typecheck serial note

## Appendix D: Demo Dataset And Knowledge Ingestion

Recommended source references:

- `docs/demo/DATASET_INVENTORY.md`
- `docs/demo/DEMO_RUNBOOK.md`
- `backend/app/demo/seed.py`
- `backend/app/knowledge/ingest_demo.py`

Suggested appendix content:

- deterministic demo credentials marked local-demo only
- seeded workflow examples
- demo seed command
- demo knowledge ingestion command
- dry-run commands
- RAG-enabled demo prerequisites

## Appendix E: End-to-End Demo Validation

Recommended source references:

- `docs/final/E2E_DEMO_VALIDATION.md`
- `docs/final/E2E_EVIDENCE_CAPTURE_TEMPLATE.md`
- `docs/final/SCREENSHOT_CHECKLIST.md`
- `scripts/final/e2e-demo-validation.sh`

Suggested appendix content:

- E2E validation command
- optional RAG/RBAC/metrics switches
- expected workflow status progression
- evidence capture checklist
- skipped optional checks

## Appendix F: API Endpoint Summary

Recommended source references:

- `.ai/project/API_CONTRACT.md`
- `README.md`
- `backend/README.md`
- backend OpenAPI docs from a running local instance

Suggested appendix content:

- auth endpoint summary
- workflow endpoint summary
- approval/resume endpoint summary
- knowledge endpoint summary
- health/readiness/observability endpoint summary

Do not paste bearer tokens, secret-bearing headers, full response bodies with
sensitive data, or raw provider payloads into the appendix.

## Appendix G: Screenshots

Screenshot planning is defined in `docs/final/SCREENSHOT_CHECKLIST.md`.
Expected screenshot categories include:

- login page
- workflow dashboard
- workflow detail before run
- `WAITING_APPROVAL` state
- approval panel/history
- evidence/citations panel
- knowledge search/catalog
- timeline events
- `COMPLETED` state after resume
- readiness or metrics evidence

## Appendix H: Architecture Diagrams

Diagram source files live in `docs/report/diagrams/`. Available diagram
categories include:

- system context
- container/deployment
- backend layered architecture
- LangGraph workflow
- approval/resume lifecycle
- RAG ingestion/retrieval
- event streaming
- CI/deployment flow

## Appendix I: Final Demo Script And Q&A

Recommended source references:

- `docs/final/FINAL_DEMO_SCRIPT.md`
- `docs/final/DEMO_TIMING_PLAN.md`
- `docs/final/DEMO_FAILURE_RECOVERY.md`
- `docs/final/DEFENSE_QA_BANK.md`

Suggested appendix content:

- final board-demo script
- 8-12 minute timing plan
- 3-5 minute fallback summary
- failure recovery notes
- defense Q&A bank

## Appendix J: Release Checklist And Final Gate

Recommended source references:

- `docs/final/RELEASE_CHECKLIST.md`
- `docs/final/FINAL_QUALITY_GATE.md`
- `docs/final/FINAL_RELEASE_NOTES.md`
- `scripts/final/final-quality-gate.sh`

Suggested appendix content:

- final repository release checklist
- final quality gate command list
- no-secret scan and unsupported-claim scan
- final release scope summary
- intentionally deferred capabilities

## Appendix K: Known Limitations And Future Work

Recommended source reference:

- `docs/report/LIMITATIONS_AND_FUTURE_WORK.md`

Suggested appendix content:

- deferred enterprise capabilities
- production-hardening gaps
- no-key/real-provider evaluation boundary
- security and operations follow-up list
