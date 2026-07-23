import type {
  ApprovalHistoryResponse,
  RuntimeStage,
  WorkflowEvent,
  WorkflowState,
} from "@/lib/api/types";

type WorkflowSection =
  | "planner"
  | "retrieval"
  | "quotation"
  | "compliance"
  | "validation"
  | "approval"
  | "email";

type ActivityStatus =
  | "Not started"
  | "Completed"
  | "Waiting for approval"
  | "Blocked until approval"
  | "Ready to run via Resume"
  | "Completed after resume"
  | "Rejected"
  | "Skipped / unavailable";

interface WorkflowAgentActivityPanelProps {
  workflow: WorkflowState;
  events?: WorkflowEvent[];
  approvalHistory?: ApprovalHistoryResponse;
}

interface StageAgentDefinition {
  id: RuntimeStage;
  section: WorkflowSection;
  name: string;
  purpose: string;
}

interface AgentActivity {
  name: string;
  purpose: string;
  status: ActivityStatus;
  source: string;
  summary: string;
  details?: Record<string, unknown>;
}

const STAGE_AGENTS: StageAgentDefinition[] = [
  {
    id: "planner",
    section: "planner",
    name: "Planner Agent",
    purpose: "Transforms the procurement request into the staged execution plan.",
  },
  {
    id: "retrieval",
    section: "retrieval",
    name: "Retrieval / RAG Agent",
    purpose:
      "Collects deterministic retrieval context and optional RAG citations when enabled.",
  },
  {
    id: "quotation",
    section: "quotation",
    name: "Calculator Agent",
    purpose: "Prepares deterministic quotation arithmetic and pricing context.",
  },
  {
    id: "compliance",
    section: "compliance",
    name: "Compliance Agent",
    purpose: "Checks the request against procurement policy and contract context.",
  },
  {
    id: "validation",
    section: "validation",
    name: "Validation / Finance Agent",
    purpose: "Validates finance, supplier, and business-rule readiness.",
  },
  {
    id: "approval",
    section: "approval",
    name: "Approval Package Agent",
    purpose: "Builds the human review package and stops the run at approval.",
  },
  {
    id: "email_preparation",
    section: "email",
    name: "Email Preview Agent",
    purpose:
      "Prepares the post-approval email preview after explicit resume without sending email.",
  },
];

const PRE_APPROVAL_STAGES = new Set<RuntimeStage>([
  "planner",
  "retrieval",
  "quotation",
  "compliance",
  "validation",
  "approval",
]);

const SENSITIVE_KEY_MARKERS = [
  "authorization",
  "cookie",
  "password",
  "secret",
  "token",
  "api_key",
  "apikey",
  "access_key",
  "secret_key",
  "jwt",
  "provider_payload",
  "raw_prompt",
  "chain_of_thought",
  "embedding",
  "vector",
  "raw_document",
  "prompt",
];

const MAX_DETAIL_STRING_LENGTH = 180;
const MAX_DETAIL_JSON_LENGTH = 1400;

export function WorkflowAgentActivityPanel({
  workflow,
  events = [],
  approvalHistory,
}: WorkflowAgentActivityPanelProps) {
  const activities = deriveWorkflowAgentActivities(
    workflow,
    events,
    approvalHistory,
  );

  return (
    <section className="ops-panel p-5 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="ops-kicker">
            Agent activity
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">
            Multi-agent workflow progress
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Agents here are deterministic workflow stages in the no-key demo.
            Enable real LLM runtime only through documented feature flags. The
            UI does not display chain-of-thought, raw prompts, raw provider
            payloads, or embeddings.
          </p>
        </div>
        <span className="ops-chip">
          {workflow.status}
        </span>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {activities.map((activity) => (
          <AgentActivityCard activity={activity} key={activity.name} />
        ))}
      </div>
    </section>
  );
}

export function deriveWorkflowAgentActivities(
  workflow: WorkflowState,
  events: WorkflowEvent[] = [],
  approvalHistory?: ApprovalHistoryResponse,
): AgentActivity[] {
  return [
    ...STAGE_AGENTS.slice(0, 6).map((agent) =>
      deriveStageActivity(workflow, events, agent),
    ),
    deriveHumanApprovalActivity(workflow, approvalHistory),
    deriveStageActivity(workflow, events, STAGE_AGENTS[6]),
  ];
}

