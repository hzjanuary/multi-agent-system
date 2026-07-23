"use client";

import { useState } from "react";

import { ApiClientError } from "@/lib/api/client";
import {
  resumeWorkflow,
  submitWorkflowApproval,
} from "@/lib/api/workflows";
import { getAccessToken } from "@/lib/auth/session";
import type {
  ApprovalDecisionResponse,
  ApprovalDecisionType,
  ApprovalHistoryResponse,
  WorkflowResumeResponse,
  WorkflowState,
} from "@/lib/api/types";

const MAX_APPROVAL_COMMENT_LENGTH = 2000;

type ApprovalActionState =
  | { status: "idle" }
  | { status: "submitting"; action: ApprovalDecisionType | "resume" }
  | { status: "success"; message: string }
  | { status: "error"; message: string };

interface WorkflowApprovalPanelProps {
  workflow: WorkflowState;
  approvalHistory: ApprovalHistoryResponse;
  onApprovalChanged?: () => Promise<void> | void;
}

export function WorkflowApprovalPanel({
  workflow,
  approvalHistory,
  onApprovalChanged,
}: WorkflowApprovalPanelProps) {
  const [comment, setComment] = useState("");
  const [actionState, setActionState] = useState<ApprovalActionState>({
    status: "idle",
  });

  const canSubmitDecision = workflow.status === "WAITING_APPROVAL";
  const canResume =
    workflow.status === "APPROVED" || approvalHistory.can_resume === true;
  const isSubmitting = actionState.status === "submitting";
  const statusCopy = approvalStatusCopy(workflow.status, canResume);
  const panelClassName =
    canSubmitDecision || canResume
      ? "ops-panel-strong p-5 md:p-6"
      : "ops-panel p-5 md:p-6";

  async function submitDecision(decision: ApprovalDecisionType) {
    const validationMessage = approvalValidationMessage(decision, comment);
    if (validationMessage) {
      setActionState({ status: "error", message: validationMessage });
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setActionState({
        status: "error",
        message: "Sign in before submitting an approval decision.",
      });
      return;
    }

    setActionState({ status: "submitting", action: decision });
    try {
      const response = await submitWorkflowApproval(
        workflow.workflow_id,
        {
          decision,
          comment: comment.trim() || null,
        },
        { token },
      );
      setActionState({
        status: "success",
        message: approvalSuccessMessage(response),
      });
      setComment("");
      await onApprovalChanged?.();
    } catch (error) {
      setActionState({ status: "error", message: approvalErrorMessage(error) });
    }
  }

  async function handleResume() {
    const token = getAccessToken();
    if (!token) {
      setActionState({
        status: "error",
        message: "Sign in before resuming this workflow.",
      });
      return;
    }

    setActionState({ status: "submitting", action: "resume" });
    try {
      const response = await resumeWorkflow(workflow.workflow_id, {}, { token });
      setActionState({
        status: "success",
        message: resumeSuccessMessage(response),
      });
      await onApprovalChanged?.();
    } catch (error) {
      setActionState({ status: "error", message: resumeErrorMessage(error) });
    }
  }

  return (
    <section className={panelClassName}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="ops-kicker">
            Approval workflow
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">
            Human approval and resume
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {statusCopy}
          </p>
        </div>
        <StatusPill status={workflow.status} />
      </div>

      {canSubmitDecision ? (
        <div className="mt-5 grid gap-4">
          <label className="grid gap-2 text-sm font-medium">
            Approval comment
            <textarea
              className="ops-input min-h-28 resize-y p-3 font-normal leading-6"
              maxLength={MAX_APPROVAL_COMMENT_LENGTH}
              name="approvalComment"
              onChange={(event) => setComment(event.target.value)}
              placeholder="Add a bounded decision comment. Rejections require a comment."
              value={comment}
            />
          </label>
          <div className="text-xs text-muted-foreground">
            {comment.length}/{MAX_APPROVAL_COMMENT_LENGTH} characters
          </div>
          <div className="flex flex-wrap gap-3">
            <ApprovalButton
              disabled={isSubmitting}
              label="Approve"
              loadingLabel="Approving..."
              loading={isSubmitting && actionState.action === "approve"}
              onClick={() => void submitDecision("approve")}
            />
            <ApprovalButton
              disabled={isSubmitting}
              label="Reject"
              loadingLabel="Rejecting..."
              loading={isSubmitting && actionState.action === "reject"}
              onClick={() => void submitDecision("reject")}
              variant="danger"
            />
            <ApprovalButton
              disabled={isSubmitting}
              label="Request changes"
              loadingLabel="Requesting..."
              loading={isSubmitting && actionState.action === "request_changes"}
              onClick={() => void submitDecision("request_changes")}
              variant="secondary"
            />
          </div>
        </div>
      ) : (
        <p className="mt-5 text-sm leading-6 text-muted-foreground">
          {nonDecisionCopy(workflow.status)}
        </p>
      )}

      {canResume ? (
        <div className="mt-5 rounded-md border border-primary/30 bg-primary/10 p-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 className="text-sm font-semibold">
                Post-approval continuation
              </h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Resume the approved workflow through the email preparation
                preview stage. This does not send real email.
              </p>
            </div>
            <ApprovalButton
              disabled={isSubmitting}
              label="Resume workflow"
              loadingLabel="Resuming..."
              loading={isSubmitting && actionState.action === "resume"}
              onClick={() => void handleResume()}
            />
          </div>
        </div>
      ) : null}

      {actionState.status === "success" ? (
        <div className="mt-5 rounded-md border border-emerald-400/30 bg-emerald-400/10 p-4 text-sm text-emerald-200">
          {actionState.message}
        </div>
      ) : null}

      {actionState.status === "error" ? (
        <div className="mt-5 rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {actionState.message}
        </div>
      ) : null}
    </section>
  );
}

