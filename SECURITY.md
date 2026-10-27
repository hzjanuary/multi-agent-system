# Security

Multi-Agent OS is an early source preview for development, experimentation and
trusted self-hosting. It is not certified for unrestricted internet-facing or
enterprise production deployment. The runtime supports one trusted instance;
readers can access all runs and installed Python extensions have worker
privileges. It provides no tenant isolation, SSO, login throttling or extension
sandbox. Operators manage TLS/reverse proxy, access/rate/body limits, backups,
secret protection and safe log retention.

## Private vulnerability disclosure

**GitHub Private Vulnerability Reporting is enabled**, verified read-only on
2026-10-27T17:14:56.290421+00:00. Use
[Report a vulnerability](https://github.com/hzjanuary/multi-agent-system/security/advisories/new)
for private disclosure. Do not include live credentials or customer information;
do not post vulnerability details in public issues. Maintainers should reproduce
privately, agree on coordinated disclosure and publish a reviewed advisory.
No response-time SLA or security certification is claimed.

The earlier disabled observation in SPEC-030 is historical. No repository setting
was changed by the publication agent; the owner enabled reporting independently.
Recheck availability before sending a private report.

## Recorded vulnerabilities and release scope

The recorded Debian Trixie runtime candidate still has unresolved findings:
0 CRITICAL / 40 HIGH / 58 MEDIUM / 60 LOW / 1 UNKNOWN across OS/Python packages.
Six HIGH CVEs have affected components present; source-package attribution is
unresolved for other rows, and specific vulnerable components are absent for
three HIGH rows. No findings have been silently reclassified as fixed.
See [security signoff](docs/release/SPEC-030-SECURITY-SIGNOFF.md) and
[OS triage](docs/release/SPEC-030-OS-TRIAGE.md) for exact source/image, DB timestamp,
mitigations, owner decisions and limitations. Raw scan/CI policy remains failing;
no blanket ignore, VEX suppression or security reviewer approval was added.

The owner authorized an **early source-code publication with disclosed residual
OS risks**. Prebuilt Docker-image publication and production-security approval
are not granted. See [the owner decision](docs/release/v0.1.0-source-preview.md).
Rebuild and rescan your own images, use supported updates where available, and
review current advisories before deployment or exposure. Successful tests or
installation do not mean the runtime is security-hardened.

## Operational boundaries

Canonical Compose application services are non-root, drop all capabilities and
set no-new-privileges. Overriding these settings changes the reviewed exposure.
Do not expose PostgreSQL/Redis or mount a Docker socket. Protect operator
configuration, CLI sessions, input/output databases and backups as sensitive.

Access tokens remain valid until expiry after logout; refresh sessions are
rotated/revoked in PostgreSQL. Remote model providers receive supplied input and
prior outputs required by their steps; self-hosting does not make cloud inference
local or override provider retention/training terms. Restrictive default provider
preferences remain intact; private smoke opt-ins are not production defaults.
Only the current headless code line is maintained; retired demo deployments
should remain isolated. See [self-hosting](docs/self-hosting.md).
