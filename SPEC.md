# PRODUCT SPEC

# Enterprise Multi-Agent OS

## Automated Business Workflow Orchestration Platform

## Academic Title

**Enterprise Procurement Workflow Automation using LangGraph-based Multi-Agent System**

---

## 1. Product Overview

### 1.1 Product Name

**Enterprise Multi-Agent OS**

### 1.2 Product Vision

Enterprise Multi-Agent OS is a distributed AI-agent orchestration platform that automates complex enterprise workflows by coordinating multiple specialized AI Agents, deterministic tools, enterprise knowledge bases, human approvals, and audit trails.

The first product domain is **enterprise procurement workflow automation**, but the platform must be designed to support multiple business workflows in the future.

### 1.3 Core Idea

This is not a chatbot.

It is a **state-driven business workflow operating system** where AI Agents act as specialized workers inside a controlled enterprise process.

The system receives a business request, decomposes it into tasks, coordinates Agents, retrieves relevant enterprise knowledge, performs deterministic calculations, validates results, asks for human approval, and generates business-ready outputs.

---

## 2. Product Scope

### 2.1 MVP Scope

The MVP focuses on automating procurement and quotation workflows across multiple domains:

```text
IT Equipment
Office Furniture
Facility Maintenance
Software Subscription
Logistics Equipment
```

The system must support the following workflow:

```text
Business Request
  -> Planner Agent
  -> Retrieval Agent
  -> Calculator Agent
  -> Compliance Agent
  -> Validation Agent
  -> Human Approval
  -> Email Preview Agent
  -> Completed Workflow
```

### 2.2 Out of Scope for MVP

The following features are not included in the MVP:

```text
Real ERP integration
Real payment processing
Automatic email sending without approval
Native mobile app
Digital signature
Advanced OCR for scanned documents
Fine-tuning custom models
Multi-tenant billing
Production SaaS subscription management
```

---

## 3. Target Users

## 3.1 Admin

Admin manages the entire system.

Responsibilities:

```text
Manage users
Manage roles
Manage system configuration
Upload master data
View all workflows
View audit logs
Manage LLM provider settings
```

## 3.2 Sales User

Sales creates procurement workflows from customer requests.

Responsibilities:

```text
Create workflow
Upload customer request
Track workflow progress
Review generated quotation
Review generated email preview
Send final response manually
```

## 3.3 Manager

Manager approves or rejects generated quotations.

Responsibilities:

```text
View pending approvals
Review quotation
Review compliance result
Approve workflow
Reject workflow with comment
```

## 3.4 Legal User

Legal reviews compliance-related information.

Responsibilities:

```text
Upload policy documents
Review compliance reports
Add legal comments
View workflows requiring legal attention
```

## 3.5 Finance User

Finance manages pricing and calculation rules.

Responsibilities:

```text
Upload pricing data
Manage tax rules
Manage discount rules
Review quotation calculation
View financial risk indicators
```

## 3.6 Viewer

Viewer can only observe workflows and reports.

Responsibilities:

```text
View workflow list
View workflow detail
View analytics
Cannot create, approve, reject, or modify data
```

---

# 4. Functional Requirements

## 4.1 Authentication and Authorization

The system must support secure authentication and role-based access control.

Required capabilities:

```text
Login
Refresh token
Logout
Current user profile
Role-based API authorization
Protected frontend routes
```

Supported roles:

```text
Admin
Manager
Sales
Legal
Finance
Viewer
```

---

## 4.2 Workflow Creation

Users must be able to create a procurement workflow from:

```text
Manual text input
Uploaded RFQ document
Email-like request text
```

A workflow must include:

```text
Workflow ID
Workflow type
Domain
Customer information
Original request
Uploaded documents
Current status
Created by
Created timestamp
```

---

## 4.3 Agent Orchestration

The system must coordinate specialized Agents through LangGraph.

Required Agents:

```text
Planner Agent
Retrieval Agent
Calculator Agent
Compliance Agent
Validation Agent
Email Agent
```

The system must support:

```text
Sequential execution
Conditional routing
Retry
Timeout
Failure handling
Human interruption
Resume after approval
State checkpointing
```

---

## 4.4 Document and Knowledge Management

The system must allow users to upload enterprise documents.

Document types:

```text
Contract
Policy
Pricing
Product specification
Historical quotation
Tender document
```