function approvalStatusCopy(
  status: WorkflowState["status"],
  canResume: boolean,
): string {
  if (status === "WAITING_APPROVAL") {
    return "Human approval required before continuation. Review the workflow state, attached evidence, and timeline before deciding.";
  }
  if (status === "APPROVED" || canResume) {
    return "Resume is now available. It continues the approved workflow without calling /run and does not send real email.";
  }
  if (status === "COMPLETED") {
    return "No more approval or resume actions are available. Review history and timeline evidence.";
  }
  if (status === "REJECTED") {
    return "Rejected workflows are terminal. Review the approval history for the recorded decision.";
  }
  return "Approval decisions are available only at WAITING_APPROVAL. Backend authorization remains the source of truth.";
}

function nonDecisionCopy(status: WorkflowState["status"]): string {
  if (status === "APPROVED") {
    return "Approval is complete. Use Resume workflow when continuation is available.";
  }
  if (status === "COMPLETED") {
    return "This workflow is complete. No more approval or resume actions are available.";
  }
  if (status === "REJECTED") {
    return "Rejected workflows are terminal. No resume action is available.";
  }
  return "Approval decisions are available only while the workflow is WAITING_APPROVAL. Backend authorization remains the source of truth for who can approve, reject, or request changes.";
}

function ApprovalButton({
  disabled,
  label,
  loading,
  loadingLabel,
  onClick,
  variant = "primary",
}: {
  disabled: boolean;
  label: string;
  loading: boolean;
  loadingLabel: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "danger";
}) {
  const className =
    variant === "danger"
      ? "inline-flex h-10 items-center justify-center rounded-md bg-destructive px-4 text-sm font-semibold text-destructive-foreground disabled:cursor-not-allowed disabled:opacity-60"
      : variant === "secondary"
        ? "ops-button-secondary"
        : "ops-button-primary";

  return (
    <button
      className={className}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {loading ? loadingLabel : label}
    </button>
  );
}

function StatusPill({ status }: { status: WorkflowState["status"] }) {
  return (
    <span className="ops-chip min-h-9">
      {status}
    </span>
  );
}

function approvalValidationMessage(
  decision: ApprovalDecisionType,
  comment: string,
): string | null {
  if (comment.length > MAX_APPROVAL_COMMENT_LENGTH) {
    return "Approval comments must be 2,000 characters or fewer.";
  }
  if (decision === "reject" && comment.trim().length === 0) {
    return "Reject decisions require a comment.";
  }
  return null;
}

function approvalSuccessMessage(response: ApprovalDecisionResponse): string {
  const decision = response.approval.decision;
  if (decision === "approve") {
    return response.can_resume
      ? "Workflow approved. It is ready for explicit resume."
      : "Workflow approved.";
  }
  if (decision === "reject") {
    return "Workflow rejected.";
  }
  return "Changes requested. The workflow remains in approval review.";
}

function resumeSuccessMessage(response: WorkflowResumeResponse): string {
  if (response.resumed) {
    return response.message ?? "Workflow resumed successfully.";
  }
  return response.message ?? "Workflow resume request completed.";
}

function approvalErrorMessage(error: unknown): string {
  return actionErrorMessage(error, {
    forbidden: "Your account cannot submit approval decisions.",
    conflict:
      "This workflow cannot accept that approval decision from its current state.",
    notFound: "The workflow was not found.",
    unauthorized: "Your session is not authorized. Sign in again.",
    validation: "Check the approval decision and comment, then try again.",
    fallback: "The approval decision could not be submitted. Try again later.",
  });
}

function resumeErrorMessage(error: unknown): string {
  return actionErrorMessage(error, {
    forbidden: "Your account cannot resume workflows.",
    conflict:
      "This workflow cannot resume from its current approval or runtime state.",
    notFound: "The workflow was not found.",
    unauthorized: "Your session is not authorized. Sign in again.",
    validation: "Check the resume request, then try again.",
    fallback: "The workflow could not be resumed. Try again later.",
  });
}

function actionErrorMessage(
  error: unknown,
  messages: {
    unauthorized: string;
    forbidden: string;
    notFound: string;
    conflict: string;
    validation: string;
    fallback: string;
  },
): string {
  if (error instanceof ApiClientError) {
    if (error.status === 401) {
      return messages.unauthorized;
    }
    if (error.status === 403) {
      return messages.forbidden;
    }
    if (error.status === 404) {
      return messages.notFound;
    }
    if (error.status === 409) {
      return error.message || messages.conflict;
    }
    if (error.status === 422) {
      return error.message || messages.validation;
    }
    return error.message;
  }
  return messages.fallback;
}
