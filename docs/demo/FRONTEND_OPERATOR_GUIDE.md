# Frontend Operator Guide

## Purpose

This one-page guide is for evaluators who want to operate the demo from the
frontend without reading the full runbook first.

## Start Here

Open the frontend and go to:

```text
/demo
```

The Demo Guide page explains the lifecycle, local-demo accounts, seeded
workflow choices, optional RAG behavior, and the next action to take.

For live observation of workflows created by an external local demo channel,
open:

```text
/agent-monitor
```

The optional Telegram inbound bridge is documented in
`docs/demo/TELEGRAM_INBOUND_DEMO.md`.

The `/demo` command center also includes a **Telegram Live Demo** section with
the exact phone message, local bridge command, Agent Monitor link, and safety
notes. Use it when you want to show a customer request arriving from Telegram,
being converted into a workflow, running to `WAITING_APPROVAL`, and then being
approved/resumed through the normal frontend UI.

The Telegram bridge accepts the English board-demo request and bounded
Vietnamese laptop RFQ messages such as:

```text
tôi muốn mua 50 cái máy tính xách tay doanh nhân tiêu chuẩn có cài sẵn office 365
```

Greeting-only messages such as `xin chào` return an example prompt and do not
create a workflow.

## Login Account

Use the Manager account for the main demo:

```text
manager@example.test
DemoPassword123!
```

Other local-demo accounts are available for role checks:

```text
admin@example.test
sales@example.test
viewer@example.test
```

All use `DemoPassword123!`. These credentials are local-demo/board-demo only and
must not be used as production accounts.

## Seeded Workflow Choices

Use these seeded workflow links from `/demo`, `/dashboard`, or `/workflows`:

| Demo path | Workflow ID | Starting status | Use when |
| --- | --- | --- | --- |
| Full demo | `dc5e7963-c2a4-5ad6-8f70-0741431597f0` | CREATED | You want to run the full workflow from the beginning. |
| Fast demo | `b0111d45-aff5-5b86-9ffd-9417704c9bab` | WAITING_APPROVAL | You want to focus on approval and resume. |
| Resume-only | `e1771f90-a85e-5684-98d1-7dd0458a4e89` | APPROVED | You want to show resume without first approving. |
| Completed history | `6b99fd38-1ecf-5213-8d69-43abcca20856` | COMPLETED | You want read-only proof of final state and timeline. |

## Status Meanings

| Status | What it means | What to click next |
| --- | --- | --- |
| CREATED | The workflow has not run yet. | Click **Run workflow**. |
| WAITING_APPROVAL | `/run` stopped at the human approval boundary. | Review details/evidence/events, then approve. |
| APPROVED | A final approval decision exists. | Click **Resume workflow**. |
| COMPLETED | The workflow completed after resume. | Review final state, history, evidence, and timeline. |
| REJECTED | The workflow was rejected and is terminal. | Review approval history and events. |
| FAILED/CANCELLED | The workflow is terminal or non-happy-path. | Review error details and events. |

## RAG Evidence

RAG is disabled by default. Evidence/citations appear only when:

```text
RAG_ENABLED=true
```

and demo knowledge ingestion has been run explicitly:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

If evidence is empty, that is expected when RAG is disabled, knowledge has not
been ingested, or the selected workflow was not run with RAG enabled. The
frontend does not fabricate evidence.

## If the Workflow Is Already Completed

Use the completed workflow as read-only proof, or return to `/demo` and choose
the CREATED workflow for a full run. Do not call `/run` again on completed
workflows; use the timeline and approval history as the evidence.

## If Login Fails

1. Confirm the backend is running.
2. Confirm the demo seed was run explicitly.
3. Use the Manager local-demo account exactly as shown above.
4. Check `docs/demo/DEMO_RUNBOOK.md` for the full setup flow.
