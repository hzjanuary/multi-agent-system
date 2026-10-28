# Product verification scripts

- `ci/backend-gate.sh`: locked Python quality and behavior gates.
- `ci/compose-gate.sh`: canonical self-host Compose configuration check.
- `ops/scan_secrets.py`: fail-closed full index/worktree secret scanning, with exact reviewed fixture hashes.
- `ops/validate_environment.py`: sanitized real-provider self-host config checks.
- `ops/live_text_review.py`: explicit bounded public-API two-agent live smoke.

Test databases must be isolated from operator state. No seed/demo/ingest step is
part of installation or validation. Historical Harness compatibility tooling was
removed from active distribution after import/CI inventory confirmed no retained
runtime dependency; baseline Git history preserves it.

Release hardening: `ci/release-gate.sh` checks the index, source archive, build
context and actual image/license integrity against the committed revision.
`ops/release_security.py` installs hash-pinned Trivy, scans OS/language packages
and emits a CycloneDX SBOM. HIGH/CRITICAL are blocking without blanket exceptions.
See [release checklist](../docs/release/RELEASE-CHECKLIST.md). Ops tests run with
`python3 -m unittest discover -s scripts/ops -p 'test_*.py'`. No inference keys
are needed. Remote CI status must be recorded independently.


`ops/verify_release_install.py` rehearses an empty installation without inference
in a new private clone/project. It isolates subprocess configuration from parent
CI settings and validates resolved API/worker/CLI profiles before starting any
service. `--public-diagnostic` selects the allowlisted summary (default
`.maos/clean-install-summary.json`). Never upload its private process records,
configuration, generated administrator password or CLI session. Existing project
resources are refused; only rehearsal services stop, with volumes retained.
