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

Status: Deferred / future only.

Goal: Apply reviewed dependency patches after triage approval.

Scope:

- Review npm audit suggested fixes.
- Prefer patch/minor updates when compatible.
- Avoid `npm audit fix --force` unless explicitly approved.
- Update manifests/locks only in that future sprint.
- Run full backend/frontend/all gates.

Non-goal for Sprint 1:

- No dependency upgrades.

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

## Sprint 1 Deliverables

- `.ai/specs/SPEC-024-dependency-security-maintenance/spec.md`
- `.ai/specs/SPEC-024-dependency-security-maintenance/tasks.md`
- `docs/security/DEPENDENCY_SECURITY_MAINTENANCE.md`
- `docs/security/SECURITY_TRIAGE_REPORT.md`
- `README.md` update
- `.ai/specs/SPEC_INDEX.md` update
- `.codex/HANDOFF.md` update
- `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md` update

No backend code, frontend code, Telegram behavior, API contract, database
model/migration, Docker/Compose/CI behavior, provider call, real email, final
quote behavior, package manifest, or lockfile was changed by Sprint 1.

