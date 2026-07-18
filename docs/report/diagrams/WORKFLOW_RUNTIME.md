# Workflow Runtime Diagram

```mermaid
flowchart TB
    Create["Create/list workflow\nREST APIs"]
    Created["CREATED"]
    Run["POST /api/v1/workflows/{id}/run"]
    Planner["planner stage"]
    Retrieval["retrieval stage"]
    Quotation["quotation/calculator stage"]
    Compliance["compliance stage"]
    Validation["validation/finance stage"]
    ApprovalPackage["approval package stage"]
    Waiting["WAITING_APPROVAL"]
    Human["Human approval boundary"]
    Approve["approve decision"]
    Resume["POST /api/v1/workflows/{id}/resume"]
    EmailPrep["email_preparation preview stage"]
    Completed["COMPLETED"]
    Reject["reject decision"]
    Rejected["REJECTED"]
    RequestChanges["request_changes decision"]

    Create --> Created
    Created --> Run
    Run --> Planner --> Retrieval --> Quotation --> Compliance --> Validation
    Validation --> ApprovalPackage --> Waiting
    Waiting --> Human
    Human --> RequestChanges --> Waiting
    Human --> Approve --> Resume --> EmailPrep --> Completed
    Human --> Reject --> Rejected
```

This diagram shows the implemented runtime flow. `/run` executes the
pre-approval stages and stops at `WAITING_APPROVAL`. Post-approval continuation
is explicit through `/resume`, which prepares an email preview and completes
the workflow.

It matters for the report because it demonstrates the human-in-the-loop safety
boundary and makes clear that `/run` does not auto-resume.

Related docs: `.ai/specs/SPEC-006-langgraph-runtime/spec.md`,
`.ai/specs/SPEC-012-human-approval-and-resume/spec.md`, and
`docs/final/E2E_DEMO_VALIDATION.md`.
