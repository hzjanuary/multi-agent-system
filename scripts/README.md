# Product verification scripts

- `ci/backend-gate.sh`: locked Python quality and behavior gates.
- `ci/compose-gate.sh`: canonical self-host Compose configuration check.
- `ops/scan_secrets.py`: bounded committed/worktree secret scanning.
- `ops/validate_environment.py`: sanitized real-provider self-host config checks.
- `ops/live_text_review.py`: explicit bounded public-API two-agent live smoke.

Test databases must be isolated from operator state. No seed/demo/ingest step is
part of installation or validation. Historical Harness compatibility tooling was
removed from active distribution after import/CI inventory confirmed no retained
runtime dependency; baseline Git history preserves it.
