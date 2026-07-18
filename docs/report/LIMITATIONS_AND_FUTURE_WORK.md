# Limitations And Future Work

This document is a report-ready source for honest limitations and future work.
It should be updated only when a later task changes implemented scope or
captures final evidence.

## Current Limitations

### Production Scope

The system includes a production-demo Docker Compose stack, but it does not
implement cloud deployment automation, Kubernetes, Terraform, autoscaling,
managed database provisioning, or zero-downtime deployment. The deployment
surface is suitable for a controlled demo server, not a complete production
SaaS platform.

### Secrets And Identity

Secrets are configured through environment variables and placeholder templates,
but there is no production secret vault integration. Authentication uses local
JWT-based accounts and RBAC. Enterprise SSO, MFA, SCIM provisioning, and
centralized identity governance are not implemented.

### Approval Operations

The approval flow supports approve, reject, request changes, history, RBAC, and
explicit resume. It does not include configurable multi-step approval chains,
approval delegation, escalation policies, SLA timers, notification delivery, or
an admin approval-policy builder UI.

### Email Delivery

The system prepares post-approval email preview content but does not send
production email. This is intentional for the MVP safety boundary: customer-
facing output must remain human-controlled.

### Document Management

The RAG knowledge base uses deterministic demo documents and explicit ingestion.
It does not implement arbitrary frontend upload, admin document management,
document deletion/editing, enterprise document permissions, production OCR/PDF
parsing, external document connectors, or large-scale ingestion pipelines.

### RAG And LLM Evaluation

The default evaluation path uses fake/no-key providers. Optional real LLM
providers are available behind feature flags, but the report must not claim
real-provider benchmark results unless later evidence captures them. RAG
evidence is bounded and demo-oriented; it should support review, not replace
legal or financial judgment.

### Observability

The backend includes structured logging, request IDs, readiness checks, and
bounded in-process metrics. It does not include Prometheus scrape
configuration, OpenTelemetry exporters, external telemetry vendors, long-term
metrics retention, alerting, or provider cost dashboards.

### Multi-Tenancy

The system has role-based access control, but it does not implement full
multi-tenant isolation, tenant-scoped knowledge indexes, tenant-specific
encryption policies, or tenant billing.

### Frontend Scope

The frontend supports the workflow, approval, timeline, evidence, and knowledge
demo surfaces. It does not include broad enterprise administration,
provider-management UI, upload UI, billing UI, or advanced analytics dashboards.

## Future Work

### Configurable Approval Chains

Add policy-driven approval chains with configurable reviewer groups,
thresholds, delegation, escalation, and audit reporting. This should remain
backend-authoritative and test-covered before adding admin UI.

### Admin Document Management

Add document upload, catalog management, versioning, deletion rules, and
permission-aware retrieval. This should include safe file validation and clear
document lifecycle ownership before supporting production documents.

### Production OCR And External Connectors

Add OCR/PDF parsing and connectors for enterprise document systems only after
security, permissions, and ingestion limits are specified.

### Enterprise Identity

Add SSO/MFA integration, centralized user provisioning, and enterprise audit
alignment. This should not weaken the current RBAC source-of-truth boundary.

### Secret Vault And Key Management

Integrate a production secret vault and provider key-management policy. The
system should continue to support no-key deterministic demos for evaluation.

### Production Email And Notifications

Add explicit post-approval notification and email delivery after defining
approval, audit, retry, and failure semantics. Automatic sending should remain
policy-controlled.

### Cloud Deployment Automation

Plan and implement a cloud target, Terraform or equivalent infrastructure code,
reverse proxy/HTTPS automation, backup automation, and rollback strategy when
the project moves beyond the bounded production-demo stack.

### External Telemetry And Alerting

Add OpenTelemetry or Prometheus integration, alerting, dashboards, and log
retention after defining privacy and redaction requirements.

### Provider Operations

Add provider-management UI, cost dashboard, quota visibility, and provider
health reports after the provider abstraction and security model are mature.

### Token Streaming Or Advanced AI UX

Token streaming may be useful for future AI-native interfaces, but it is not
required for the controlled workflow dashboard. Agent thought streaming should
remain out of scope unless a safe explainability model is explicitly approved.

### Multi-Tenant Isolation

Add tenant-scoped users, workflows, knowledge collections, object storage
prefixes, audit boundaries, and configuration only after a dedicated multi-
tenancy spec defines ownership and security rules.
