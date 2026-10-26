# Runtime architecture

Multi-Agent OS is a single-host application runtime. API and worker use the same
trusted installed extension registry and one application image. PostgreSQL is the
sole durable authority for users, refresh sessions, run state, jobs, per-node
checkpoints, approvals, idempotency records and event sequences. Redis provides
notification hints; it is not the job queue or event history.

The HTTP request creates a CREATED run, then start/resume atomically queues one
job. It does not invoke a provider. The worker claims queued work with row locks,
an owner, fencing generation and a lease based on database time. Heartbeats
renew ownership in short transactions; no transaction spans inference. A
reconciler marks expired work INTERRUPTED and invalidates the generation.
An installed-identity mismatch before ownership leaves the original submission
QUEUED with a safe error; the worker rotates that blocked job behind other work.
Restoring the matching installed identity permits the original start to proceed.

LangGraph executes the registered sequential nodes. Before each dispatch, the
worker writes a started attempt. Provider requests reserve persisted call budget
before dispatch, including retries and explicit crash recovery. Successful typed
outputs and their events commit together. Completed nodes are loaded from
application-owned PostgreSQL checkpoints rather than recomputed. There is no
second provider execution loop in API or CLI.

Every result/error write checks current ownership. Cancellation of RUNNING work
is durable intent; the worker terminates at a supported boundary and rejects late
results. Network cancellation cannot promise that upstream inference stops.
Interrupted pure/idempotent tools and agents require explicit resume; uncertain
non-idempotent actions are not resumable. No exactly-once side-effect guarantee
is offered.

Approval records bind a workflow hash/version, node, immutable content revision
and content hash to one decision. The mutable run revision protects concurrent
decisions separately. Only admin/operator may decide. Approval leaves execution
paused until explicit resume; each sequential approval gate has its own record.
There is no public arbitrary state-patch endpoint.

Per-run event sequence allocation occurs under the same run lock as state
changes. Events are durable and paginated independently of summaries. Streams
poll PostgreSQL from the last sequence, closing missed-notification and
backlog/live races. Redis never carries raw input or model output.

Trusted host administrators install Python extensions and configure model
endpoints/credentials. No API accepts executable code, arbitrary modules or
provider URLs. Definition hashes cover schemas, instructions, mappings, limits,
node kinds and reproducible extension/handler source fingerprints. Each run pins
its definition and provider/model identity. Missing or changed identities block
execution/recovery. Credential rotation does not change that identity.

The instance is not multi-tenant: all read roles can inspect instance runs. Inputs
and validated outputs persist in PostgreSQL. Remote models receive selected
input; installed extensions run with the worker's privileges. File attachments,
untrusted-code isolation, distributed execution and autonomous planning are out
of scope.
