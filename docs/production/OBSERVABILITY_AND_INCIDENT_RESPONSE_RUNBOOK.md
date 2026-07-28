# Observability And Incident Response Runbook

## Purpose And Scope

Use this runbook to operate and troubleshoot the production-demo stack and
future production-like environments.

This is documentation only. It does not add monitoring infrastructure,
alerting, external telemetry, provider automation, backend behavior, frontend
behavior, Docker/Compose behavior, CI behavior, API behavior, database schema,
real email sending, or final quotation behavior.

The current observability layer is production-demo visibility: structured logs,
request IDs, health/live/ready checks, protected in-process metrics, workflow
events, approval history, and audit logs. It is not a managed production
observability platform.

## Existing Observability Surfaces

| Surface | Current implementation | Use |
| --- | --- | --- |
| Request IDs | Backend request middleware/logging context | Correlate logs, API failures, and frontend/API reports. |
| Logs | Structlog JSON or text output with redaction support | Review route, status, bounded errors, startup, readiness, and runtime failures. |
| Redaction | `LOG_REDACTION_ENABLED=true` by default in production-demo env | Redact sensitive keys such as tokens, passwords, secrets, raw prompts, embeddings, and vector payloads. |
| `/health` | Backend process health | Confirms the backend process responds. |
| `/live` | Backend liveness | Confirms liveness independent of dependency readiness. |
| `/ready` | Bounded dependency readiness | Checks Postgres, Redis, Qdrant, and object storage readiness. |
| Metrics endpoint | `GET /api/v1/observability/metrics` for Admin/Manager | Bounded in-process request/counter metrics. Not a Prometheus/external monitoring setup. |
| Workflow events | Persisted `workflow_events` records and timeline API/UI | Trace workflow runtime stages, approval boundary, resume, and failures. |
| Audit logs | Persisted `audit_logs` records | Review workflow creation, status transitions, event append actions, and other audited operations. |

## Operational Checks

### Backend Health

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/live
```

Expected:

- backend process is reachable;
- response contains only safe service metadata.

### Readiness

```bash
curl -fsS http://localhost:8000/ready
```

Expected:

- status is ready when required dependencies are available;
- failed checks are bounded to safe dependency names and generic messages;
- no connection strings, passwords, tokens, or stack traces are exposed.

### Frontend Availability

```bash
curl -fsS http://localhost:3000/login
```

Manual route smoke:

- `/login`
- `/demo`
- `/agent-monitor`
- `/workflows`
- workflow detail route
- `/dashboard`

### Database Connectivity

Use `/ready` first. It runs a bounded non-mutating Postgres check.

If deeper inspection is needed, use operator-reviewed database tooling with
local untracked credentials. Do not paste credentials into docs, issue reports,
or screenshots.

### Redis, Qdrant, And MinIO Availability

Use `/ready` first. It checks:

- `postgres`
- `redis`
- `qdrant`
- `object_storage`

If `/ready` fails:

- inspect the specific failed dependency;
- check Compose service health;
- check env values;
- check logs;
- avoid destructive volume actions until the cause is understood.

### Metrics Endpoint

As Admin or Manager, when an access token is intentionally available:

```bash
curl -fsS \
  -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/observability/metrics
