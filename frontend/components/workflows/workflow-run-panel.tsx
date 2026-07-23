"use client";

import { useState } from "react";

import { ApiClientError } from "@/lib/api/client";
import { runWorkflow } from "@/lib/api/workflows";
import { getAccessToken } from "@/lib/auth/session";
import type { WorkflowRunResponse, WorkflowState } from "@/lib/api/types";

type RunState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "success"; response: WorkflowRunResponse }
  | { status: "error"; message: string };

interface WorkflowRunPanelProps {
  workflowId: string;
  workflowStatus?: WorkflowState["status"];
  onRunCompleted?: () => Promise<void> | void;
}

export function WorkflowRunPanel({
  workflowId,
  workflowStatus = "CREATED",
  onRunCompleted,
}: WorkflowRunPanelProps) {
  const [runState, setRunState] = useState<RunState>({ status: "idle" });
  const guidance = runGuidance(workflowStatus);

  async function handleRun() {
    if (!guidance.canRun) {
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setRunState({
        status: "error",
        message: "Sign in before running this workflow.",
      });
      return;
    }

    setRunState({ status: "running" });
    try {
      const response = await runWorkflow(workflowId, { token });
      setRunState({ status: "success", response });
      await onRunCompleted?.();
    } catch (error) {
      setRunState({ status: "error", message: runErrorMessage(error) });
    }
  }

  const isRunning = runState.status === "running";
  const panelClassName = guidance.canRun
    ? "ops-panel-strong p-5 md:p-6"
    : "ops-panel p-5 md:p-6";

  return (
    <section className={panelClassName}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="ops-kicker">
            Runtime action
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">
            {guidance.title}
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {guidance.description}
          </p>
        </div>
        {guidance.canRun ? (
          <button
            className="ops-button-primary"
            disabled={isRunning}
            onClick={handleRun}
            type="button"
          >
            {isRunning ? "Running..." : "Run workflow"}
          </button>
        ) : (
          <span className="ops-chip min-h-10 px-4">
            {guidance.actionLabel}
          </span>
        )}
      </div>

      {runState.status === "success" ? (
        <RuntimeResult response={runState.response} />
      ) : null}

      {runState.status === "error" ? (
        <div className="mt-5 rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {runState.message}
        </div>
      ) : null}
    </section>
  );
}

function runGuidance(status: WorkflowState["status"]): {
  title: string;
  description: string;
  actionLabel: string;
  canRun: boolean;
} {
  if (status === "CREATED") {
    return {
      title: "Run deterministic workflow",
      description:
        "Start the existing backend runtime. The expected demo stop is WAITING_APPROVAL, where human review begins.",
      actionLabel: "Run workflow",
      canRun: true,
    };
  }
  if (status === "WAITING_APPROVAL") {
    return {
      title: "Run already stopped at approval",
      description:
        "Do not run this workflow again. Review details and evidence, then submit a human approval decision.",
      actionLabel: "Review and approve",
      canRun: false,
    };
  }
  if (status === "APPROVED") {
    return {
      title: "Approved workflow is ready to resume",
      description:
        "Use Resume workflow in the approval panel. Resume continues after approval and does not call /run.",
      actionLabel: "Use Resume",
      canRun: false,
    };
  }
  if (
    status === "COMPLETED" ||
    status === "REJECTED" ||
    status === "FAILED" ||
    status === "CANCELLED"
  ) {
    return {
      title: "Runtime action unavailable",
      description:
        "This workflow is in a terminal state. Review the detail, approval history, evidence, and timeline.",
      actionLabel: "Terminal state",
      canRun: false,
    };
  }
  return {
    title: "Workflow is already in progress",
    description:
      "The backend is authoritative for runtime progress. Wait for the next stable status before taking another action.",
    actionLabel: "In progress",
    canRun: false,
  };
}

function RuntimeResult({ response }: { response: WorkflowRunResponse }) {
  return (
    <div className="ops-panel-muted mt-5 grid gap-4 p-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <ResultItem label="Status" value={response.status} />
        <ResultItem
          label="Waiting approval"
          value={response.waiting_for_approval ? "Yes" : "No"}
        />
        <ResultItem label="Completed" value={response.completed ? "Yes" : "No"} />
      </div>
      <div>
        <h3 className="text-sm font-semibold">Runtime result</h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {response.message ??
            "Runtime returned successfully. Check persisted events below for progress evidence."}
        </p>
      </div>
      <div>
        <h3 className="text-sm font-semibold">Completed stages</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {response.completed_stages.length > 0
            ? response.completed_stages.join(", ")
            : "No completed stages reported."}
        </p>
      </div>
    </div>
  );
}

function ResultItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}

function runErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 401) {
      return "Your session is not authorized. Sign in again.";
    }
    if (error.status === 403) {
      return "Your account cannot run workflows.";
    }
    if (error.status === 409) {
      return error.message || "This workflow cannot be run from its current state.";
    }
    return error.message;
  }
  return "The workflow runtime is unavailable. Try again later.";
}
