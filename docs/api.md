# API and CLI

The breaking pre-1.0 interface uses `/api/v1`. `/docs` and `/openapi.json` expose
the generated contract. `/live` is process liveness; `/ready` checks schema,
storage and configured definitions/provider without inference. Redis degradation
is reported separately from required PostgreSQL readiness.

Authenticate with `POST /auth/login` (email/password); send the returned access
token in `Authorization: Bearer <token>`. Refresh rotates a stored hashed session;
logout revokes the supplied refresh token. Existing access JWTs remain valid
until their short expiry. There is no registration or remote user-admin API.

| Resource relative to `/api/v1` | Operation |
| --- | --- |
| `GET /agents`, `/workflows`, `/workflows/{id}?version=...` | Discover installed metadata/schemas |
| `POST /runs` | Create from workflow_id, exact version and input |
| `GET /runs?limit=100&offset=0` | Summary list; status/workflow filters |
| `GET /runs/{id}` | Summary/final output |
| `GET /runs/{id}/nodes` | Bounded attempt records/validated node outputs |
| `POST /runs/{id}/start` | Queue durably, 202 |
| `POST /runs/{id}/cancel` | Persist cancellation or cancellation request, 202 |
| `GET /runs/{id}/approvals` | Pending content and decision history |
| `POST /runs/{id}/approvals/{approval-id}/decision` | Approve/reject with expected_revision, content_revision, content_hash |
| `POST /runs/{id}/resume` | Explicitly queue approved/safely interrupted work, 202 |
| `GET /runs/{id}/events?after_sequence=0&limit=100` | Ordered durable events |
| `WS /runs/{id}/stream?after_sequence=0` | Header-authenticated committed-event catch-up |

List limit defaults to 100, maximum 500. Clients persist the last received
sequence and deduplicate event IDs. Node/event history is never embedded as an
unbounded array in run summaries. Streams re-check authentication and eventually
poll the database even when Redis notifications are absent. Query-token
WebSocket authentication is not accepted.

Admin/operator can create and control runs and decide approvals. Viewer can read
all instance run details, definitions and events. Readers are instance-wide,
not per-owner isolated. Unknown resources are 404, validation 422, authentication
401, denied roles 403, conflicts 409, and unusable configuration/dependencies 503.
Asynchronous execution failure persists a FAILED state and safe error category.

`Idempotency-Key` is accepted for create/start/resume. Keys are scoped by principal
and operation family, and retained for the run lifetime. Replay of the same
canonical request returns the existing run; changing body or run target in that
family conflicts. No key is needed to prevent simultaneous active claims.

`python -m app.cli --help` discovers CLI groups. Ordinary workflow/run commands
use HTTP. Local config, migration, account administration and doctor use the
same application services. `--json` appears before the command group; failures
exit nonzero with diagnostics on stderr. Passwords are prompted or read with
`--password-stdin`; tokens are stored only in an explicit private auth file.
`run events --follow` uses cursor-based REST polling. See README for the persistent
Compose CLI profile.