```

Rules:

- do not paste real tokens into docs or tickets;
- do not expose Authorization headers in screenshots;
- treat metrics as in-process demo visibility, not external monitoring;
- metrics must remain bounded and safe.

### Evaluation Runners

Use deterministic evaluation checks during pre-demo or post-incident review:

```bash
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
```

Expected:

- no live provider calls;
- no Telegram network calls;
- no database required;
- no real email sending.

## Incident Categories

### Backend Unavailable

Symptoms:

- `/health` or `/live` fails;
- frontend API calls fail;
- backend container exits or restarts repeatedly.

Initial checks:

- Compose service status;
- backend logs;
- env values;
- recent dependency, migration, or configuration changes.

### Database Unavailable

Symptoms:

- `/ready` reports Postgres failed;
- migrations fail;
- login/workflow APIs fail.

Initial checks:

- `DATABASE_URL`;
- Postgres service health;
- credentials from local untracked env;
- volume availability;
- recent migration activity.

### Frontend Build Or Runtime Issue

Symptoms:

- frontend route does not load;
- login page unavailable;
- static build fails;
- API base URL points to wrong backend.

Initial checks:

- `NEXT_PUBLIC_API_BASE_URL`;
- `NEXT_PUBLIC_WS_BASE_URL`;
- frontend build output;
- browser network panel without exposing tokens.

### Telegram Bridge Failure

Symptoms:

- bot does not reply;
- supported RFQ does not create workflow;
- created workflow does not auto-run to `WAITING_APPROVAL`.

Initial checks:

- local `TELEGRAM_BOT_TOKEN`;
- bridge process logs;
- backend availability;
- manager credentials in local env;
- dry-run mode;
- ensure no live price research or auto-approval expectation exists.

### Provider Key Leak

Symptoms:

- token/key appears in logs, screenshots, shell history, issue report, or Git;
- provider dashboard shows suspicious usage.

Initial checks:

- stop using the key;
- rotate/revoke at provider;
- search tracked files and recent diffs;
- review screenshots/logs/evidence packages;
- update local ignored overrides.

### Live Provider Smoke Failure

Symptoms:

- manual Tavily/provider smoke fails;
- provider returns timeout, non-2xx, invalid JSON, or low-confidence evidence.

Initial checks:

- confirm live smoke is optional/manual;
- confirm dry-run still works;
- confirm key is local and not committed;
- do not wire live provider failure into Telegram/workflow runtime;
- label evidence as reference-only if present.

### Outbound Preview Policy Block

Symptoms:

- preview unavailable;
- outbound panel shows blocked state;
- operator expects email sending.

Initial checks:

- `OUTBOUND_COMMUNICATION_ENABLED`;
- workflow status;
- approval/resume evidence;
- preview evidence;
- remember `OUTBOUND_SEND_ENABLED=false` and no send endpoint exists.

### Suspicious Final-Quote Or Send Claim

Symptoms:

- UI, Telegram reply, logs, docs, or operator script implies final quote,
  stock availability, delivery date, discount approval, email sent, auto-send,
  auto-approval, or auto-resume.

Initial response:

- stop the demo or release action;
- preserve evidence;
- identify the source text or code path;
- do not approve release until corrected;
- confirm Manager/Admin approval and explicit resume remain the boundary.

### Dependency/Security Alert

Symptoms:

- `npm audit` reports tracked findings;
- new advisory appears;
- provider or framework publishes a security notice.

Initial checks:

- read `docs/security/SECURITY_TRIAGE_REPORT.md`;
- read `docs/security/SPEC_025_REMEDIATION_MATRIX.md`;
- do not run `npm audit fix --force`;
- open a bounded dependency/security task for remediation;
- keep stable demo defaults unchanged.

## Incident Response Checklist

### 1. Detect

- [ ] Record timestamp and environment.
- [ ] Capture route, workflow ID, request ID, command, or service name.
- [ ] Preserve bounded logs.
- [ ] Avoid copying tokens, cookies, provider payloads, raw prompts,
  embeddings, vector payloads, or chain-of-thought.

### 2. Assess Blast Radius

- [ ] Determine affected service: frontend, backend, Postgres, Redis, Qdrant,
  MinIO, Telegram bridge, provider smoke, outbound preview, or docs.
- [ ] Determine whether data integrity may be affected.
- [ ] Determine whether secrets may be exposed.
- [ ] Determine whether approval/resume/final-quote boundaries may be affected.
- [ ] Determine whether release/demo can continue safely.

### 3. Preserve Logs And Evidence

- [ ] Save bounded logs outside the repository.
- [ ] Record request IDs.
- [ ] Record workflow IDs.
- [ ] Record command names and exit statuses.
- [ ] Record screenshots only after redaction review.
- [ ] Preserve database/storage state before destructive investigation.

### 4. Rotate Secrets When Needed

Use `docs/production/SECRETS_AND_PROVIDER_KEYS_RUNBOOK.md`.

- [ ] Revoke/rotate exposed provider keys.
- [ ] Rotate Telegram token if exposed.
- [ ] Rotate JWT secret if token signing key exposure is suspected.
- [ ] Rotate database or MinIO credentials if exposed.
- [ ] Restart affected services.
- [ ] Re-run smoke checks.

### 5. Disable Risky Feature Flags

For stable recovery, prefer:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
PRICE_RESEARCH_ENABLED=false
RAG_ENABLED=false
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
TELEGRAM_LLM_EXTRACTION_ENABLED=false
TELEGRAM_SALES_REPLY_ENABLED=false
```

