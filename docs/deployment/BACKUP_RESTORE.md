# Backup, Restore, And Rollback Basics

SPEC-014 does not implement production-grade backup automation or rollback
automation. This guide records the current operator responsibilities for the
production-demo Docker Compose stack.

## Stateful Volumes

The production-demo stack uses named volumes for:

- Postgres data
- Qdrant data
- MinIO data

Treat these volumes as the source of state for workflows, audit records,
approval history, vector chunks, and stored demo knowledge documents.

## Backup Guidance

Prefer service-native backups when possible.

Postgres:

```bash
docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > postgres-demo-backup.sql
```

If environment variables are not available inside your shell, substitute the
deployment values from the untracked env file. Do not paste secrets into docs
or commit backup commands containing real credentials.

MinIO:

- Use MinIO client tooling or an operator-controlled object backup workflow.
- Back up the configured bucket contents.
- Do not expose MinIO publicly just to perform backups.

Qdrant:

- Prefer Qdrant snapshot/export tooling for a real deployment.
- For the current demo stack, snapshot scripting is deferred.
- If copying the named volume directly, stop the stack first.

Volume copy fallback:

- Stop services before copying named volumes.
- Copy only from a trusted host.
- Record the image tag/build and env file used with the backup.
- Never copy untracked env files into source control.

## Restore Guidance

Restore should happen into a stopped or isolated stack:

1. Stop the stack.
2. Restore the env file from a secure operator location.
3. Restore Postgres with service-native tools.
4. Restore MinIO bucket data.
5. Restore Qdrant data or re-run deterministic knowledge ingestion if
   acceptable for the demo.
6. Start the stack.
7. Run `/health`, `/live`, and `/ready`.
8. Run `bash scripts/deployment/smoke-prod-demo.sh --include-ready`.

Knowledge ingestion is deterministic and idempotent, so a demo Qdrant
collection can be reconstructed by re-running:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

Use a production-demo-targeted one-off command when restoring a separate
production-demo volume/network. Do not add auto-ingestion to startup.

## Rollback Basics

No zero-downtime rollback automation exists.

Operator rollback flow:

1. Keep the previous image tag/build and env file available.
2. Stop the current stack.
3. Restore the previous env file if it changed.
4. Start the previous backend/frontend images.
5. Confirm `GET /health` and `GET /live`.
6. Confirm `GET /ready` after dependencies settle.
7. Run the smoke script.
8. Verify the board-demo path manually if the rollback is demo-critical.

Do not claim a rollback is complete until smoke checks pass against the
restored stack.

## Security Notes

- Backups may contain workflow data, audit data, object data, and knowledge
  documents.
- Store backups outside the repository.
- Do not commit backup files.
- Do not include real customer data in the demo stack.
- Production secret vault integration is not implemented yet.
- Retention, encryption-at-rest policy, and automated restore tests are later
  production hardening work.
