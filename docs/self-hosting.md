# Self-host operations

Use the README's ordered first-run procedure and consult
[release evidence](release/verification.md) for what has actually been exercised.
The supported primary target is Docker Engine/Compose on Linux. Container images
are built locally; publication and remote deployment are separate operator work.

API/worker/migrations/CLI share the same image. Build from the repository root with `docker build --file backend/Dockerfile
--target runtime --build-arg VCS_REF="$(git rev-parse HEAD)"
-t multi-agent-os:local .`. `--network=host` is optional when the host cannot
resolve package indexes through Docker bridge networking.
The build network flag does not publish runtime ports. Build before Compose secret
interpolation. `config init` works without settings imports, creates generated
secrets and UID/GID configuration, preserves existing values, and stores `.env`
0600 and `cli/` 0700. Database migration/admin commands do not require inference.
Use a new database and uniquely named project; the schema guard refuses legacy
and unknown installations without modifying them.

The canonical installation file is `.maos/.env`. `--env-file` supplies Compose
interpolation; Compose explicitly forwards application settings to API/worker.
PostgreSQL/Redis expose no host ports; API binds loopback. Normal stop/restart
preserves named PostgreSQL volumes. Do not use `down -v` on an operator project.
CLI credentials are mounted only into the CLI profile.

`doctor` checks current schema, database and installed registry/configuration
without inference, and reports a worker availability heartbeat using database
time (30-second expiry). Worker container health also checks its local heartbeat. Missing model/key is an honest configuration failure. Redis
loss degrades notifications while database event polling and durable work remain
available. `/live` only means the process responds; `/ready` is the service gate.

For host Ollama on Linux, Compose maps host.docker.internal to the Docker gateway.
The endpoint must listen on an interface containers can reach; firewall access to
trusted networks. An optional `ollama` profile runs Ollama without downloading
weights. Install and select a model explicitly. Docker Desktop connectivity and
other operating systems are not claimed verified unless listed in evidence.

## Backup and restore

Use PostgreSQL tools from the database image and protect backups as sensitive
input/output/auth data. Keep `.maos/.env`, provider credentials and extension
artifacts separately. Do not commit backups or secrets.

The following is the documented operator procedure; restore-rehearsal status is
listed in the release matrix. Run from the repository root. Shell variables refer
to operator-controlled paths, never add them to Git.

```bash
umask 077
docker compose --env-file .maos/.env exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > /tmp/maos-backup.dump
COMPOSE_PROJECT_NAME=maos-restore-review docker compose --env-file .maos/.env up -d --wait postgres
COMPOSE_PROJECT_NAME=maos-restore-review docker compose --env-file .maos/.env exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < /tmp/maos-backup.dump
```

The restore project name must be unused and distinct from the operator project.
Restore into a fresh empty database only; do not add `--clean`. Use the same
application version, definitions and secret configuration for the restored
installation, with its database hostname resolving to the restore project.
Inspect completed outputs, ordered event sequences, pending content/decisions and
login/refresh state before considering it usable. To run a second API alongside
the first, choose another loopback `MAOS_API_PORT`. Do not destroy source volumes.

## Upgrade and recovery

Back up first; record the current image/source revision and enabled extension
fingerprints. Stop API/worker, build the reviewed new image, run its `migrate`,
then start services and run `doctor`. Future headless migrations must preserve
headless data. The graduation database is a separate product and has no in-place
migration. Test restore before upgrade; rollback uses the old image plus a
separate restored compatible database, not an automatic destructive downgrade.

Expired claims become INTERRUPTED; explicitly resume permitted work. A repeated
model call can consume resources even if its first remote outcome was unknown.
Non-idempotent uncertain actions return unsafe_resume_requires_reconciliation;
cancel, reconcile externally and create a new run if appropriate. Committed
checkpoints, approval snapshots and consumed request reservations remain durable.

## Optional public exposure

This is a manual deployment example, not a verified hosted service recipe:
place an operator-managed TLS reverse proxy in front of the loopback API,
forward WebSocket upgrades and Authorization headers, restrict upstream access,
set explicit CORS origins if a client needs them, and use the same auth controls.
Do not expose database or Redis ports. Configure certificate issuance, request
limits and access logs for your environment; avoid recording auth headers/body
content. The project does not provision remote infrastructure.


Keep this single-instance service behind a trusted network or authenticated VPN.
For internet exposure, an operator-managed TLS proxy must enforce request/body
and connection limits, login rate limiting, upstream access restrictions and
WebSocket handling. There is no built-in login throttling, SSO, tenant isolation
or untrusted-extension sandbox. Do not describe this recipe as enterprise
security certification. Test proxy limits and recovery independently.

Keep credentials outside shell history and logs; avoid resolved `compose config`
output (use `--quiet`). Restrict logs/backups to operators, encrypt off-host
backups, set retention, test restore, and redact Authorization/body content in
proxy logs. Readers can see all instance runs, including stored input/output.
Provider data policies are independent; optional smoke consent is not the
production policy. See [release gates](release/RELEASE-CHECKLIST.md).


The release Compose application services (including CLI/migrations) run without
Linux capabilities and with `no-new-privileges`. Keep those options; using root,
privileged containers or added capabilities invalidates the containment review.
For manual application containers, also pass `--cap-drop ALL --security-opt
no-new-privileges:true`. The runtime image excludes filesystem mount utilities
and pip/ensurepip installers; dependencies/extensions belong in reviewed build
stages, not ad-hoc package installation in running services. Python and the
locked application packages remain installed. See the OS triage for unresolved
vulnerabilities; these controls are not a substitute for vendor patches or
enterprise security certification.