function AgentActivityCard({ activity }: { activity: AgentActivity }) {
  return (
    <article className="grid gap-4 rounded-md border border-border/70 bg-background/50 p-4 shadow-[0_0_0_1px_hsl(var(--primary)/0.04)_inset]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h3 className="text-base font-semibold">{activity.name}</h3>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {activity.purpose}
          </p>
        </div>
        <span className={statusClassName(activity.status)}>
          {activity.status}
        </span>
      </div>
      <div className="grid gap-3 border-l border-primary/25 pl-3 text-sm">
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Evidence source
          </p>
          <p className="mt-1 break-words text-muted-foreground">
            {activity.source}
          </p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Summary
          </p>
          <p className="mt-1 break-words leading-6 text-muted-foreground">
            {activity.summary}
          </p>
        </div>
      </div>
      {activity.details ? (
        <details className="ops-panel-muted p-3">
          <summary className="cursor-pointer text-sm font-medium">
            Technical details
          </summary>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-muted-foreground">
            {safeJsonPreview(activity.details)}
          </pre>
        </details>
      ) : null}
    </article>
  );
}

function deriveStageActivity(
  workflow: WorkflowState,
  events: WorkflowEvent[],
  agent: StageAgentDefinition,
): AgentActivity {
  const evidence = stageEvidence(workflow, events, agent);
  const status = stageStatus(workflow, agent.id, Boolean(evidence.details));
  const summary = stageSummary(workflow, agent.id, evidence, status);

  return {
    name: agent.name,
    purpose: agent.purpose,
    status,
    source: evidence.source,
    summary,
    details: evidence.details,
  };
}

function deriveHumanApprovalActivity(
  workflow: WorkflowState,
  approvalHistory?: ApprovalHistoryResponse,
): AgentActivity {
  const finalDecision = approvalHistory?.approvals.find((approval) =>
    ["approve", "reject"].includes(approval.decision),
  );

  if (workflow.status === "CREATED") {
    return {
      name: "Human Approval",
      purpose: "Records the governance decision before post-approval resume.",
      status: "Not started",
      source: "workflow.status/current_step",
      summary: "Click Run workflow to reach the human approval boundary.",
    };
  }

  if (workflow.status === "WAITING_APPROVAL") {
    return {
      name: "Human Approval",
      purpose: "Records the governance decision before post-approval resume.",
      status: "Waiting for approval",
      source: "workflow.status/current_step",
      summary:
        "Runtime has stopped at WAITING_APPROVAL. Review details, evidence, and events before deciding.",
    };
  }

  if (workflow.status === "REJECTED") {
    return {
      name: "Human Approval",
      purpose: "Records the governance decision before post-approval resume.",
      status: "Rejected",
      source: finalDecision ? "approval history" : "workflow.status/current_step",
      summary:
        finalDecision?.comment ??
        "A reject decision is final; resume is blocked for this workflow.",
      details: finalDecision ? { approval: finalDecision } : undefined,
    };
  }

  if (workflow.status === "APPROVED" || workflow.status === "COMPLETED") {
    return {
      name: "Human Approval",
      purpose: "Records the governance decision before post-approval resume.",
      status: "Completed",
      source: finalDecision ? "approval history" : "workflow.status/current_step",
      summary:
        finalDecision?.decision === "approve"
          ? "Approval is complete; explicit resume is allowed after this boundary."
          : "Approval state is complete according to the workflow status.",
      details: finalDecision ? { approval: finalDecision } : undefined,
    };
  }

  return {
    name: "Human Approval",
    purpose: "Records the governance decision before post-approval resume.",
    status: "Skipped / unavailable",
    source: "workflow.status/current_step",
    summary:
      "Human approval evidence is available only after the workflow reaches the approval boundary.",
  };
}

