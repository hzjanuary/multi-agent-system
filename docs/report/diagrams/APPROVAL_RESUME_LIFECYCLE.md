# Approval And Resume Lifecycle Diagram

```mermaid
stateDiagram-v2
    [*] --> WAITING_APPROVAL

    WAITING_APPROVAL --> WAITING_APPROVAL: request_changes\nnon-final
    WAITING_APPROVAL --> APPROVED: approve\nfinal
    WAITING_APPROVAL --> REJECTED: reject with comment\nfinal

    APPROVED --> GENERATING_EMAIL: /resume allowed
    GENERATING_EMAIL --> COMPLETED: email preview prepared

    APPROVED --> APPROVED: duplicate final decision blocked
    REJECTED --> REJECTED: approval mutation blocked
    COMPLETED --> COMPLETED: approval/resume mutation blocked
    FAILED --> FAILED: terminal mutation blocked
    CANCELLED --> CANCELLED: terminal mutation blocked

    REJECTED --> [*]
    COMPLETED --> [*]
```

This diagram shows approval decision semantics. Request changes is non-final
and leaves the workflow waiting. Approve and reject are final. Resume is only
allowed from `APPROVED` with a final approve record.

It matters for the report because it captures the lifecycle rules that protect
high-stakes procurement decisions and prevent duplicate or terminal-state
mutations.

Related docs: `.ai/specs/SPEC-012-human-approval-and-resume/spec.md`,
`docs/demo/DEMO_RUNBOOK.md`, and `docs/report/TECHNICAL_NARRATIVE.md`.
