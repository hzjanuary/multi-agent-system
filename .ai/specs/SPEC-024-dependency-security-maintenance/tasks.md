# SPEC-024 Tasks - Dependency and Security Maintenance

## Task List

### TASK 024.1 - Audit Baseline and Triage

Status: Implemented.

Goal: Capture the current dependency/security baseline without changing
dependencies.

Scope:

- Run frontend npm audit commands.
- Run frontend outdated command.
- Attempt backend Poetry outdated review if available.
- Summarize findings in security triage docs.
- Do not run `npm audit fix`.
- Do not edit package manifests or lock files.

Validation:

```bash
git status --short
git diff --check
cd frontend && npm audit --json
cd frontend && npm audit
cd frontend && npm outdated || true
cd backend && poetry show --outdated || true
```

Implementation:

- Frontend npm audit reported 12 high vulnerabilities.
- Affected npm names: `next`, `postcss`, `sharp`, `brace-expansion`,
  `minimatch`, `eslint`, `@eslint/config-array`, `@eslint/eslintrc`,
  `eslint-config-next`, `eslint-plugin-import`, `eslint-plugin-jsx-a11y`, and
  `eslint-plugin-react`.
- Host Poetry command was unavailable, so backend outdated review is deferred
  to an environment with Poetry.
- No dependency files were changed.

### TASK 024.2 - Security Maintenance Docs

Status: Implemented.

Goal: Add reusable dependency/security maintenance guidance.

Scope:

- Document how to run and read npm audit.
- Document when to use or avoid audit fix.
- Document dev/transitive vulnerability triage.
- Document validation and rollback.
- Document no-secret handling.

Deliverable:

- `docs/security/DEPENDENCY_SECURITY_MAINTENANCE.md`

### TASK 024.3 - README and Release Docs Update

Status: Implemented.

Goal: Add concise security maintenance links/status to project entry points.

Scope:

- Update `README.md` with SPEC-024 security status.
- Update `.ai/specs/SPEC_INDEX.md`.
- Update `.codex/HANDOFF.md`.
- Update `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md` if needed.

Implementation:

- Added SPEC-024 status and links to README.
- Added SPEC-024 to the spec index.
- Added handoff section with audit summary and next steps.
- Added dependency/security maintenance limitation and roadmap note.

### TASK 024.4 - Optional Safe Dependency Patch Sprint

Status: Implemented for bounded Sprint 2 patch attempt; remaining force/major
findings deferred.

Goal: Apply reviewed dependency patches after triage approval.

Scope:

- Review npm audit suggested fixes.
- Prefer patch/minor updates when compatible.
- Avoid `npm audit fix --force` unless explicitly approved.
- Update manifests/locks only in that future sprint.
- Run full backend/frontend/all gates.

Sprint 2 implementation:

- Updated `next` from `15.5.20` to `15.5.22`.
- Updated `eslint-config-next` lockfile/package target to `15.5.22`.
- Updated direct `postcss` from lockfile `8.5.22` to `8.5.23`.
- Did not upgrade React.
- Did not run `npm audit fix` or `npm audit fix --force`.
- Did not apply broad `npm update`.

Sprint 2 outcome:

- Before audit: 12 high vulnerabilities.
- After audit: 12 high vulnerabilities.
- Safe direct patch updates were accepted and validated.
- Remaining findings require force/breaking remediation paths or nested Next
  dependency changes and are deferred.

### TASK 024.5 - Final Validation and Closeout

Status: Implemented / ready for closeout review.

Goal: Validate Sprint 1 docs and confirm no behavior/dependency changes were
introduced.

Required validation:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
cd frontend && npm audit
cd frontend && npm outdated || true
```

Optional validation:

```bash
bash scripts/ci/all-gates.sh
```

Closeout checklist:

- SPEC-024 docs exist.
- Security maintenance docs exist.
- Security triage report exists.
- README/security/release/handoff links are present.
- No dependency files changed.
- No `npm audit fix` was run.
- No product behavior changed.
- Current release remains stable/demo-ready, with dependency remediation tracked
  as separate future work.

Sprint 2 validation results:

- `npm ci` passed.
- `npm run lint` passed.
- `npm run build` passed on Next `15.5.22`.
- `npm run typecheck` passed.
- `npm test` passed: 13 test files, 93 tests.
- `docker compose config` passed.
- `docker compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config`
  passed.
- `bash scripts/ci/frontend-gate.sh` passed.
- `bash scripts/ci/all-gates.sh` passed, including backend gate, frontend
  gate, production-demo image build, and whitespace check.
- Final `npm audit` still reports 12 high vulnerabilities; remaining
  remediation is deferred because npm requires force/breaking paths.

## Sprint 1 Deliverables

- `.ai/specs/SPEC-024-dependency-security-maintenance/spec.md`
- `.ai/specs/SPEC-024-dependency-security-maintenance/tasks.md`
- `docs/security/DEPENDENCY_SECURITY_MAINTENANCE.md`
- `docs/security/SECURITY_TRIAGE_REPORT.md`
- `README.md` update
- `.ai/specs/SPEC_INDEX.md` update
- `.codex/HANDOFF.md` update
- `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md` update
- `frontend/package.json` targeted dependency updates
- `frontend/package-lock.json` targeted lockfile updates

No backend code, frontend feature code, Telegram behavior, API contract,
database model/migration, Docker/Compose/CI behavior, provider call, real email,
or final quote behavior was changed by SPEC-024 Sprint 1 or Sprint 2.
