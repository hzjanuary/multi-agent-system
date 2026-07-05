# ARCHITECTURE

## System Overview

Enterprise Multi-Agent OS is a workflow orchestration platform for complex business processes. Procurement is the first implemented domain.

```text
NextJS Dashboard
    |
FastAPI API Gateway
    |
LangGraph Workflow Runtime
    |
Specialized Agent Layer
    |
+-- PostgreSQL
+-- Redis
+-- Qdrant
+-- MinIO
+-- LLM Providers
```

## Architectural Style

- Clean Architecture
- Async-first backend
- State-driven orchestration
- Tool-based Agent execution
- Explicit human-in-the-loop control
- Observable workflow execution

## Backend Responsibilities

- Authentication and RBAC
- Workflow lifecycle management
- Document upload and indexing
- Agent orchestration
- Event streaming
- Approval handling
- Audit logging
- Analytics API

## Frontend Responsibilities

- Login
- Dashboard
- Workflow List
- Workflow Detail
- Agent Monitor
- Approval Center
- Document Management
- Analytics

## Workflow Runtime

LangGraph controls workflow state transitions, retry behavior, interruption for approval, and resume behavior.

## Agent Runtime

Agents do not own workflow state. They receive structured input and return structured output. The workflow engine merges outputs into WorkflowState.

## Data Flow

1. User creates a workflow from an RFQ/email/document.
2. Planner produces a workflow plan.
3. Retrieval fetches contracts, policies, pricing and citations.
4. Calculator generates deterministic quotation data.
5. Compliance checks quotation against policies and contracts.
6. Validation checks schema and business rules.
7. Human approval interrupts workflow.
8. Email Agent generates preview after approval.
9. Workflow completes and audit trail is stored.
