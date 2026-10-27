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


Before public release, the repository owner must enable GitHub Private
Vulnerability Reporting: repository **Settings → Security and quality → Advanced
Security → Private vulnerability reporting → Enable**. Verify **Security →
Advisories → Report a vulnerability** is available. Enablement has not been
verified and this task does not change repository settings. See
[GitHub's instructions](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).

Once enabled, use the private form at
https://github.com/hzjanuary/multi-agent-system/security/advisories/new for
vulnerabilities. Until that channel is confirmed, request private contact through
a public issue containing no vulnerability details; wait for a private channel
before sharing proof. Maintainers should acknowledge privately, reproduce on an
isolated instance, agree on coordinated disclosure and publish a reviewed advisory.
No response-time SLA is promised. Never include live secrets or customer data.

TLS/reverse proxy, network access controls, login throttling, body/connection
limits, backup encryption/restore and safe log retention belong to the operator.
This project does not provide SSO or tenant isolation. See the self-hosting guide
and release checklist. A clean local test is not security certification.