Documents must be stored in object storage and indexed into Qdrant where applicable.

---

## 4.5 Quotation Calculation

The system must generate deterministic quotation data.

LLM must not perform arithmetic directly.

The Calculator Agent must use a deterministic calculation tool.

A quotation must include:

```text
Item list
Quantity
Unit price
Subtotal
Discount percent
Discount amount
Taxable amount
VAT percent
VAT amount
Total
Grand total
Currency
Approval required flag
```

---

## 4.6 Compliance Checking

The Compliance Agent must check the quotation against:

```text
Contract terms
Internal policies
Payment rules
Discount approval rules
Domain-specific compliance rules
```

Compliance result must include:

```text
Status
Risk level
Violations
Missing clauses
Recommendations
Citations
```

---

## 4.7 Validation

The Validation Agent must validate:

```text
Schema correctness
Required fields
Calculation consistency
Business rule compliance
Missing citations
Invalid workflow transition
```

Validation failure must either:

```text
Request retry from a specific previous Agent
or
Mark workflow as FAILED
```

---

## 4.8 Human Approval

Before customer-facing output is finalized, the workflow must wait for human approval.

Manager can:

```text
Approve
Reject
Add comment
Request revision
```

---

## 4.9 Email Preview Generation

The Email Agent must generate an email preview only after approval.

MVP must not send email automatically.

Email preview must include:

```text
Subject
Body
Quotation summary
Payment terms
Validity period
Next steps
Attachment references
```

---

## 4.10 Monitoring and Audit

The system must record all important events.

Required events:

```text
Workflow created
Agent started
Agent completed
Agent failed
Retry triggered
Validation failed
Approval requested
Workflow approved
Workflow rejected
Email preview generated
Workflow completed
Workflow failed
```

---

# 5. Non-functional Requirements

## 5.1 Reliability

```text
Workflow state must not be lost after backend restart.
Agent timeout must be configurable.
Failed Agent execution must be logged.
Retry count must be limited.
Human approval must be resumable.
```

## 5.2 Security

```text
Passwords must be hashed with Argon2.
JWT must be used for authentication.
Refresh token must be supported.
RBAC must protect APIs.
Secrets must not be hardcoded.
Sensitive prompts must not be exposed in logs.
```

## 5.3 Observability

The system must expose:

```text
Workflow duration
Agent duration
Retry count
Failure count
LLM provider used
Estimated token usage
Estimated LLM cost
Approval waiting time
```

## 5.4 Performance Targets for MVP

```text
Login response: under 1 second
Create workflow: under 1 second
Calculator execution: under 1 second
Retrieval with demo data: under 5 seconds
Full automated workflow before approval: under 30 seconds
Dashboard load with 1,000 workflows: under 2 seconds
```

## 5.5 Testability

Every implementation phase must include tests.

Required test types:

```text
Unit tests
API integration tests
Repository tests
Tool tests
Workflow tests
Mock LLM tests
Frontend component tests where applicable
```

---

# 6. User Stories

# Epic 1 — Authentication and RBAC

## US-001 — User Login

As a registered user,
I want to log in with my email and password,
so that I can access the system securely.

### Acceptance Criteria

```gherkin
Given I am a registered user
When I submit a valid email and password
Then I receive an access token and refresh token
And I am redirected to the dashboard
```

```gherkin
Given I submit invalid credentials
When the login request is processed
Then the system returns an authentication error
And no token is issued
```

---

## US-002 — Role-based Access

As an Admin,
I want system features to be protected by roles,
so that users can only perform actions they are allowed to perform.

### Acceptance Criteria

```gherkin
Given I am logged in as a Sales user
When I try to approve a workflow
Then the system denies the request
```

```gherkin
Given I am logged in as a Manager
When I approve a pending workflow
Then the workflow is approved successfully
```

---

# Epic 2 — Workflow Creation

## US-003 — Create Workflow from Text Request

As a Sales user,
I want to create a procurement workflow from a customer request,
so that the system can process it automatically.

### Acceptance Criteria

```gherkin
Given I am logged in as a Sales user
When I submit a customer procurement request
Then a new workflow is created
And the workflow status is CREATED
And the original request is stored
```

---

## US-004 — Upload RFQ Document

As a Sales user,
I want to upload an RFQ document,
so that the system can use it as workflow input.

### Acceptance Criteria

