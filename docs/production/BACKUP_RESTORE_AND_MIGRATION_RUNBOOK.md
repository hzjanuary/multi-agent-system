# Backup, Restore, And Migration Runbook

## Purpose And Scope

Use this runbook to plan backup, restore, rollback, and migration safety for the
production-demo stack and future production-like environments.

This is documentation only. It does not add backup automation, restore
automation, migration automation, new scripts, database schema changes, Docker
or Compose changes, CI behavior, provider calls, real email sending, or final
quotation behavior.

The current production-demo stack uses Docker Compose named volumes. Treat this
runbook as an operator checklist and planning baseline, not as proof that
production-grade backup automation exists.

## Current Storage Components

| Component | Compose service | Production-demo volume | Main data |
| --- | --- | --- | --- |
| Postgres | `postgres` | `postgres_prod_data` | Users, roles, workflows, workflow events, approval history, audit logs, workflow state JSON. |
| Redis | `redis` | `redis_prod_data` | Cache/pub-sub state for event streaming paths. |
| MinIO | `minio` | `minio_prod_data` | Demo knowledge source objects and object-storage data. |
| Qdrant | `qdrant` | `qdrant_prod_data` | Vector collections for optional RAG/knowledge evidence. |

Local development uses similarly named non-production volumes from
`docker-compose.yml`. Do not mix local development volumes with
production-demo volumes during restore.

## Backup Planning

### Postgres Logical Backup Planning

Postgres is the primary durable system of record for workflow state, approvals,
events, and audit logs. Prefer logical backups with `pg_dump` for
production-demo portability.

Operator-reviewed example:

```bash
mkdir -p /tmp/multi-agent-system-backups
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example \
  exec -T postgres pg_dump \
  -U enterprise_os \
  enterprise_os \
  > /tmp/multi-agent-system-backups/postgres-demo-backup.sql
```

Before using this command in a real production-like environment:

- replace example database names through the local untracked env values;
- do not paste real passwords into docs or shell history;
- confirm the backup target is outside the repository;
- record repository commit, image tag, env file identity, and backup timestamp;
- protect the SQL file as sensitive because it may contain workflow, user,
  approval, and audit data.

### Redis Persistence And Backup Expectations

Redis supports operational event-streaming/cache paths. Postgres remains the
durable source for persisted workflow events and audit logs.

Planning expectations:

- define whether Redis state is disposable for the target environment;
- if Redis state must be preserved, use Redis-native persistence/export in a
  future runbook task;
- do not treat Redis as the source of truth for approvals, workflow state, or
  audit history;
- after Redis loss, validate persisted workflow event backlog and live timeline
  behavior separately.

### MinIO Bucket/Object Backup Planning

MinIO stores object data such as demo knowledge documents.

Planning expectations:

- back up the configured `MINIO_BUCKET_NAME`;
- prefer MinIO client or operator-controlled object backup tooling;
- keep MinIO private to the deployment network unless a future hardening task
  explicitly changes exposure;
- store object backups outside the repository;
- treat object backups as sensitive if they contain customer RFQs, policies, or
  knowledge documents.

Operator-reviewed example template:

```bash
# Example only. Configure mc locally outside the repository first.
mc mirror enterprise-os/enterprise-multi-agent-os \
  /tmp/multi-agent-system-backups/minio-bucket
```

### Qdrant Collection Export/Snapshot Planning

Qdrant stores vector collections for optional RAG/knowledge demos.

Planning expectations:

- prefer Qdrant-native snapshot/export tooling for real production-like use;
- document collection names before backup;
- treat vector payloads and metadata as sensitive;
- do not expose Qdrant publicly just to perform backup;
- if direct volume copy is used, stop the stack first and record image/env
  versions.

For deterministic demo data, Qdrant may be rebuilt by explicit knowledge
ingestion when that is acceptable:

```bash
docker compose run --rm backend-test \
  python -m app.knowledge.ingest_demo --confirm-local-demo
```

