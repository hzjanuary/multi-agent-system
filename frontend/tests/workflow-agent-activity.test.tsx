import React, { act, type ReactElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";

import { WorkflowAgentActivityPanel } from "@/components/workflows/workflow-agent-activity-panel";
import type {
  ApprovalHistoryResponse,
  WorkflowEvent,
  WorkflowState,
  WorkflowStatus,
} from "@/lib/api/types";

let root: Root | null = null;
let container: HTMLDivElement | null = null;

afterEach(() => {
  if (root) {
    act(() => {
      root?.unmount();
    });
  }
  root = null;
  container?.remove();
  container = null;
});

describe("workflow agent activity panel", () => {
  it("shows CREATED workflows as not started and prompts Run", async () => {
    await render(<WorkflowAgentActivityPanel workflow={sampleWorkflow("CREATED")} />);

    expect(document.body.textContent).toContain("Agent activity");
    expect(document.body.textContent).toContain("Planner Agent");
    expect(document.body.textContent).toContain("Email Preview Agent");
    expect(document.body.textContent).toContain("Not started");
    expect(document.body.textContent).toContain(
      "Click Run workflow to start agent execution.",
    );
  });

  it("shows pre-approval progress and the human approval boundary", async () => {
    await render(
      <WorkflowAgentActivityPanel
        events={[stageEvent("validation")]}
        workflow={{
          ...sampleWorkflow("WAITING_APPROVAL"),
          stage_outputs: {
            planner: stageOutput("Planner completed."),
            retrieval: stageOutput("Retrieval completed."),
            quotation: stageOutput("Calculator completed."),
            compliance: stageOutput("Compliance completed."),
            validation: stageOutput("Validation completed."),
            approval: stageOutput("Approval package prepared."),
          },
        }}
      />,
    );

    expect(document.body.textContent).toContain("Planner completed.");
    expect(document.body.textContent).toContain("Human Approval");
    expect(document.body.textContent).toContain("Waiting for approval");
    expect(document.body.textContent).toContain("Email Preview Agent");
    expect(document.body.textContent).toContain("Blocked until approval");
  });

  it("shows approved workflows as resume-ready for email preview", async () => {
    await render(
      <WorkflowAgentActivityPanel
        approvalHistory={approvalHistory("workflow-1", "approve", true)}
        workflow={sampleWorkflow("APPROVED")}
      />,
    );

    expect(document.body.textContent).toContain("Human Approval");
    expect(document.body.textContent).toContain("Completed");
    expect(document.body.textContent).toContain("Email Preview Agent");
    expect(document.body.textContent).toContain("Ready to run via Resume");
    expect(document.body.textContent).toContain(
      "Click Resume workflow to run the email preview stage",
    );
  });

  it("shows completed workflows with post-resume email preview completion", async () => {
    await render(
      <WorkflowAgentActivityPanel
        events={[stageEvent("email_preparation")]}
        workflow={{
          ...sampleWorkflow("COMPLETED"),
          email: {
            summary:
              "Deterministic email preparation placeholder recorded email stage without sending email.",
            email_sent: false,
          },
        }}
      />,
    );

    expect(document.body.textContent).toContain("Email Preview Agent");
    expect(document.body.textContent).toContain("Completed after resume");
    expect(document.body.textContent).toContain(
      "Deterministic email preparation placeholder recorded email stage without sending email.",
    );
  });

  it("shows rejected workflows as terminal at the human approval boundary", async () => {
    await render(
      <WorkflowAgentActivityPanel
        approvalHistory={approvalHistory("workflow-1", "reject", false)}
        workflow={sampleWorkflow("REJECTED")}
      />,
    );

    expect(document.body.textContent).toContain("Human Approval");
    expect(document.body.textContent).toContain("Rejected");
    expect(document.body.textContent).toContain(
      "Rejected workflows are terminal",
    );
    expect(document.body.textContent).toContain("Email Preview Agent");
    expect(document.body.textContent).toContain("Blocked until approval");
  });

  it("does not render raw prompts, provider payloads, embeddings, vectors, or tokens", async () => {
    await render(
      <WorkflowAgentActivityPanel
        events={[
          {
            ...stageEvent("compliance"),
            payload: {
              stage: "compliance",
              raw_prompt: "never show raw prompt",
              provider_payload: { value: "never show provider payload" },
              embedding_vector: [0.123, 0.456],
              access_token: "never-show-token",
            },
          },
        ]}
        workflow={{
          ...sampleWorkflow("WAITING_APPROVAL"),
          runtime_context: {
            completed_stages: ["compliance"],
            raw_prompt: "hidden runtime prompt",
            jwt: "hidden-runtime-token",
          },
          stage_outputs: {
            compliance: {
              summary: "Safe compliance summary.",
              provider_payload: { unsafe: true },
              vector_payload: [0.1, 0.2],
              secret: "hidden-secret",
            },
          },
        }}
      />,
    );

    expect(document.body.textContent).toContain("Safe compliance summary.");
    expect(document.body.textContent).not.toContain("never show raw prompt");
    expect(document.body.textContent).not.toContain(
      "never show provider payload",
    );
    expect(document.body.textContent).not.toContain("hidden runtime prompt");
    expect(document.body.textContent).not.toContain("hidden-secret");
    expect(document.body.textContent).not.toContain("never-show-token");
    expect(document.body.textContent).not.toContain("0.123");
    expect(document.body.textContent).not.toContain("0.1");
  });
});

async function render(element: ReactElement) {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);

  await act(async () => {
    root?.render(element);
  });
  await flushEffects();
}

async function flushEffects() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

function sampleWorkflow(status: WorkflowStatus): WorkflowState {
  return {
    workflow_id: "workflow-1",
    workflow_type: "procurement_quotation",
    domain: "it_equipment",
    status,
    request: { raw_text: "Need 50 standard laptops" },
    metadata: { state_version: 1 },
    customer: { name: "Acme Manufacturing Group" },
    items: [{ name: "Laptop", quantity: 50 }],
    current_step: status === "CREATED" ? null : "approval",
    retry_count: 0,
    created_at: "2026-07-13T10:00:00Z",
    updated_at: "2026-07-13T10:00:00Z",
  };
}

function stageOutput(summary: string) {
  return {
    status: "completed",
    summary,
  };
}

function stageEvent(stage: string): WorkflowEvent {
  return {
    event_id: `event-${stage}`,
    workflow_id: "workflow-1",
    event_type: "workflow.node.completed",
    agent_name: stage,
    status: "completed",
    message: `${stage} completed`,
    payload: { stage },
    created_at: "2026-07-13T10:01:00Z",
  };
}

function approvalHistory(
  workflowId: string,
  decision: "approve" | "reject",
  canResume: boolean,
): ApprovalHistoryResponse {
  return {
    workflow_id: workflowId,
    approvals: [
      {
        decision_id: "decision-1",
        workflow_id: workflowId,
        decision,
        actor_id: "user-1",
        actor_email: "manager@example.test",
        actor_roles: ["manager"],
        comment:
          decision === "reject"
            ? "Rejected workflows are terminal."
            : "Approved for deterministic resume.",
        decided_at: "2026-07-13T10:05:00Z",
        previous_status: "WAITING_APPROVAL",
        next_status: decision === "approve" ? "APPROVED" : "REJECTED",
        request_id: null,
        metadata: {},
      },
    ],
    has_final_decision: true,
    can_resume: canResume,
  };
}