```gherkin
Given I am creating a workflow
When I upload a supported document file
Then the file is stored in object storage
And the document metadata is stored in the database
And the document is linked to the workflow
```

---

# Epic 3 — Agent Planning

## US-005 — Planner Agent Creates Workflow Plan

As a Sales user,
I want the system to understand the request and create an execution plan,
so that the correct Agents are executed.

### Acceptance Criteria

```gherkin
Given a workflow contains a procurement request
When the Planner Agent runs
Then it identifies the workflow intent
And it identifies the procurement domain
And it returns a structured workflow plan
```

```gherkin
Given the request lacks required information
When the Planner Agent runs
Then it returns a missing information list
And the workflow does not proceed to calculation
```

---

# Epic 4 — Retrieval and Enterprise Knowledge

## US-006 — Retrieve Contract and Policy

As a Sales user,
I want the system to retrieve relevant contracts and policies,
so that the quotation follows existing business agreements.

### Acceptance Criteria

```gherkin
Given the workflow has customer and domain information
When the Retrieval Agent runs
Then it retrieves relevant contract information
And it retrieves relevant policy documents
And it returns citations for all retrieved facts
```

---

## US-007 — Retrieval Failure Handling

As a Manager,
I want the system to clearly indicate when required knowledge cannot be found,
so that I do not approve unsupported quotations.

### Acceptance Criteria

```gherkin
Given no relevant contract is found
When the Retrieval Agent completes
Then the retrieval result includes a warning
And the workflow is marked as requiring human review
```

---

# Epic 5 — Quotation Calculation

## US-008 — Generate Deterministic Quotation

As a Finance user,
I want the system to calculate quotations deterministically,
so that pricing outputs are reliable and auditable.

### Acceptance Criteria

```gherkin
Given product, quantity, unit price, discount and VAT are available
When the Calculator Agent runs
Then the quotation is calculated by a deterministic tool
And the output includes subtotal, discount, VAT and total
```

```gherkin
Given quantity is 50
And unit price is 980
And discount is 10 percent
And VAT is 8 percent
When the Calculator Agent runs
Then the grand total is 47628 USD
```

---

## US-009 — Multi-item Quotation

As a Sales user,
I want the system to support multiple products in one request,
so that complex procurement requests can be handled.

### Acceptance Criteria

```gherkin
Given a request contains multiple products
When the Calculator Agent runs
Then each item is calculated independently
And the quotation includes a grand total
```

---

# Epic 6 — Compliance Checking

## US-010 — Check Quotation Compliance

As a Legal user,
I want the system to check quotations against policies and contracts,
so that risky quotations are detected before approval.

### Acceptance Criteria

```gherkin
Given a quotation and retrieved policy documents exist
When the Compliance Agent runs
Then it returns a compliance status
And it returns risk level
And it lists missing clauses or violations
And it includes citations
```

---

## US-011 — Detect Missing Domain Clause

As a Legal user,
I want the system to detect missing domain-specific clauses,
so that generated quotations are legally complete.

### Acceptance Criteria

```gherkin
Given an IT equipment quotation
When the compliance check is performed
Then the result must confirm warranty terms are included
```

```gherkin
Given a software subscription quotation
When the compliance check is performed
Then the result must confirm data protection and renewal terms are included
```

---

# Epic 7 — Validation and Retry

## US-012 — Validate Agent Outputs

As a Manager,
I want the system to validate all Agent outputs,
so that incorrect data is caught before approval.

### Acceptance Criteria

```gherkin
Given all Agent outputs are available
When the Validation Agent runs
Then it validates schemas
And it validates required fields
And it validates calculation consistency
```

---

## US-013 — Retry Failed Step

As an Admin,
I want the workflow to retry a failed step when appropriate,
so that temporary failures do not break the workflow.

### Acceptance Criteria

```gherkin
Given the Validation Agent detects a calculation mismatch
When retry is allowed
Then the workflow routes back to the Calculator Agent
And retry_count is incremented
```

```gherkin
Given retry_count reaches the maximum limit
When validation fails again
Then the workflow status becomes FAILED
```

---

# Epic 8 — Human Approval

## US-014 — Manager Approves Workflow

As a Manager,
I want to approve a generated quotation,
so that the workflow can proceed to email preview generation.

### Acceptance Criteria

```gherkin
Given a workflow status is WAITING_APPROVAL
When I approve the workflow
Then the workflow status becomes APPROVED
And the workflow resumes to Email Agent
```

