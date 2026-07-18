# Screenshot Checklist

This checklist plans final screenshot capture for the graduation report and
demo evidence package. It does not capture screenshots and does not create
image files.

## Purpose And Rules

Screenshots should prove the user-visible board-demo flow:

- authentication
- workflow dashboard and detail
- runtime to `WAITING_APPROVAL`
- timeline visibility
- approval and resume
- RAG evidence and knowledge search/catalog when enabled
- readiness, metrics, CI, and production-demo smoke evidence

Capture only the visible UI or bounded command summaries needed for the report.
Do not capture bearer tokens, JWTs, cookies, API keys, real secrets, real
customer data, raw prompts, raw provider payloads, raw embeddings, raw vector
payloads, or chain-of-thought.

## Naming Convention

Use stable, ordered filenames:

```text
docs/final/screenshots/<NN>-<area>-<short-description>.png
```

Examples:

```text
docs/final/screenshots/01-auth-login-page.png
docs/final/screenshots/06-approval-panel-waiting.png
docs/final/screenshots/12-rag-evidence-populated.png
```

Use lowercase words separated by hyphens. Keep filenames descriptive but short.

## Storage Recommendation

- Store reviewed screenshots under `docs/final/screenshots/` only after TASK
  015.4.
- Do not commit screenshots that contain sensitive hostnames, tokens, cookies,
  real customer data, real provider keys, or secret-bearing terminal output.
- Redact public-submission screenshots when needed.
- Demo credentials may appear only when clearly marked local-demo/board-demo
  and not production accounts.
- Keep raw browser captures out of the repository until reviewed.

## Required Screenshots

| ID | Filename | Page/command | Purpose | Required/optional | Capture status | Notes/redaction required |
| --- | --- | --- | --- | --- | --- | --- |
| SS-01 | `01-auth-login-page.png` | Frontend `/login` | Show authentication entry point | Required | Pending | No tokens/cookies |
| SS-02 | `02-workflow-dashboard-list.png` | Frontend dashboard/workflow list | Show seeded workflows and navigation | Required | Pending | Use local-demo data only |
| SS-03 | `03-workflow-detail-before-run.png` | Workflow detail | Show run panel, summary, timeline/evidence areas before run | Required | Pending | Avoid raw payload expansion |
| SS-04 | `04-workflow-waiting-approval.png` | Workflow detail after `/run` | Prove `/run` stops at `WAITING_APPROVAL` | Required | Pending | Local-demo workflow only |
| SS-05 | `05-event-timeline-after-run.png` | Workflow event timeline | Show persisted/runtime events after run | Required | Pending | No fake streamed events |
| SS-06 | `06-approval-panel-waiting.png` | Workflow approval panel | Show approve/reject/request changes actions | Required | Pending | Manager/Admin session |
| SS-07 | `07-approval-decision-submitted.png` | Workflow approval result | Show successful approval result | Required | Pending | Bounded comment only |
| SS-08 | `08-approval-history.png` | Approval history panel | Show final approval history row | Required | Pending | Local-demo actor only |
| SS-09 | `09-resume-action-result.png` | Workflow detail resume panel | Show explicit resume action/result | Required | Pending | Confirm `/resume`, not `/run` |
| SS-10 | `10-workflow-completed-state.png` | Workflow detail after resume | Show final `COMPLETED` state | Required | Pending | No real email sending claim |
| SS-11 | `11-evidence-empty-state.png` | Evidence panel with RAG disabled/no evidence | Show honest empty state | Required | Pending | No fake evidence |
| SS-12 | `12-rag-evidence-populated.png` | Evidence panel with `RAG_ENABLED=true` | Show citation cards with source/excerpt/score | Required | Pending | Bounded excerpts only |
| SS-13 | `13-knowledge-search-results.png` | Knowledge search panel | Show safe search results after ingestion | Required | Pending | No raw vector payloads |
| SS-14 | `14-knowledge-document-catalog.png` | Knowledge document list | Show demo document catalog metadata | Required | Pending | No full document dump |
| SS-15 | `15-live-timeline-behavior.png` | Workflow timeline during live run | Show live/backlog timeline behavior if practical | Required | Pending | No fake streamed events |
| SS-16 | `16-readiness-ready-result.png` | `/ready` command/browser result | Show dependency readiness evidence | Required | Pending | Redact hostnames if needed |
| SS-17 | `17-metrics-endpoint-summary.png` | `/api/v1/observability/metrics` | Show safe bounded metrics evidence | Required | Pending | Do not capture token/header |
| SS-18 | `18-production-compose-ps-or-smoke.png` | Compose `ps` or smoke script output | Show production-demo stack/smoke evidence | Required | Pending | No env file contents |
| SS-19 | `19-ci-local-gates-summary.png` | CI run or `scripts/ci/all-gates.sh` summary | Show quality gate evidence | Required | Pending | Summaries only |

## Optional Screenshots

| ID | Filename | Page/command | Purpose | Required/optional | Capture status | Notes/redaction required |
| --- | --- | --- | --- | --- | --- | --- |
| SS-20 | `20-viewer-forbidden-approval.png` | Viewer workflow detail/API result | Show Viewer mutation denial | Optional | Pending | No token/header |
| SS-21 | `21-approval-conflict-error.png` | Duplicate/invalid approval attempt | Show understandable 409 conflict | Optional | Pending | Local-demo only |
| SS-22 | `22-resume-conflict-error.png` | Invalid resume attempt | Show understandable 409 conflict | Optional | Pending | Local-demo only |
| SS-23 | `23-no-key-provider-setup-doc.png` | LLM/local demo docs | Show no-key mode documentation | Optional | Pending | Docs only |
| SS-24 | `24-deployment-runbook.png` | Deployment runbook | Show production-demo operator guidance | Optional | Pending | No env file values |

## Evidence Mapping

| Evaluation dimension | Screenshot IDs |
| --- | --- |
| Functional completeness | SS-02, SS-03, SS-04, SS-10 |
| Backend API correctness | SS-04, SS-07, SS-09, SS-16, SS-17 |
| Authentication and RBAC | SS-01, SS-06, SS-20 |
| Workflow orchestration correctness | SS-04, SS-05, SS-10, SS-15 |
| Event streaming and timeline correctness | SS-05, SS-15 |
| Human approval and resume correctness | SS-06, SS-07, SS-08, SS-09, SS-10 |
| LLM provider abstraction safety | SS-23 |
| RAG/document knowledge grounding correctness | SS-11, SS-12, SS-13, SS-14 |
| Frontend usability and demo flow | SS-01 through SS-15 |
| Demo dataset and deterministic no-key behavior | SS-02, SS-04, SS-10, SS-23 |
| Production-demo deployment readiness | SS-18 |
| Readiness/health and observability | SS-16, SS-17 |
| CI/local quality gates | SS-19 |
| Security and safety boundaries | SS-20, SS-21, SS-22, SS-23 |
| Documentation/report readiness | SS-23, SS-24 |

## Capture Notes

- Pair screenshots with `docs/final/E2E_EVIDENCE_CAPTURE_TEMPLATE.md` notes.
- Record the commit SHA and environment profile before capture.
- Prefer browser UI screenshots for user-facing proof and terminal screenshots
  only for bounded validation summaries.
- Redact URLs or hostnames when public submission rules require it.
- Do not edit screenshots to imply a state that was not actually captured.