function stageStatus(
  workflow: WorkflowState,
  stage: RuntimeStage,
  hasEvidence: boolean,
): ActivityStatus {
  if (workflow.status === "CREATED") {
    return "Not started";
  }

  if (workflow.status === "REJECTED" && stage === "email_preparation") {
    return "Blocked until approval";
  }

  if (workflow.status === "WAITING_APPROVAL" && stage === "email_preparation") {
    return "Blocked until approval";
  }

  if (workflow.status === "APPROVED" && stage === "email_preparation") {
    return "Ready to run via Resume";
  }

  if (workflow.status === "COMPLETED" && stage === "email_preparation") {
    return "Completed after resume";
  }

  if (
    ["WAITING_APPROVAL", "APPROVED", "COMPLETED", "REJECTED"].includes(
      workflow.status,
    ) &&
    PRE_APPROVAL_STAGES.has(stage)
  ) {
    return "Completed";
  }

  if (hasEvidence) {
    return "Completed";
  }

  return "Skipped / unavailable";
}

function stageSummary(
  workflow: WorkflowState,
  stage: RuntimeStage,
  evidence: ReturnType<typeof stageEvidence>,
  status: ActivityStatus,
): string {
  const summary = findSummary(evidence.details);
  if (summary) {
    return summary;
  }

  if (workflow.status === "CREATED") {
    return "Click Run workflow to start agent execution.";
  }

  if (stage === "retrieval") {
    const citationCount = countRagCitations(workflow);
    if (citationCount > 0) {
      return `RAG grounding attached ${citationCount} citation${citationCount === 1 ? "" : "s"} to the workflow state.`;
    }
    return status === "Completed"
      ? "Retrieval stage completed. RAG citations appear only when RAG is enabled and knowledge has been ingested."
      : "No retrieval or RAG evidence is attached yet.";
  }

  if (stage === "approval") {
    return "Approval package is prepared; /run stops before any final human decision.";
  }

  if (stage === "email_preparation") {
    if (workflow.status === "APPROVED") {
      return "Approval is complete. Click Resume workflow to run the email preview stage; no real email is sent.";
    }
    if (workflow.status === "COMPLETED") {
      return "Post-approval continuation completed with an email preview only; no real email is sent.";
    }
    if (workflow.status === "REJECTED") {
      return "Rejected workflows are terminal, so email preview remains blocked.";
    }
    return "Email preview is blocked until a human approval is recorded and /resume is called.";
  }

  if (status === "Completed") {
    return "Stage completion is derived from workflow progress, stage output, runtime context, or persisted events.";
  }

  return "No safe stage output or event evidence is available for this stage yet.";
}

function stageEvidence(
  workflow: WorkflowState,
  events: WorkflowEvent[],
  agent: StageAgentDefinition,
): { source: string; details?: Record<string, unknown> } {
  const directStageOutput = workflow.stage_outputs?.[agent.id];
  if (directStageOutput && Object.keys(directStageOutput).length > 0) {
    return {
      source: "workflow.stage_outputs",
      details: { stage_output: directStageOutput },
    };
  }

  const outputStage = asRecord(asRecord(workflow.outputs)?.stage_outputs)?.[
    agent.id
  ];
  if (asRecord(outputStage)) {
    return {
      source: "workflow.outputs.stage_outputs",
      details: { stage_output: outputStage },
    };
  }

  const sectionOutput = workflow[agent.section];
  if (sectionOutput && Object.keys(sectionOutput).length > 0) {
    return {
      source: `workflow.${agent.section}`,
      details: { stage_output: sectionOutput },
    };
  }

  const runtimeContext = runtimeContextEvidence(workflow, agent.id);
  if (runtimeContext) {
    return runtimeContext;
  }

  const event = eventForStage(events, agent.id);
  if (event) {
    return {
      source: "persisted events",
      details: {
        event: {
          event_type: event.event_type,
          agent_name: event.agent_name,
          status: event.status,
          message: event.message,
          payload: event.payload,
        },
      },
    };
  }

  return { source: "workflow.status/current_step" };
}

function runtimeContextEvidence(
  workflow: WorkflowState,
  stage: RuntimeStage,
): { source: string; details: Record<string, unknown> } | null {
  const runtimeContext = asRecord(workflow.runtime_context);
  if (!runtimeContext) {
    return null;
  }

  const completedStages = stringArray(runtimeContext.completed_stages);
  const lastCompletedStage =
    typeof runtimeContext.last_completed_stage === "string"
      ? runtimeContext.last_completed_stage
      : null;
  const ragStage = asRecord(asRecord(asRecord(runtimeContext.rag)?.stages)?.[stage]);

  if (
    completedStages.includes(stage) ||
    lastCompletedStage === stage ||
    ragStage
  ) {
    return {
      source: "workflow.runtime_context",
      details: {
        completed_stages: completedStages,
        last_completed_stage: lastCompletedStage,
        rag: ragStage ? { [stage]: ragStage } : undefined,
      },
    };
  }

  return null;
}

