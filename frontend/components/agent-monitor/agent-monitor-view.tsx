"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { WorkflowAgentActivityPanel } from "@/components/workflows/workflow-agent-activity-panel";
import { WorkflowEventTimeline } from "@/components/workflows/workflow-event-timeline";
import { WorkflowNextStepGuide } from "@/components/workflows/workflow-next-step-guide";
import { WorkflowStatusBadge } from "@/components/workflows/workflow-status-badge";
import { workflowErrorMessage } from "@/components/workflows/workflow-list-view";
import { demoWorkflows } from "@/lib/demo";
import {
  getWorkflow,
  getWorkflowApprovalHistory,
  listWorkflowEvents,
  listWorkflows,
} from "@/lib/api/workflows";
import { getAccessToken } from "@/lib/auth/session";
import type {
  ApprovalHistoryResponse,
  WorkflowEvent,
  WorkflowState,
} from "@/lib/api/types";

type MonitorState =
  | { status: "loading" }
  | { status: "login-required" }
  | { status: "error"; message: string }
  | { status: "recent"; workflows: WorkflowState[] }
  | {
      status: "workflow";
      workflow: WorkflowState;
      events: WorkflowEvent[];
      approvalHistory: ApprovalHistoryResponse;
    };

interface AgentMonitorViewProps {
  workflowId?: string;
}