Do not add auto-ingestion to application startup.

## Restore Planning

### Restore Order

Restore into a stopped or isolated stack. Do not restore into a live
environment receiving traffic.

Recommended order:

1. Confirm rollback target commit/image/env identity.
2. Stop application services.
3. Preserve current volumes before overwriting anything.
4. Restore environment values from a secure operator location.
5. Restore Postgres.
6. Restore MinIO object data.
7. Restore Qdrant snapshots or rerun deterministic knowledge ingestion if that
   is acceptable for the demo.
8. Start infrastructure services.
9. Start backend and frontend.
10. Run health, readiness, smoke, and workflow checks.

### Restore Validation Checklist

- [ ] `docker compose config` passes.
- [ ] Production-demo Compose config passes.
- [ ] Postgres container is healthy.
- [ ] Redis container is healthy.
- [ ] Qdrant container is healthy.
- [ ] MinIO container is healthy.
- [ ] Backend `/health` returns success.
- [ ] Backend `/live` returns success.
- [ ] Backend `/ready` returns success after dependencies settle.
- [ ] Frontend login page loads.
- [ ] Manager/Admin login works with intended environment credentials.
- [ ] Workflow list loads.
- [ ] Workflow detail loads.
- [ ] Workflow events and approval history are present for expected workflows.
- [ ] Optional knowledge search works only when MinIO/Qdrant data or explicit
  ingestion is present.
- [ ] No real email sending, auto-approval, auto-resume, live provider call, or
  final quote behavior appears.

### Rollback Criteria

Rollback rather than continue when:

- migrations fail or leave schema version uncertain;
- `/ready` fails for required dependencies after normal startup time;
- workflow run/approval/resume safety semantics change;
- auth tokens cannot be validated after expected secret rotation behavior;
- Postgres restore validation fails;
- MinIO or Qdrant restore cannot be verified for a RAG-required demo;
- logs show repeated unhandled exceptions or unsafe secret exposure;
- the operator cannot prove which env file, image, or backup was restored.

No zero-downtime rollback automation exists. A rollback is complete only after
health/readiness and smoke checks pass.

## Migration Safety

### Alembic Migration Review

The backend uses Alembic under `backend/alembic/`.

Current migration command used by demo docs:

```bash
docker compose run --rm backend-test alembic upgrade head
```

Before any production-like migration:

- inspect the migration file under `backend/alembic/versions/`;
- confirm `upgrade()` and `downgrade()` behavior is understood;
- confirm the migration does not silently drop data;
- confirm affected tables and indexes are known;
- confirm backup exists and can be restored;
- confirm a smoke-test plan exists;
- confirm maintenance window and rollback criteria are defined.

### Pre-Migration Backup

Do not run production migrations blindly.

Pre-migration checklist:

- [ ] Freeze new deployment changes.
- [ ] Record current Git commit and image tags.
- [ ] Record current Alembic revision.
- [ ] Run Postgres backup.
- [ ] Preserve object/vector data if the migration affects knowledge/RAG
  behavior.
- [ ] Store backup artifacts outside the repository.
- [ ] Confirm restore command or operator procedure is available.
- [ ] Confirm no real secrets are copied into evidence.

### Migration Dry-Run Checklist

Use non-production data or an isolated copy where practical.

Checklist:

- [ ] Build backend test/runtime image from the target commit.
- [ ] Restore a copy of the database into an isolated environment.
- [ ] Run `alembic upgrade head` against the isolated copy.
- [ ] Run backend tests or focused smoke where practical.
- [ ] Run `/health`, `/live`, and `/ready`.
- [ ] Verify workflow list/detail for representative workflows.
- [ ] Verify approval/resume lifecycle for a safe test workflow.
- [ ] Verify audit logs and workflow events remain readable.
- [ ] Document migration duration and warnings.

### Downgrade And Rollback Expectations

