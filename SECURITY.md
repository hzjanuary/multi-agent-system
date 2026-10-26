# Security

This pre-1.0 runtime supports one trusted self-hosted instance. It does not
sandbox Python extensions or offer SaaS tenant isolation. Operators are
responsible for their host, TLS exposure, provider configuration and backups.
Only the current headless release is maintained; legacy graduation deployments
must remain isolated.

For a non-sensitive report, open an issue in the existing project repository:
https://github.com/hzjanuary/multi-agent-system/issues
Do not include secrets, raw user input, tokens, provider bodies or private
backups. A dedicated private disclosure channel is not currently advertised;
request a private contact arrangement without publishing vulnerability details.
No response-time SLA or security certification is claimed.

Access tokens remain valid until expiry after logout; refresh sessions are
rotated/revoked in PostgreSQL. Instance readers can access all runs. Remote model
providers receive the supplied input; no all-local guarantee applies to them.