---

## US-015 — Manager Rejects Workflow

As a Manager,
I want to reject a generated quotation with a comment,
so that the requester understands why it was rejected.

### Acceptance Criteria

```gherkin
Given a workflow status is WAITING_APPROVAL
When I reject the workflow with a comment
Then the workflow status becomes REJECTED
And the rejection comment is stored
And no email preview is generated
```

---

# Epic 9 — Email Preview

## US-016 — Generate Email Preview

As a Sales user,
I want the system to generate a professional email preview,
so that I can respond to the customer faster.

### Acceptance Criteria

```gherkin
Given a workflow has been approved
When the Email Agent runs
Then it generates an email subject
And it generates an email body
And it includes quotation summary
And it includes payment terms
And it includes next steps
```

---

## US-017 — Prevent Email Before Approval

As a Manager,
I want the system to prevent customer-facing output before approval,
so that unapproved quotations are not sent externally.

### Acceptance Criteria

```gherkin
Given a workflow is not approved
When the Email Agent is requested
Then the system blocks email preview generation
```

---

# Epic 10 — Agent Monitor

## US-018 — View Workflow Progress

As a Sales user,
I want to see workflow progress visually,
so that I know which Agent is currently working.

### Acceptance Criteria

```gherkin
Given a workflow is running
When I open the Agent Monitor
Then I see each Agent node
And I see current status for each node
And I see started time, completed time and duration
```

---

## US-019 — View Agent Errors

As an Admin,
I want to see Agent errors,
so that I can debug failed workflows.

### Acceptance Criteria

```gherkin
Given an Agent fails
When I open the workflow detail page
Then I see the failed Agent name
And I see the error message
And I see retry count
```

---

# Epic 11 — Document Management

## US-020 — Upload Enterprise Documents

As a Legal or Finance user,
I want to upload contracts, policies and pricing documents,
so that Agents can use them during workflow execution.

### Acceptance Criteria

```gherkin
Given I have permission to upload documents
When I upload a document with a valid type
Then the document is stored
And metadata is saved
And the document is available for retrieval
```

---

## US-021 — Index Documents for Retrieval

As an Admin,
I want uploaded documents to be indexed into the vector store,
so that Retrieval Agent can search them.

### Acceptance Criteria

```gherkin
Given a supported document is uploaded
When indexing is triggered
Then the document is chunked
And embeddings are generated
And chunks are stored in Qdrant with metadata
```

---

# Epic 12 — Analytics and Audit

## US-022 — View Workflow Analytics

As a Manager,
I want to view workflow analytics,
so that I can evaluate operational efficiency.

### Acceptance Criteria

```gherkin
Given workflows have been executed
When I open the analytics dashboard
Then I see total workflows
And completed workflows
And failed workflows
And average processing time
And approval waiting time
```

---

## US-023 — View Audit Log

As an Admin,
I want every important system action to be audited,
so that the system is explainable and traceable.

### Acceptance Criteria

```gherkin
Given a workflow runs through multiple steps
When I view the audit log
Then I see all important events
And each event contains actor, timestamp, action and payload summary
```

---

# 7. Workflow State Specification

## 7.1 WorkflowState

