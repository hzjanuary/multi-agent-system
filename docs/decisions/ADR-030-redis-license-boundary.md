# Redis license boundary and possible future Valkey evaluation

Status: current Redis retained; future alternative not selected.

SPEC-030 does not replace infrastructure. Redis 7.4 is distributed under a choice
of RSALv2 or SSPLv1, neither OSI-approved. Project-owned code remains MIT; those
terms do not cover the whole deployment. Operators/distributors must review the
actual independent infrastructure terms. See `release/third-party/stack.json`.

A future Valkey migration could pursue an OSI-only infrastructure stack. It needs
a separate decision covering notification compatibility, versions/support,
security scans, persistence/recovery, image provenance and licensing. This note
does not authorize a migration or claim that Valkey was tested here.