Do not enable live providers, RAG, outbound preview, Telegram LLM extraction, or
sales replies during incident recovery unless they are the specific surface
being tested and an operator explicitly approves it.

### 6. Rollback

Use `docs/production/BACKUP_RESTORE_AND_MIGRATION_RUNBOOK.md`.

- [ ] Stop services without deleting volumes.
- [ ] Restore known-good env values from secure local storage.
- [ ] Restore known-good images or commit.
- [ ] Preserve state before overwriting volumes.
- [ ] Run health/readiness checks.
- [ ] Run workflow smoke checks.

### 7. Post-Incident Notes

- [ ] Summarize impact.
- [ ] Record root cause if known.
- [ ] Record validation commands and results.
- [ ] Record follow-up tasks.
- [ ] Do not include secrets or raw sensitive payloads.

## Logging And Redaction Policy

Keep production-demo settings aligned to:

```text
LOG_FORMAT=json
LOG_REDACTION_ENABLED=true
METRICS_ENABLED=true
METRICS_ROUTE_ENABLED=true
```

Do not log or share:

- provider keys;
- Telegram tokens;
- JWTs or refresh tokens;
- cookies;
- Authorization headers;
- database credentials;
- MinIO credentials;
- raw prompts;
- raw provider payloads;
- raw model output;
- embeddings or vector payloads;
- chain-of-thought;
- real customer data.

Safe incident evidence includes:

- request ID;
- route template;
- HTTP status class;
- bounded error category;
- service name;
- dependency readiness status;
- workflow ID;
- event count;
- approval decision status without sensitive comments when sharing publicly.

## Audit Trail Expectations

Postgres stores audit and event evidence:

- `workflow_events` records runtime and workflow timeline activity;
- `audit_logs` records important system actions with workflow/resource
  references and bounded JSON payloads;
- approval history is part of the human approval/resume lifecycle.

Expected use:

- use workflow events to explain what the runtime did;
- use audit logs to verify important state transitions and event append
  actions;
- use approval history to verify Manager/Admin decisions;
- do not treat logs alone as durable audit proof;
- do not expose raw payloads publicly without redaction review.

## Escalation And Owner Placeholders

Fill these placeholders before production-like operation:

| Area | Primary owner | Backup owner | Escalation channel | Notes |
| --- | --- | --- | --- | --- |
| Application backend | TBD | TBD | TBD | FastAPI, workflow runtime, health/readiness. |
| Frontend | TBD | TBD | TBD | Violet Operations Console routes and API config. |
| Database/storage | TBD | TBD | TBD | Postgres, Redis, MinIO, Qdrant. |
| Secrets/provider keys | TBD | TBD | TBD | Rotation, revocation, key storage. |
| Telegram demo bridge | TBD | TBD | TBD | Local demo bridge only. |
| Security/dependencies | TBD | TBD | TBD | SPEC-024/SPEC-025 carryover. |
| Release manager | TBD | TBD | TBD | Release gate and rollback decisions. |

## Post-Incident Review Template

```text
Incident title:
Date/time detected:
Environment:
Detected by:
Affected services:
Workflow IDs:
Request IDs:
User-visible impact:
Data integrity impact:
Secret exposure suspected: yes/no
Approval/resume boundary affected: yes/no
Provider/live web/email behavior involved: yes/no
Immediate mitigation:
Rollback performed: yes/no
Validation commands run:
Validation result:
Root cause:
Corrective actions:
Follow-up SPEC/task:
Notes redacted for public sharing:
```

## Known Limitations And Future Work

Current limitations:

- no external monitoring vendor integration;
- no alert manager;
- no OpenTelemetry exporter;
- no Prometheus scrape configuration;
- no centralized log storage;
- no production incident rota;
- no automated rollback;
- no production backup automation;
- no managed secret store;
- no live provider automation in default workflows;
- no real email sending or outbound send endpoint.

Future work should add:

- external observability integration;
- alert thresholds and escalation policy;
- centralized log retention;
- production runbook ownership;
- automated smoke evidence capture;
- backup/restore rehearsal automation;
- formal incident severity definitions;
- production SLOs after real deployment architecture is selected.
