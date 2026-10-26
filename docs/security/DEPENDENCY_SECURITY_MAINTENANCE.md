# Dependency security maintenance

The supported application is the Python headless runtime. There is no active
frontend, Node.js manifest, Qdrant, MinIO or demo-provider dependency set. Old
SPEC-025 frontend triage reports and catalog/outbound policies remain available
at Git baseline `92e5f1cfb2b0144bdb39a48db99371974bd372a5`; they are not current
product rules. Security, data protection, approval boundaries and third-party
notices remain required by SPEC-029.

Keep audits separate from upgrades: record the affected locked version,
advisory, reachable code path, fixed version and validation before changing
packages. Do not run automatic force-upgrade/fix commands during a read-only
audit. Upgrade related packages through Poetry so the manifest and lock stay
consistent, then run the backend gates and actual image build.

The current release audit uses the exported locked main dependency graph and
`pip-audit`, with no inference or operator database access. From `backend/`:

```bash
poetry export --only main --without-hashes --format requirements.txt \
  --output /tmp/maos-main-requirements.txt
uv tool run pip-audit --requirement /tmp/maos-main-requirements.txt \
  --no-deps --disable-pip --format json \
  --output /tmp/maos-dependency-audit.json
```

These are optional network-dependent maintenance commands; they do not audit the
container OS, host, installed custom extensions or model weights. Record the
actual audit time and source revision, and inspect findings rather than treating
an exit code alone as a security guarantee. The release
[verification matrix](../release/verification.md) names the audited graph and
known limitations.

For current source scanning, use the strict tracked-file scanner:

```bash
python3 scripts/ops/scan_secrets.py --strict --allow-test-placeholders
python3 -m unittest scripts.ops.test_scan_secrets -q
```

It prints only redacted findings. Known test fixtures are excluded deliberately;
ignored local configuration is not a committed-source finding. The scanner
recognizes the exact random-secret generator used in CI rather than suppressing
arbitrary shell assignments. Review any finding before changing its rules.
This bounded scanner is not a claim that every possible secret pattern or all
historical Git objects have been exhaustively audited. Never copy real keys,
JWTs, database backups or `.maos/` contents into a report or commit.

Check image contents, installed dependencies and required notices before release.
Retain explicit human approval and resume behavior when upgrading LangGraph or
model transports; run the PostgreSQL concurrency/restart/restore tests when their
underlying packages change. Test-double success is not live-provider proof.
Report sensitive issues following [SECURITY.md](../../SECURITY.md); the existing
repository issue channel is for non-sensitive coordination only.
