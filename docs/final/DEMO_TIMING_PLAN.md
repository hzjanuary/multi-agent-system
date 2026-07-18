# Demo Timing Plan

This plan keeps the final presentation inside an 8-12 minute target while
preserving a shorter 3-5 minute fallback if live demo time is reduced.

## 8-12 Minute Live Demo

| Time | Segment | Speaker Goal | Demo Evidence |
|---|---|---|---|
| 0:00-1:00 | Pitch and problem | State the procurement problem and one-sentence solution. | Title slide or opening screen. |
| 1:00-2:30 | Architecture overview | Explain Next.js, FastAPI, LangGraph, Postgres, Redis, Qdrant, MinIO, optional LLMs, RAG, and events. | `docs/report/diagrams/README.md` and selected Mermaid diagrams. |
| 2:30-3:30 | Workflow dashboard | Show authenticated workflow dashboard and procurement workflow detail. | Frontend dashboard/list/detail. |
| 3:30-4:30 | Run to approval | Run workflow and verify `WAITING_APPROVAL`. | Workflow status and event timeline. |
| 4:30-5:45 | RAG evidence | If enabled, show citations and knowledge search/catalog. If disabled, explain empty evidence state. | Evidence panel, knowledge search, document catalog. |
| 5:45-7:00 | Human approval | Submit approval and show approval history. | Approval panel/history and event timeline. |
| 7:00-7:30 | Resume | Resume workflow and verify `COMPLETED`. | Resume action/result and completed timeline. |
| 7:30-9:00 | Operations proof | Explain deployment docs, health/readiness, metrics, CI, and smoke script. | `/ready`, metrics endpoint, smoke script, CI/local gate references. |
| 9:00-10:30 | Evaluation and limitations | Explain evidence plan, no-key reproducibility, and honest limitations. | `docs/final/EVALUATION_MATRIX.md`, limitations docs. |
| 10:30-12:00 | Q&A transition | Summarize contribution and invite questions. | `docs/final/DEFENSE_QA_BANK.md`. |

## 3-5 Minute Fallback Summary

Use this if the live environment is unavailable or presentation time is cut.

| Time | Segment | Script |
|---|---|---|
| 0:00-0:30 | Pitch | Enterprise Multi-Agent OS automates procurement review by coordinating specialized workflow stages, human approval, RAG evidence, and operational proof in one auditable system. |
| 0:30-1:30 | Architecture | The dashboard is Next.js, the API is FastAPI, LangGraph controls the runtime, Postgres stores workflow/audit state, Redis streams events, Qdrant retrieves knowledge chunks, and MinIO stores demo source objects. |
| 1:30-3:00 | Demo highlight | The workflow runs to `WAITING_APPROVAL`, shows timeline and optional evidence, requires manager approval, then resumes through `/resume` to `COMPLETED` without sending real email. |
| 3:00-4:00 | Evaluation/deployment | Evidence is captured through CI/local gates, the E2E validation script, Docker Compose production-demo config, health/readiness, metrics, and screenshot checklists. |
| 4:00-5:00 | Conclusion | The project demonstrates controlled multi-agent orchestration with human governance, deterministic no-key reproducibility, and production-demo packaging. Deferred work includes enterprise SSO, secret vault, cloud automation, upload UI, OCR, and production notifications. |

## Timing Control Notes

- If the workflow takes longer than expected, skip knowledge search and show
  the evidence panel only.
- If RAG is disabled, use the empty evidence panel as proof that the UI does
  not fabricate citations.
- If operations proof runs long, show the smoke script and CI docs instead of
  live metrics.
- If Q&A starts early, move directly to the closing summary and use the Q&A
  bank for structured answers.

