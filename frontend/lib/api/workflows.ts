import { apiFetch, type ApiFetchOptions } from "@/lib/api/client";
import type {
  ApprovalDecisionRequest,
  ApprovalDecisionResponse,
  ApprovalHistoryResponse,
  OutboundCommunicationPreview,
  WorkflowCreateRequest,
  WorkflowEventListResponse,
  WorkflowListResponse,
  WorkflowResponse,
  WorkflowResumeRequest,
  WorkflowResumeResponse,
  WorkflowRunResponse,
  WorkflowStatus,
} from "@/lib/api/types";

type WorkflowRequestOptions = Pick<ApiFetchOptions, "baseUrl" | "fetcher"> & {
  token: string;
};

export interface WorkflowListParams {
  limit?: number;
  offset?: number;
  status?: WorkflowStatus | null;
}

export function listWorkflows(
  options: WorkflowRequestOptions,
  params: WorkflowListParams = {},
): Promise<WorkflowListResponse> {
  return apiFetch<WorkflowListResponse>("/workflows", {
    ...options,
    query: {
      limit: params.limit ?? 100,
      offset: params.offset ?? 0,
      status: params.status ?? undefined,
    },
  });
}

export function getWorkflow(
  workflowId: string,
  options: WorkflowRequestOptions,
): Promise<WorkflowResponse> {
  return apiFetch<WorkflowResponse>(workflowPath(workflowId), options);
}

export function createWorkflow(
  payload: WorkflowCreateRequest,
  options: WorkflowRequestOptions,
): Promise<WorkflowResponse> {
  return apiFetch<WorkflowResponse>("/workflows", {
    ...options,
    method: "POST",
    body: payload,
  });
}

export function runWorkflow(
  workflowId: string,
  options: WorkflowRequestOptions,
): Promise<WorkflowRunResponse> {
  return apiFetch<WorkflowRunResponse>(`${workflowPath(workflowId)}/run`, {
    ...options,
    method: "POST",
  });
}

export function submitWorkflowApproval(
  workflowId: string,
  payload: ApprovalDecisionRequest,
  options: WorkflowRequestOptions,
): Promise<ApprovalDecisionResponse> {
  return apiFetch<ApprovalDecisionResponse>(
    `${workflowPath(workflowId)}/approval`,
    {
      ...options,
      method: "POST",
      body: payload,
    },
  );
}

export function getWorkflowApprovalHistory(
  workflowId: string,
  options: WorkflowRequestOptions,
): Promise<ApprovalHistoryResponse> {
  return apiFetch<ApprovalHistoryResponse>(
    `${workflowPath(workflowId)}/approval/history`,
    options,
  );
}

export function resumeWorkflow(
  workflowId: string,
  payload: WorkflowResumeRequest = {},
  options: WorkflowRequestOptions,
): Promise<WorkflowResumeResponse> {
  return apiFetch<WorkflowResumeResponse>(`${workflowPath(workflowId)}/resume`, {
    ...options,
    method: "POST",
    body: payload,
  });
}

export function getWorkflowOutboundPreview(
  workflowId: string,
  options: WorkflowRequestOptions,
): Promise<OutboundCommunicationPreview> {
  return apiFetch<OutboundCommunicationPreview>(
    `${workflowPath(workflowId)}/outbound/preview`,
    options,
  );
}

export function listWorkflowEvents(
  workflowId: string,
  options: WorkflowRequestOptions,
  params: Pick<WorkflowListParams, "limit" | "offset"> = {},
): Promise<WorkflowEventListResponse> {
  return apiFetch<WorkflowEventListResponse>(`${workflowPath(workflowId)}/events`, {
    ...options,
    query: {
      limit: params.limit ?? 25,
      offset: params.offset ?? 0,
    },
  });
}

function workflowPath(workflowId: string): string {
  return `/workflows/${encodeURIComponent(workflowId)}`;
}
