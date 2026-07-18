"use client";

import { useEffect, useState } from "react";

import { KnowledgeDocumentList } from "@/components/knowledge/knowledge-document-list";
import { KnowledgeSearchPanel } from "@/components/knowledge/knowledge-search-panel";
import { WorkflowAgentActivityPanel } from "@/components/workflows/workflow-agent-activity-panel";
import { WorkflowApprovalHistory } from "@/components/workflows/workflow-approval-history";
import { WorkflowApprovalPanel } from "@/components/workflows/workflow-approval-panel";
import { WorkflowDetail } from "@/components/workflows/workflow-detail";
import { WorkflowEvidencePanel } from "@/components/workflows/workflow-evidence-panel";
import { WorkflowEventTimeline } from "@/components/workflows/workflow-event-timeline";
import { WorkflowNextStepGuide } from "@/components/workflows/workflow-next-step-guide";
import { workflowErrorMessage } from "@/components/workflows/workflow-list-view";
import { WorkflowRunPanel } from "@/components/workflows/workflow-run-panel";
import {
  getWorkflow,
  getWorkflowApprovalHistory,
  listWorkflowEvents,
} from "@/lib/api/workflows";
import { getAccessToken } from "@/lib/auth/session";
import type {
  ApprovalHistoryResponse,
  WorkflowEvent,
  WorkflowState,
} from "@/lib/api/types";

type DetailState =
  | { status: "loading" }
  | { status: "login-required" }
  | { status: "error"; message: string }
  | {
      status: "ready";
      workflow: WorkflowState;
      events: WorkflowEvent[];
      approvalHistory: ApprovalHistoryResponse;
      token: string;
    };

interface WorkflowDetailViewProps {
  workflowId: string;
}

export function WorkflowDetailView({ workflowId }: WorkflowDetailViewProps) {
  const [state, setState] = useState<DetailState>({ status: "loading" });

  useEffect(() => {
    let isMounted = true;
    const token = getAccessToken();

    if (!token) {
      setState({ status: "login-required" });
      return;
    }

    loadWorkflowDetail(workflowId, token)
      .then(({ workflow, events, approvalHistory }) => {
        if (isMounted) {
          setState({
            status: "ready",
            workflow,
            events,
            approvalHistory,
            token,
          });
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setState({ status: "error", message: workflowErrorMessage(error) });
        }
      });

    return () => {
      isMounted = false;
    };
  }, [workflowId]);

  if (state.status === "loading") {
    return <DetailStatePanel title="Loading workflow detail" />;
  }

  if (state.status === "login-required") {
    return (
      <DetailStatePanel
        title="Login required"
        description="Sign in before loading this workflow from the backend."
      />
    );
  }

  if (state.status === "error") {
    return (
      <DetailStatePanel
        title="Unable to load workflow"
        description={state.message}
      />
    );
  }

  async function refreshWorkflowDetail() {
    const token = getAccessToken();
    if (!token) {
      setState({ status: "login-required" });
      return;
    }

    const { workflow, events, approvalHistory } = await loadWorkflowDetail(
      workflowId,
      token,
    );
    setState({ status: "ready", workflow, events, approvalHistory, token });
  }

  return (
    <div className="grid gap-6">
      <WorkflowNextStepGuide status={state.workflow.status} />
      <WorkflowAgentActivityPanel
        approvalHistory={state.approvalHistory}
        events={state.events}
        workflow={state.workflow}
      />
      <WorkflowRunPanel
        workflowId={state.workflow.workflow_id}
        workflowStatus={state.workflow.status}
        onRunCompleted={refreshWorkflowDetail}
      />
      <WorkflowApprovalPanel
        approvalHistory={state.approvalHistory}
        workflow={state.workflow}
        onApprovalChanged={refreshWorkflowDetail}
      />
      <WorkflowDetail workflow={state.workflow} />
      <WorkflowEvidencePanel workflow={state.workflow} events={state.events} />
      <WorkflowApprovalHistory history={state.approvalHistory} />
      <WorkflowEventTimeline
        workflowId={state.workflow.workflow_id}
        persistedEvents={state.events}
      />
      <section className="grid gap-6">
        <div>
          <h2 className="text-lg font-semibold">Knowledge tools</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Advanced RAG/search checks use existing knowledge endpoints. These
            panels do not fabricate evidence for the workflow above.
          </p>
        </div>
        <KnowledgeSearchPanel token={state.token} />
        <KnowledgeDocumentList token={state.token} />
      </section>
    </div>
  );
}

async function loadWorkflowDetail(workflowId: string, token: string) {
  const [workflowResponse, eventResponse, approvalHistory] = await Promise.all([
    getWorkflow(workflowId, { token }),
    listWorkflowEvents(workflowId, { token }, { limit: 25, offset: 0 }),
    getWorkflowApprovalHistory(workflowId, { token }),
  ]);

  return {
    workflow: workflowResponse.workflow,
    events: eventResponse.events,
    approvalHistory,
  };
}

function DetailStatePanel({
  title,
  description = "This view will update after the backend response is available.",
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
      <h2 className="text-base font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </div>
  );
}