function eventForStage(
  events: WorkflowEvent[],
  stage: RuntimeStage,
): WorkflowEvent | null {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    const payloadStage = asString(event.payload?.stage);
    if (
      event.agent_name === stage ||
      payloadStage === stage ||
      (stage === "retrieval" && event.event_type.startsWith("knowledge.")) ||
      (stage === "email_preparation" &&
        event.event_type.includes("email_preparation"))
    ) {
      return event;
    }
  }
  return null;
}

function findSummary(value: unknown): string | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }

  const directSummary = asString(record.summary);
  if (directSummary) {
    return boundText(directSummary);
  }

  const stageOutput = asRecord(record.stage_output);
  if (stageOutput) {
    const outputSummary = asString(stageOutput.summary);
    if (outputSummary) {
      return boundText(outputSummary);
    }
  }

  const event = asRecord(record.event);
  if (event) {
    const message = asString(event.message);
    if (message) {
      return boundText(message);
    }
  }

  return null;
}

function countRagCitations(workflow: WorkflowState): number {
  const ragStages = asRecord(asRecord(workflow.runtime_context)?.rag)?.stages;
  const stages = asRecord(ragStages);
  if (!stages) {
    return 0;
  }

  return Object.values(stages).reduce<number>((total, stageValue) => {
    const citations = asArray(asRecord(stageValue)?.citations);
    return total + (citations?.length ?? 0);
  }, 0);
}

function safeJsonPreview(value: Record<string, unknown>): string {
  const sanitized = sanitizeValue(value);
  const json = JSON.stringify(sanitized, null, 2) ?? "{}";
  return json.length > MAX_DETAIL_JSON_LENGTH
    ? `${json.slice(0, MAX_DETAIL_JSON_LENGTH)}...`
    : json;
}

function sanitizeValue(value: unknown, depth = 0): unknown {
  if (depth > 4) {
    return "[bounded]";
  }

  if (typeof value === "string") {
    return boundText(redactSensitiveString(value));
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null
  ) {
    return value;
  }

  if (Array.isArray(value)) {
    return value.slice(0, 8).map((item) => sanitizeValue(item, depth + 1));
  }

  if (typeof value === "object" && value !== null) {
    const result: Record<string, unknown> = {};
    for (const [key, nestedValue] of Object.entries(value)) {
      if (isSensitiveKey(key)) {
        continue;
      }
      result[key] = sanitizeValue(nestedValue, depth + 1);
    }
    return result;
  }

  return undefined;
}

function isSensitiveKey(key: string): boolean {
  const normalized = key.toLowerCase();
  return SENSITIVE_KEY_MARKERS.some((marker) => normalized.includes(marker));
}

function redactSensitiveString(value: string): string {
  if (/bearer\s+[a-z0-9._-]+/i.test(value)) {
    return "[redacted]";
  }
  if (/sk-[a-z0-9_-]{12,}/i.test(value)) {
    return "[redacted]";
  }
  return value;
}

function boundText(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized.length > MAX_DETAIL_STRING_LENGTH
    ? `${normalized.slice(0, MAX_DETAIL_STRING_LENGTH)}...`
    : normalized;
}

function statusClassName(status: ActivityStatus): string {
  const base =
    "inline-flex w-fit shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium";
  if (
    status === "Completed" ||
    status === "Completed after resume" ||
    status === "Ready to run via Resume"
  ) {
    return `${base} ops-status-completed`;
  }
  if (status === "Waiting for approval") {
    return `${base} ops-status-waiting`;
  }
  if (status === "Blocked until approval" || status === "Rejected") {
    return `${base} ops-status-danger`;
  }
  return `${base} border-border/70 bg-muted/30 text-muted-foreground`;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function asArray(value: unknown): unknown[] | null {
  return Array.isArray(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}