Alembic downgrade support may exist for individual migrations, but downgrade is
not a substitute for a verified backup.

Rollback expectations:

- prefer restoring a known-good backup when data safety is uncertain;
- do not run destructive downgrade commands without operator review;
- never delete volumes as a first response;
- keep application services stopped while restoring database state;
- rerun smoke checks after rollback;
- record what changed and what was restored.

## Data Retention And Privacy Notes

Production-like data may include:

- user records;
- workflow request text;
- approval decisions and comments;
- workflow events;
- audit logs;
- object-storage documents;
- vector metadata;
- reference evidence.

Privacy rules:

- do not store real customer data in demo environments unless a future policy
  explicitly permits it;
- keep backups encrypted or in a secure operator-controlled location;
- define retention periods before production use;
- define deletion and restore-from-backup implications before production use;
- redact tokens, provider payloads, raw prompts, embeddings, vector payloads,
  chain-of-thought, and customer personal data from shared evidence.

## Demo Versus Production Data Boundary

Demo data:

- deterministic;
- safe for local board-demo use;
- explicitly seeded by command;
- not customer production data;
- may be rebuilt with seed and optional ingestion commands.

Production-like data:

- must use real secrets outside Git;
- must be backed up before migrations;
- must have retention and restore expectations;
- must not rely on automatic demo seed or automatic knowledge ingestion;
- must not be mixed with demo credentials or local-demo records.

## Disaster Recovery Checklist

- [ ] Identify incident start time and affected environment.
- [ ] Stop risky traffic or demo actions if data integrity is uncertain.
- [ ] Preserve logs and request IDs.
- [ ] Preserve current volumes before overwriting or deleting anything.
- [ ] Confirm whether Postgres, MinIO, Qdrant, or Redis is affected.
- [ ] Confirm latest known-good backup and env identity.
- [ ] Restore into an isolated stack when possible.
- [ ] Validate `/health`, `/live`, `/ready`.
- [ ] Validate workflow, event, approval, and audit data.
- [ ] Validate frontend access and operator login.
- [ ] Keep `OUTBOUND_SEND_ENABLED=false`.
- [ ] Do not call live providers or send real email during recovery.
- [ ] Record post-recovery notes without exposing secrets.

## Commands

These commands use existing repository tools or clearly marked service-native
examples. Review destructive actions before running them.

### Non-Destructive Checks

```bash
git status --short
git diff --check
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
curl http://localhost:8000/health
curl http://localhost:8000/live
curl http://localhost:8000/ready
```

### Migration Command

```bash
docker compose run --rm backend-test alembic upgrade head
```

Run this only after backup and migration review for production-like data.

### Postgres Backup Example

```bash
mkdir -p /tmp/multi-agent-system-backups
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example \
  exec -T postgres pg_dump \
  -U enterprise_os \
  enterprise_os \
  > /tmp/multi-agent-system-backups/postgres-demo-backup.sql
```

This is an example. Use actual untracked deployment values for real
environments without committing secrets.

### Safe Shutdown

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example down
```

This stops services without deleting volumes.

### Destructive Commands

Commands that remove volumes, drop databases, overwrite object stores, or
delete vector collections require explicit operator review and are intentionally
not listed as mandatory steps in this runbook.

## Known Limitations And Future Work

Current limitations:

- no production backup automation;
- no scheduled backup verification;
- no automated restore rehearsal;
- no production data-retention automation;
- no managed secret store;
- no zero-downtime migration or rollback;
- no cloud deployment automation;
- Qdrant and MinIO backup procedures are operator-planned, not scripted here;
- Redis persistence requirements are not formalized for production.

Future work should add:

- managed backup storage;
- restore rehearsal automation;
- migration preflight tooling;
- production retention policy;
- environment-specific recovery objectives;
- documented RPO/RTO targets;
- cloud or managed-service backup procedures when deployment architecture is
  selected.