```json
{
  "workflow_id": "string",
  "workflow_type": "procurement_quotation",
  "domain": "it_equipment",
  "status": "CREATED",
  "request": {
    "raw_text": "string",
    "source": "manual_text",
    "uploaded_document_ids": []
  },
  "customer": {
    "customer_id": "string",
    "name": "string",
    "contact_name": "string",
    "contact_email": "string",
    "risk_tier": "LOW"
  },
  "items": [
    {
      "product_id": "string",
      "name": "string",
      "quantity": 0
    }
  ],
  "planner": {},
  "retrieval": {},
  "quotation": {},
  "compliance": {},
  "validation": {},
  "approval": {},
  "email": {},
  "retry_count": 0,
  "events": [],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 7.2 Workflow Status

```text
CREATED
PLANNING
RETRIEVING
CALCULATING
CHECKING_COMPLIANCE
VALIDATING
WAITING_APPROVAL
APPROVED
REJECTED
GENERATING_EMAIL
COMPLETED
FAILED
CANCELLED
```

---

# 8. Phase Plan with Acceptance Criteria

# Sprint -1 — AI Development Framework

## Goal

Prepare the repository so Codex/Harness can implement the project consistently.

## Deliverables

```text
.ai/project/PROJECT_CONTRACT.md
.ai/project/ARCHITECTURE.md
.ai/project/TECH_STACK.md
.ai/project/CODING_STANDARD.md
.ai/project/FOLDER_STRUCTURE.md
.ai/project/STATE_CONTRACT.md
.ai/project/AGENT_CONTRACT.md
.ai/project/API_CONTRACT.md
.ai/project/DATABASE_CONTRACT.md
.ai/prompts/system.md
.ai/prompts/planner.md
.ai/prompts/implementer.md
.ai/prompts/reviewer.md
.ai/prompts/tester.md
.ai/templates/SPEC_TEMPLATE.md
.ai/templates/TASK_TEMPLATE.md
.ai/specs/SPEC_INDEX.md
datasets/
docs/demo/
```

## Acceptance Criteria

```gherkin
Given a new Codex session starts
When Codex reads the .ai/project files
Then it understands the product mission, architecture, tech stack and coding rules
```

```gherkin
Given Codex is assigned a task
When the task references a SPEC
Then Codex can identify in-scope and out-of-scope work
```

```gherkin
Given demo data is required
When the dataset folder is inspected
Then it contains customers, products, pricing rules, contracts, policies, RFQs and expected outputs
```

---

# Phase 1 — Infrastructure Foundation

## Goal

Build the backend foundation and infrastructure services.

## Included Specs

```text
SPEC-001 Bootstrap Backend
SPEC-002 Database Foundation
SPEC-003 Authentication and RBAC
SPEC-004 Storage Infrastructure
```

## User Stories Covered

```text
US-001 User Login
US-002 Role-based Access
US-020 Upload Enterprise Documents foundation only
```

## Acceptance Criteria

```gherkin
Given the repository is cloned
When docker compose up is executed
Then backend, postgres, redis, qdrant and minio start successfully
```

```gherkin
Given the backend is running
When GET /health is called
Then the API returns 200 OK
```

```gherkin
Given database migrations exist
When alembic upgrade head is executed
Then all Phase 1 tables are created
```

```gherkin
Given a valid user exists
When the user logs in
Then the system returns an access token and refresh token
```

```gherkin
Given an unauthorized user calls a protected endpoint
When the request is processed
Then the API returns 401 or 403
```

## Phase 1 Done Means

```text
Backend skeleton exists
Docker Compose works
Database connection works
Migrations work
JWT auth works
RBAC foundation works
Redis/Qdrant/MinIO clients are available
Tests pass
```

---

# Phase 2 — Core Workflow Engine

## Goal

Implement workflow state, lifecycle APIs, LangGraph runtime foundation and event streaming.

## Included Specs

```text
SPEC-005 Workflow State
SPEC-006 LangGraph Runtime
SPEC-007 Workflow API
SPEC-008 Event Streaming
```

## User Stories Covered

```text
US-003 Create Workflow from Text Request
US-004 Upload RFQ Document
US-018 View Workflow Progress foundation
US-019 View Agent Errors foundation
US-023 View Audit Log foundation
```

## Acceptance Criteria

```gherkin
Given a Sales user submits a valid request
When POST /api/v1/workflows is called
Then a workflow is created with status CREATED
```

```gherkin
Given a workflow exists
When POST /api/v1/workflows/{workflow_id}/run is called
Then the workflow transitions from CREATED to PLANNING
```

```gherkin
Given a workflow emits events
When the frontend subscribes to the workflow stream
Then the frontend receives workflow event updates
```

```gherkin
Given a workflow fails
When the workflow detail is requested
Then the API returns the failure state and error event
```

## Phase 2 Done Means

```text
WorkflowState is implemented
Workflow lifecycle is persisted
LangGraph can run placeholder nodes
Events are recorded
Workflow APIs exist
Streaming endpoint exists
Audit log foundation exists
```

---

# Phase 3 — Agent and Tool Implementation

## Goal

Implement specialized Agents and deterministic tools.

## Included Specs

```text
SPEC-009 Planner Agent
SPEC-010 Retrieval Agent
SPEC-011 Calculator Tool
SPEC-012 Compliance Agent
SPEC-013 Validation Agent
SPEC-014 Email Agent
```

## User Stories Covered

```text
US-005 Planner Agent Creates Workflow Plan
US-006 Retrieve Contract and Policy
US-007 Retrieval Failure Handling
US-008 Generate Deterministic Quotation
US-009 Multi-item Quotation
US-010 Check Quotation Compliance
US-011 Detect Missing Domain Clause
US-012 Validate Agent Outputs
US-013 Retry Failed Step
US-016 Generate Email Preview
US-017 Prevent Email Before Approval
```

## Acceptance Criteria

```gherkin
Given RFQ-001 exists in the demo dataset
When the workflow runs
Then Planner Agent identifies the domain as it_equipment
```

```gherkin
Given RFQ-001 references Acme Manufacturing Group
When Retrieval Agent runs
Then it retrieves CON-2026-ACME-IT
And it returns citations
```

```gherkin
Given RFQ-001 requires 50 laptops
When Calculator Agent runs
Then the grand total is 47628 USD
```

```gherkin
Given a quotation is generated
When Compliance Agent runs
Then it checks contract terms and internal policies
And returns PASS, WARNING or FAIL
```

```gherkin
Given an invalid quotation total exists
When Validation Agent runs
Then it detects the mismatch
And routes the workflow back to Calculator if retry is available
```

```gherkin
Given a workflow is not approved
When Email Agent is requested
Then email generation is blocked
```

```gherkin
Given a workflow is approved
When Email Agent runs
Then an email preview is generated
```

## Phase 3 Done Means

```text
All MVP Agents exist
All Agent outputs are structured
Calculator uses deterministic Python tool
Retrieval returns citations
Compliance returns risk report
Validation supports retry
Email preview requires approval
Mock LLM tests exist
```

---

# Phase 4 — Frontend Application

## Goal

Build the NextJS dashboard for operating and monitoring workflows.

## Included Specs

```text
SPEC-015 Frontend Bootstrap
SPEC-016 Authentication UI
SPEC-017 Dashboard
SPEC-018 Workflow List and Detail
SPEC-019 Agent Monitor
SPEC-020 Approval Center
SPEC-021 Document Management
```

## User Stories Covered

```text
US-001 User Login
US-003 Create Workflow from Text Request
US-014 Manager Approves Workflow
US-015 Manager Rejects Workflow
US-018 View Workflow Progress
US-019 View Agent Errors
US-020 Upload Enterprise Documents
US-022 View Workflow Analytics foundation
```

## Acceptance Criteria

```gherkin
Given a user opens the frontend
When the user is not authenticated
Then the user is redirected to the login page
```

```gherkin
Given a Sales user is logged in
When the user creates a workflow
Then the new workflow appears in the workflow list
```

```gherkin
Given a workflow is running
When the user opens Agent Monitor
Then the user sees Planner, Retrieval, Calculator, Compliance, Validation, Approval and Email nodes
```

```gherkin
Given a workflow is waiting for approval
When a Manager opens Approval Center
Then the Manager can approve or reject it
```

```gherkin
Given a document is uploaded
When upload succeeds
Then the document appears in Document Management
```

## Phase 4 Done Means

```text
Frontend can authenticate
Dashboard displays workflow summary
Workflow list works
Workflow detail works
Agent Monitor works
Approval Center works
Document upload UI works
Frontend integrates with backend APIs
```

---

# Phase 5 — Observability, Analytics and Demo

## Goal

Make the system explainable, measurable and demo-ready.

## Included Specs

```text
SPEC-022 Audit Log
SPEC-023 Analytics
SPEC-024 Demo Dataset Integration
SPEC-025 End-to-End Demo Flow
```

## User Stories Covered

```text
US-022 View Workflow Analytics
US-023 View Audit Log
```

## Acceptance Criteria

```gherkin
Given multiple workflows have run
When the analytics dashboard is opened
Then it shows workflow count, completion rate, failure rate and average duration
```

```gherkin
Given a workflow has completed
When the audit log is opened
Then it shows all Agent executions, approval decision and email preview generation
```

```gherkin
Given demo dataset is loaded
When RFQ-001 is executed
Then the workflow completes through approval and email preview
```

```gherkin
Given the demo is presented
When the Agent Monitor is shown
Then the audience can understand which Agent is running and what output it produced
```

## Phase 5 Done Means

```text
Demo dataset can be loaded
End-to-end RFQ demo works
Audit log is complete
Analytics dashboard works
Demo script is documented
System is presentation-ready
```

---

# Phase 6 — Deployment and Finalization

## Goal

Prepare the project for final delivery, demonstration and academic evaluation.

## Included Specs

```text
SPEC-026 Production Docker
SPEC-027 CI/CD
SPEC-028 Deployment Guide
SPEC-029 Final Documentation
```

## Acceptance Criteria

```gherkin
Given a clean environment
When deployment instructions are followed
Then the system starts successfully
```

```gherkin
Given a pull request is created
When CI runs
Then lint, tests and build checks pass
```

```gherkin
Given the final project is submitted
When the evaluator reads the documentation
Then they can understand architecture, workflow, Agents, database, APIs and demo process
```

## Phase 6 Done Means

```text
Production Docker files exist
CI/CD works
Deployment guide exists
Final report materials exist
Demo guide exists
Architecture documentation is complete
```

---

# 9. MVP Demo Acceptance Criteria

The MVP is considered successful when the following full scenario works.

## Demo Input

```text
We would like to purchase 50 standard business laptops for a new operations team.
We signed a master agreement in May 2026.
Please provide your best quotation with the applicable discount.
```

## Expected Result

```gherkin
Given the demo dataset is loaded
When the Sales user creates a workflow from the demo input
Then the system creates a workflow
And Planner identifies the domain as it_equipment
And Retrieval finds CON-2026-ACME-IT
And Retrieval applies 10 percent discount
And Calculator generates grand total 47628 USD
And Compliance returns PASS or LOW risk
And Validation returns valid true
And workflow status becomes WAITING_APPROVAL
And Manager approves the workflow
And Email Agent generates email preview
And workflow status becomes COMPLETED
```

---

# 10. Codex Implementation Rules

Codex must follow these rules for every task:

```text
Read project contract before implementation
Read current SPEC before implementation
Implement only the current task
Do not redesign architecture
Do not add frameworks without approval
Do not implement future phase features early
Keep each task small
Add tests
Update documentation
Run lint and tests
Report changed files
Stop after completing the assigned task
```

---

# 11. Recommended SPEC Breakdown for Codex

```text
SPEC-001 Bootstrap Backend
SPEC-002 Database Foundation
SPEC-003 Authentication and RBAC
SPEC-004 Storage Infrastructure
SPEC-005 Workflow State
SPEC-006 LangGraph Runtime
SPEC-007 Workflow API
SPEC-008 Event Streaming
SPEC-009 Planner Agent
SPEC-010 Retrieval Agent
SPEC-011 Calculator Tool
SPEC-012 Compliance Agent
SPEC-013 Validation Agent
SPEC-014 Email Agent
SPEC-015 Frontend Bootstrap
SPEC-016 Authentication UI
SPEC-017 Dashboard
SPEC-018 Workflow List and Detail
SPEC-019 Agent Monitor
SPEC-020 Approval Center
SPEC-021 Document Management
SPEC-022 Audit Log
SPEC-023 Analytics
SPEC-024 Demo Dataset Integration
SPEC-025 End-to-End Demo Flow
SPEC-026 Production Docker
SPEC-027 CI/CD
SPEC-028 Deployment Guide
SPEC-029 Final Documentation
```

---

# 12. Final Success Criteria

The project is successful when:

```text
A user can log in
A Sales user can create a workflow
The workflow can run through multiple specialized Agents
The system can retrieve contract and policy knowledge
The system can calculate a quotation deterministically
The system can check compliance
The system can validate outputs
A Manager can approve or reject the workflow
The system can generate an email preview
The dashboard can show real-time Agent progress
The system records audit logs
The demo dataset works end-to-end
The project can be deployed with Docker
The documentation explains architecture and implementation clearly
```

---

## Bản SPEC này nên được tách thành các file sau trong repo

```text
.ai/project/PRODUCT_SPEC.md
.ai/project/USER_STORIES.md
.ai/project/PHASE_ACCEPTANCE_CRITERIA.md
.ai/specs/SPEC_INDEX.md
```

Trong đó:

```text
PRODUCT_SPEC.md
```

lưu phần tổng quan sản phẩm.

```text
USER_STORIES.md
```

lưu toàn bộ User Stories.

```text
PHASE_ACCEPTANCE_CRITERIA.md
```

lưu Acceptance Criteria theo từng Phase.

```text
SPEC_INDEX.md
```

lưu danh sách SPEC để Codex thực thi theo thứ tự.
