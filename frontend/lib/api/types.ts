export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export type HttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

export interface ApiErrorDetail {
  code?: string;
  message?: string;
  details?: Record<string, unknown>;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer" | string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

export interface CurrentUserResponse {
  user: UserProfile;
}

export interface LogoutResponse {
  success: boolean;
}

export type WorkflowStatus =
  | "CREATED"
  | "PLANNING"
  | "RETRIEVING"
  | "CALCULATING"
  | "CHECKING_COMPLIANCE"
  | "VALIDATING"
  | "WAITING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "GENERATING_EMAIL"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface WorkflowState {
  workflow_id: string;
  workflow_type: string;
  domain?: string | null;
  status: WorkflowStatus;
  request: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  customer?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  current_step?: string | null;
  outputs?: Record<string, unknown>;
  retry_count?: number;
  error?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkflowResponse {
  workflow: WorkflowState;
}

export interface WorkflowListResponse {
  workflows: WorkflowState[];
  count: number;
  limit: number;
  offset: number;
  status: WorkflowStatus | null;
}

export interface WorkflowEvent {
  event_id: string;
  workflow_id: string;
  event_type: string;
  actor_type?: string | null;
  actor_id?: string | null;
  agent_name?: string | null;
  status?: string | null;
  message?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface WorkflowEventListResponse {
  events: WorkflowEvent[];
  count: number;
  limit: number;
  offset: number;
}

export interface RuntimeWorkflowResult {
  state: Record<string, unknown>;
  completed: boolean;
  failed: boolean;
  message?: string | null;
}

export interface WorkflowRunResponse {
  result: RuntimeWorkflowResult;
  workflow_id: string;
  status: WorkflowStatus;
  completed_stages: string[];
  waiting_for_approval: boolean;
  completed: boolean;
  failed: boolean;
  message?: string | null;
}

export interface WorkflowEventStreamMessage {
  type: "workflow.event";
  workflow_id: string;
  event_id: string;
  event_type: string;
  status?: string | null;
  stage?: string | null;
  message?: string | null;
  created_at: string;
  emitted_at: string;
  sequence?: number | null;
  payload: Record<string, unknown>;
}
