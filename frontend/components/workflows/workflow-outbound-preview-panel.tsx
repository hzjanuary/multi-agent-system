"use client";

import { useState } from "react";

import { ApiClientError } from "@/lib/api/client";
import { getWorkflowOutboundPreview } from "@/lib/api/workflows";
import type {
  OutboundCommunicationPreview,
  OutboundRecipient,
  WorkflowState,
} from "@/lib/api/types";

type PreviewState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; preview: OutboundCommunicationPreview }
  | { status: "error"; message: string };

interface WorkflowOutboundPreviewPanelProps {
  workflow: WorkflowState;
  token: string;
}

export function WorkflowOutboundPreviewPanel({
  workflow,
  token,
}: WorkflowOutboundPreviewPanelProps) {
  const [previewState, setPreviewState] = useState<PreviewState>({
    status: "idle",
  });
  const canLoadPreview = workflow.status === "COMPLETED";

  async function loadPreview() {
    if (!canLoadPreview || previewState.status === "loading") {
      return;
    }

    setPreviewState({ status: "loading" });
    try {
      const preview = await getWorkflowOutboundPreview(workflow.workflow_id, {
        token,
      });
      setPreviewState({ status: "ready", preview });
    } catch (error) {
      setPreviewState({
        status: "error",
        message: outboundPreviewErrorMessage(error),
      });
    }
  }

  return (
    <section className={canLoadPreview ? "ops-panel-strong p-5" : "ops-panel p-5"}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="ops-kicker">Approved communication</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">
            Approved Communication Preview
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {canLoadPreview
              ? "Load the approved customer communication preview after the workflow has completed approval and resume. This UI has no send action."
              : "Preview becomes available only after Manager/Admin approval and explicit resume to COMPLETED."}
          </p>
        </div>
        {canLoadPreview ? (
          <button
            className="ops-button-primary"
            disabled={previewState.status === "loading"}
            onClick={() => void loadPreview()}
            type="button"
          >
            {previewState.status === "loading"
              ? "Loading preview..."
              : "Load approved preview"}
          </button>
        ) : (
          <span className="ops-chip min-h-10 px-4">Pending completion</span>
        )}
      </div>

      <div className="mt-5 rounded-md border border-border/80 bg-background/35 p-4 text-sm leading-6 text-muted-foreground">
        Preview-only surface. Delivery is disabled, Gmail/SMTP integration is not
        connected, and customer-ready communication remains governed by the
        completed approval/resume lifecycle.
      </div>

      {previewState.status === "error" ? (
        <div className="mt-5 rounded-md border border-amber-300/30 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
          {previewState.message}
        </div>
      ) : null}

      {previewState.status === "ready" ? (
        <PreviewContent preview={previewState.preview} />
      ) : null}
    </section>
  );
}

function PreviewContent({ preview }: { preview: OutboundCommunicationPreview }) {
  return (
    <div className="mt-5 grid gap-4">
      <div className="grid gap-3 md:grid-cols-3">
        <PreviewFact label="Source" value={preview.source} />
        <PreviewFact label="Approval state" value={preview.approval_status} />
        <PreviewFact
          label="Delivery state"
          value={
            preview.is_sent || preview.is_sendable
              ? "Requires safety review"
              : "Preview only"
          }
        />
      </div>

      <div className="ops-panel-muted grid gap-3 p-4">
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Subject
          </p>
          <h3 className="mt-1 text-base font-semibold">{preview.subject}</h3>
        </div>
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Body preview
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-foreground/90">
            {preview.body}
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="ops-panel-muted p-4">
          <h3 className="text-sm font-semibold">Recipients</h3>
          {preview.recipients.length > 0 ? (
            <ul className="mt-3 grid gap-2">
              {preview.recipients.map((recipient, index) => (
                <RecipientRow key={`${recipient.email ?? recipient.role}-${index}`} recipient={recipient} />
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              No recipient metadata was included in the preview.
            </p>
          )}
        </div>

        <div className="ops-panel-muted p-4">
          <h3 className="text-sm font-semibold">Safety warnings</h3>
          {preview.warnings.length > 0 ? (
            <ul className="mt-3 grid gap-2 text-sm leading-6 text-muted-foreground">
              {preview.warnings.map((warning) => (
                <li key={warning} className="rounded border border-border/70 bg-background/30 px-3 py-2">
                  {warning}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              No additional warnings were returned.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function PreviewFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border/70 bg-background/35 p-3">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}

function RecipientRow({ recipient }: { recipient: OutboundRecipient }) {
  const primary = recipient.name ?? recipient.email ?? recipient.role ?? "Recipient";
  const secondary = [recipient.email, recipient.role].filter(Boolean).join(" / ");

  return (
    <li className="rounded border border-border/70 bg-background/30 px-3 py-2">
      <p className="text-sm font-medium">{primary}</p>
      {secondary ? (
        <p className="mt-1 break-words text-xs text-muted-foreground">
          {secondary}
        </p>
      ) : null}
    </li>
  );
}

function outboundPreviewErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 401) {
      return "Sign in again before loading the approved communication preview.";
    }
    if (error.status === 403) {
      return "Your account cannot view approved communication previews.";
    }
    if (error.status === 409) {
      return `Preview unavailable: ${error.message}`;
    }
    return error.message;
  }
  return "Preview unavailable. Check the workflow status and backend readiness.";
}
