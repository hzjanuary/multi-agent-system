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

export type WorkflowType = "procurement_quotation";

export interface WorkflowStateMetadata {
  state_version?: number;
  created_by_id?: string | null;
  tags?: Record<string, string>;
  attributes?: Record<string, unknown>;
}

export interface WorkflowCreateRequest {
  workflow_type: WorkflowType;
  domain?: string | null;
  request: Record<string, unknown>;
  metadata?: WorkflowStateMetadata;
}

export interface WorkflowState {
  workflow_id: string;
  workflow_type: WorkflowType | string;
  domain?: string | null;
  status: WorkflowStatus;
  request: Record<string, unknown>;
  metadata?: WorkflowStateMetadata | Record<string, unknown>;
  customer?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  planner?: Record<string, unknown>;
  retrieval?: Record<string, unknown>;
  quotation?: Record<string, unknown>;
  compliance?: Record<string, unknown>;
  validation?: Record<string, unknown>;
  approval?: Record<string, unknown>;
  email?: Record<string, unknown>;
  current_step?: string | null;
  runtime_context?: Record<string, unknown>;
  stage_outputs?: Partial<Record<RuntimeStage, Record<string, unknown>>>;
  outputs?: Record<string, unknown>;
  steps?: WorkflowStepState[];
  retry_count?: number;
  error?: WorkflowError | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkflowError {
  code: string;
  message: string;
  failed_step?: string | null;
  retryable?: boolean;
  details?: Record<string, unknown>;
}

export interface WorkflowStepState {
  name: string;
  status: WorkflowStatus;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  output?: Record<string, unknown>;
  error?: WorkflowError | null;
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

export type RuntimeStage =
  | "planner"
  | "retrieval"
  | "quotation"
  | "compliance"
  | "validation"
  | "approval"
  | "email_preparation";

export interface RuntimeWorkflowState {
  workflow_id: string;
  workflow_type: WorkflowType | string;
  domain?: string | null;
  status: WorkflowStatus;
  request: Record<string, unknown>;
  metadata?: WorkflowStateMetadata | Record<string, unknown>;
  customer?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  current_stage?: RuntimeStage | null;
  completed_stages?: RuntimeStage[];
  failed_stage?: RuntimeStage | null;
  runtime_context?: Record<string, unknown>;
  stage_outputs?: Partial<Record<RuntimeStage, Record<string, unknown>>>;
  outputs?: Record<string, unknown>;
  steps?: WorkflowStepState[];
  retry_count?: number;
  error?: WorkflowError | null;
  events?: Record<string, unknown>[];
}

export interface RuntimeWorkflowResult {
  state: RuntimeWorkflowState;
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

export type ApprovalDecisionType = "approve" | "reject" | "request_changes";

export interface ApprovalDecisionRequest {
  decision: ApprovalDecisionType;
  comment?: string | null;
  request_id?: string | null;
  metadata?: Record<string, JsonValue>;
}

export interface ApprovalRecord {
  decision_id: string;
  workflow_id: string;
  decision: ApprovalDecisionType;
  actor_id: string;
  actor_email?: string | null;
  actor_roles: string[];
  comment?: string | null;
  decided_at: string;
  previous_status: WorkflowStatus;
  next_status?: WorkflowStatus | null;
  request_id?: string | null;
  metadata: Record<string, JsonValue>;
}

export interface ApprovalDecisionResponse {
  workflow_id: string;
  approval: ApprovalRecord;
  previous_status: WorkflowStatus;
  next_status: WorkflowStatus;
  can_resume: boolean;
  resume_recommended: boolean;
}

export interface ApprovalHistoryResponse {
  workflow_id: string;
  approvals: ApprovalRecord[];
  has_final_decision: boolean;
  can_resume: boolean;
}

export interface WorkflowResumeRequest {
  request_id?: string | null;
  metadata?: Record<string, JsonValue>;
}

export interface WorkflowResumeResponse {
  workflow_id: string;
  previous_status: WorkflowStatus;
  next_status: WorkflowStatus;
  resumed: boolean;
  message?: string | null;
  request_id?: string | null;
}

export type OutboundCommunicationChannel =
  | "email_preview"
  | "telegram_preview"
  | "file_preview";

export type OutboundCommunicationProvider = "preview" | "file" | "gmail_future";

export interface OutboundRecipient {
  name?: string | null;
  email?: string | null;
  role?: string | null;
}

export interface OutboundCommunicationPreview {
  workflow_id: string;
  channel: OutboundCommunicationChannel;
  provider: OutboundCommunicationProvider;
  subject: string;
  body: string;
  recipients: OutboundRecipient[];
  source: string;
  approval_status: string;
  workflow_status: WorkflowStatus;
  generated_at: string;
  warnings: string[];
  is_sendable: boolean;
  is_sent: boolean;
  requires_human_approval: boolean;
  communication_label: string;
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

export type WorkflowTimelineEventSource = "persisted" | "live";

export interface WorkflowTimelineEvent {
  event_id: string;
  workflow_id: string;
  event_type: string;
  status?: string | null;
  stage?: string | null;
  message?: string | null;
  created_at: string;
  emitted_at?: string | null;
  sequence?: number | null;
  payload: Record<string, unknown>;
  source: WorkflowTimelineEventSource;
}

export type KnowledgeDocumentSourceType =
  | "policy"
  | "contract"
  | "pricing"
  | "supplier_profile"
  | "rfq"
  | "guideline"
  | "compliance_checklist";

export interface KnowledgeCitation {
  citation_id: string;
  document_id: string;
  document_title: string;
  source_type: KnowledgeDocumentSourceType;
  section?: string | null;
  page?: number | null;
  excerpt: string;
  relevance_score: number;
  citation_label: string;
}

export interface KnowledgeRetrievalResult {
  chunk_id: string;
  document_id: string;
  chunk_text: string;
  score: number;
  source_type: KnowledgeDocumentSourceType;
  document_title: string;
  domain: string;
  citation: KnowledgeCitation;
  metadata: Record<string, JsonValue>;
}

export interface KnowledgeSearchRequest {
  query: string;
  top_k?: number;
  source_types?: KnowledgeDocumentSourceType[];
  domain?: string | null;
  document_ids?: string[];
  minimum_score?: number | null;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: KnowledgeRetrievalResult[];
}

export interface KnowledgeDocumentCatalogItem {
  document_id: string;
  title: string;
  source_type: KnowledgeDocumentSourceType;
  domain: string;
  version?: string | null;
  effective_date?: string | null;
  owner_team?: string | null;
  object_storage_key?: string | null;
  checksum?: string | null;
  content_type?: string | null;
  dataset_path?: string | null;
  tags: string[];
  attributes: Record<string, JsonValue>;
}

export interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocumentCatalogItem[];
  count: number;
}

export interface KnowledgeDocumentDetailResponse {
  document: KnowledgeDocumentCatalogItem;
  content_preview?: string | null;
}

export interface WorkflowEvidenceCitation extends KnowledgeCitation {
  stage?: RuntimeStage | string | null;
  reason?: string | null;
}
