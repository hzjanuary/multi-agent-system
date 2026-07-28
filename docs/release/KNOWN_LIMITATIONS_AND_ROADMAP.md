# Known Limitations And Roadmap

## Purpose

This document records release limitations honestly and lists bounded future
work. It prevents the final package from implying capabilities that are not
implemented in the current repository.

## Current Release Limitations

### Outbound Communication

- No real email sending.
- No outbound send endpoint.
- No Gmail/SMTP/Resend production provider integration.
- Approved communication is preview-only.
- Preview loading requires the completed approval/resume lifecycle and explicit
  preview evidence.

### Quotation And Approval

- No final customer quotation is produced before Manager/Admin approval and
  explicit resume.
- No automatic approval.
- No automatic resume.
- No autonomous customer-ready quote issuance.
- Reference evidence is review material only.

### Provider And Price Research

- No automatic live provider calls in the stable demo.
- No Telegram live price research.
- No Tavily/live web calls from Telegram or workflow runtime.
- Provider live verification is manual-only and not part of CI.
- Price research foundations exist as schemas/providers/reference evidence,
  but they are disabled by default and not an autonomous quotation system.
- Prices are not inferred from unstructured prose.

### Catalog

- The deterministic catalog is demo-focused.
- Catalog support means the system can normalize a bounded item family for
  workflow intake.
- Catalog support is not a stock, delivery, supplier, discount, price, approval,
  or final quotation claim.
- Unsupported or mixed unsupported requests must fail closed or ask for
  clarification.

### Deployment And Operations

- No real cloud production deployment automation.
- No Kubernetes.
- No Terraform.
- No production secret vault.
- No enterprise SSO.
- No production backup automation.
- Production-demo Docker Compose exists for operational credibility, not as a
  claim of hardened cloud deployment.

### Documents And Knowledge

- No production OCR/PDF parsing pipeline.
- No upload/admin document management UI.
- RAG is optional and requires explicit demo knowledge ingestion.
- RAG evidence appears only when enabled and supplied by workflow state.

### Frontend And Monitoring

- Agent Monitor and workflow detail are demo/operator observation surfaces.
- They render explicit workflow state and API data only.
- They do not fabricate events, agent activity, catalog metadata, reference
  evidence, prices, approvals, or outbound communication.

### Dependency And Security Maintenance

- Frontend `npm audit` currently reports tracked high-severity findings.
- SPEC-024 Sprint 1 documents triage and maintenance policy.
- SPEC-024 Sprint 2 applies bounded frontend patch updates for `next`,
  `eslint-config-next`, and `postcss`.
- SPEC-024 is closed with the remaining 12 high npm audit findings documented
  and deferred.
- `npm audit fix` and `npm audit fix --force` require a separate reviewed
  maintenance sprint.
- Remaining audit findings require force/major or nested framework remediation
  and are deferred.
- Backend outdated review should be rerun in an environment with Poetry
  available.

## Stable Safety Boundaries

The release must preserve:

- deterministic no-key demo defaults;
- Manager/Admin approval before resume;
- `/run` stopping at `WAITING_APPROVAL`;
- `/resume` as the only post-approval continuation path;
- preview-only outbound communication;
- manual-only provider live verification;
- no secrets in committed files;
- no raw prompts, provider payloads, embeddings, vector payloads, tokens,
  cookies, passwords, or chain-of-thought in docs, UI, logs, metrics, tests, or
  screenshots.

## Bounded Roadmap

### 1. Approved Outbound Send Spec

Future work may add a real send path only after a dedicated spec defines:

- provider selection;
- recipient policy;
- audit record model;
- approval requirements;
- retry behavior;
- redaction rules;
- operator controls;
- tests and release gates.

### 2. Provider Policy Enforcement Automation

Future provider work should add:

- provider registry governance;
- key handling policy;
- rate-limit and timeout enforcement;
- citation quality checks;
- source trust labels;
- audit storage for live reference evidence;
- no-CI-key enforcement.

### 3. Expanded Catalog Governance Automation

Future catalog work should add:

- catalog admin review workflow;
- versioned catalog import/export;
- alias approval;
- add-on compatibility policy;
- unsupported item escalation;
- catalog evidence audit trail.

### 4. Richer Evaluation Reports

Future evaluation work should add:

- deterministic benchmark report generation;
- historical benchmark comparisons;
- manual smoke result templates;
- evaluator signoff package;
- optional CI integration for no-key/no-network benchmarks.

### 5. Production Hardening

SPEC-026 starts production-hardening planning with:

- `docs/production/PRODUCTION_ENVIRONMENT_CHECKLIST.md`
- `docs/production/SECRETS_AND_PROVIDER_KEYS_RUNBOOK.md`

Future production work should add:

- cloud deployment automation;
- managed secrets;
- enterprise SSO;
- backup and restore automation;
- operational SLOs;
- incident runbooks;
- external observability integration;
- production data-retention policies.

### 6. Document Management And OCR

Future document work should add:

- upload/admin document management UI;
- OCR/PDF parsing;
- document versioning;
- retention and redaction policy;
- ingestion review controls.

### 7. Dependency And Security Patch Sprint

Future security maintenance should add:

- reviewed frontend patch/minor upgrades where compatible;
- rerun npm audit after patching;
- Poetry-based backend outdated review;
- full backend/frontend/all-gates validation after dependency changes;
- separate major upgrade specs for framework-level changes.

## Non-Roadmap Claims

The roadmap does not mean these capabilities already exist. Do not present them
as implemented until a future spec delivers and validates them.