export function AgentMonitorView({ workflowId }: AgentMonitorViewProps) {
  const [state, setState] = useState<MonitorState>({ status: "loading" });

  useEffect(() => {
    let isMounted = true;
    const token = getAccessToken();

    if (!token) {
      setState({ status: "login-required" });
      return;
    }

    const load = workflowId
      ? loadWorkflowMonitor(workflowId, token)
      : listWorkflows({ token }, { limit: 8, offset: 0 }).then((response) => ({
          status: "recent" as const,
          workflows: response.workflows,
        }));

    load
      .then((nextState) => {
        if (isMounted) {
          setState(nextState);
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
    return <MonitorStatePanel title="Loading agent monitor" />;
  }

  if (state.status === "login-required") {
    return (
      <MonitorStatePanel
        title="Login required"
        description="Sign in before observing workflow agent activity."
      />
    );
  }

  if (state.status === "error") {
    return (
      <MonitorStatePanel
        title="Unable to load agent monitor"
        description={state.message}
      />
    );
  }

  if (state.status === "recent") {
    return <RecentWorkflowMonitor workflows={state.workflows} />;
  }

  return (
    <WorkflowMonitor
      approvalHistory={state.approvalHistory}
      events={state.events}
      workflow={state.workflow}
    />
  );
}

async function loadWorkflowMonitor(workflowId: string, token: string) {
  const [workflowResponse, eventResponse, approvalHistory] = await Promise.all([
    getWorkflow(workflowId, { token }),
    listWorkflowEvents(workflowId, { token }, { limit: 25, offset: 0 }),
    getWorkflowApprovalHistory(workflowId, { token }),
  ]);

  return {
    status: "workflow" as const,
    workflow: workflowResponse.workflow,
    events: eventResponse.events,
    approvalHistory,
  };
}

function RecentWorkflowMonitor({ workflows }: { workflows: WorkflowState[] }) {
  return (
    <div className="grid gap-6">
      <ObserverModeIntro />
      <section className="ops-panel-strong p-5 md:p-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="ops-kicker">Observer queue</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Recent workflows
            </h2>
          </div>
          <Link className="ops-button-secondary" href="/workflows">
            Open workflow queue
          </Link>
        </div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Select a workflow to observe live stage progress, approval boundary,
          and persisted events. This page reads existing workflow records only.
        </p>
        {workflows.length === 0 ? (
          <p className="mt-5 text-sm leading-6 text-muted-foreground">
            No recent workflows are available yet.
          </p>
        ) : (
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            {workflows.map((workflow) => (
              <RecentWorkflowCard workflow={workflow} key={workflow.workflow_id} />
            ))}
          </div>
        )}
      </section>
      <section className="ops-panel p-5 md:p-6">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="ops-kicker">Secondary demo anchors</p>
            <h2 className="mt-2 text-lg font-semibold">Seeded demo shortcuts</h2>
          </div>
          <span className="ops-chip">Static demo records</span>
        </div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Use these stable workflows when you need a predictable board-demo
          state. Recent Telegram-created workflows should be observed from the
          queue above.
        </p>
        <div className="mt-5 grid gap-4 lg:grid-cols-4">
          {demoWorkflows.map((workflow) => (
            <MonitorShortcutCard
              href={`/agent-monitor?workflowId=${workflow.workflowId}`}
              key={workflow.workflowId}
              label={workflow.title}
              status={workflow.status}
              subtitle={workflow.shortTitle}
              text={workflow.nextStep}
              workflowId={workflow.workflowId}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function WorkflowMonitor({
  workflow,
  events,
  approvalHistory,
}: {
  workflow: WorkflowState;
  events: WorkflowEvent[];
  approvalHistory: ApprovalHistoryResponse;
}) {
  return (
    <div className="grid gap-6">
      <ObserverModeIntro />
      <section className="ops-panel-strong p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="ops-kicker">
              Observed workflow
            </p>
            <h2 className="mt-2 break-words text-xl font-semibold tracking-tight">
              {workflow.workflow_id}
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Monitor this workflow without changing backend state. Use the
              full workflow detail route for run, approval, resume, evidence,
              and catalog panels.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <WorkflowStatusBadge status={workflow.status} />
            <Link
              className="ops-button-primary"
              href={`/workflows/${workflow.workflow_id}`}
            >
              Open full detail
            </Link>
            <Link
              className="ops-button-secondary"
              href={`/workflows/${workflow.workflow_id}`}
            >
              Approve / resume
            </Link>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MonitorFact label="Status" value={workflow.status} emphasis />
          <MonitorFact
            label="Domain"
            value={workflow.domain ?? "Not specified"}
          />
          <MonitorFact label="Type" value={workflow.workflow_type} />
          <MonitorFact
            label="Current step"
            value={workflow.current_step ?? "Not started"}
          />
        </div>
      </section>
      <WorkflowNextStepGuide status={workflow.status} />
      <WorkflowAgentActivityPanel
        approvalHistory={approvalHistory}
        events={events}
        workflow={workflow}
      />
      <WorkflowEventTimeline
        workflowId={workflow.workflow_id}
        persistedEvents={events}
      />
    </div>
  );
}

function ObserverModeIntro() {
  return (
    <section className="ops-panel-strong p-5 md:p-6">
      <p className="ops-kicker">
        Live demo observer mode
      </p>
      <h2 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight md:text-3xl">
        Observe the workflow execution path in one console.
      </h2>
      <div className="mt-4 grid gap-3 text-sm leading-6 text-muted-foreground lg:grid-cols-2">
        <p>
          External requests can create workflows, including channels such as a
          Telegram integration when configured outside this frontend. This page
          lets evaluators select a recent workflow or a seeded demo workflow and
          observe execution.
        </p>
        <p>
          Agents are deterministic workflow stages in no-key mode. The UI shows
          bounded operational evidence, not chain-of-thought, and human approval
          is still required before resume.
        </p>
      </div>
    </section>
  );
}

function MonitorShortcutCard({
  href,
  label,
  status,
  subtitle,
  text,
  workflowId,
}: {
  href: string;
  label: string;
  status: string;
  subtitle: string;
  text: string;
  workflowId: string;
}) {
  return (
    <Link
      className="ops-card-link p-4"
      href={href}
    >
      <p className="ops-kicker">{label}</p>
      <h3 className="mt-2 text-base font-semibold">{subtitle}</h3>
      <p className="mt-2 inline-flex rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">{status}</p>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{text}</p>
      <p className="mt-3 break-words text-xs leading-5 text-muted-foreground">
        {workflowId}
      </p>
    </Link>
  );
}

function RecentWorkflowCard({ workflow }: { workflow: WorkflowState }) {
  return (
    <Link
      className="ops-card-link group p-4"
      href={`/agent-monitor?workflowId=${workflow.workflow_id}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="ops-kicker">Workflow</p>
          <h3 className="mt-1 text-base font-semibold">
            {workflow.workflow_type}
          </h3>
          <p className="mt-2 break-all font-mono text-xs leading-5 text-muted-foreground">
            {workflow.workflow_id}
          </p>
        </div>
        <WorkflowStatusBadge status={workflow.status} />
      </div>
      <div className="mt-4 grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
        <MonitorFact label="Domain" value={workflow.domain ?? "Not specified"} />
        <MonitorFact
          label="Current step"
          value={workflow.current_step ?? "Not started"}
        />
      </div>
      <p className="mt-4 text-sm font-semibold text-primary group-hover:underline">
        Observe in Agent Monitor
      </p>
    </Link>
  );
}

function MonitorFact({
  label,
  value,
  emphasis = false,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div className="rounded-md border border-border/70 bg-background/45 p-3">
      <p className="ops-kicker">
        {label}
      </p>
      <p
        className={
          emphasis
            ? "mt-1 break-words text-base font-semibold text-primary"
            : "mt-1 break-words text-sm font-semibold"
        }
      >
        {value}
      </p>
    </div>
  );
}

function MonitorStatePanel({
  title,
  description = "This view updates after the backend response is available.",
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="ops-panel p-6">
      <h2 className="text-base font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </div>
  );
}
