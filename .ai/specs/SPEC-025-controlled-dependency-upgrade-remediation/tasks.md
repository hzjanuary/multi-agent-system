# SPEC-025 Tasks - Controlled Dependency Upgrade Remediation

## Task List

### TASK 025.1 - Audit Refresh And Dependency Graph Review

Status: Implemented.

Goal: Refresh npm audit evidence and identify exact dependency paths before
changing manifests.

Scope:

- Run `npm audit` and `npm audit --json` without mutation.
- Capture affected packages, direct/transitive paths, fix availability, and
  force/major recommendations.
- Review `npm outdated` for compatible wanted/latest versions.
- Compare findings against SPEC-024 closeout.
- Keep raw audit JSON outside the repository unless a future task explicitly
  asks for a sanitized artifact.

Acceptance criteria:

- Findings are grouped into runtime framework and development-tooling chains.
- Any proposed package target has an exact version and rationale.
- No dependency files are changed.
- No `npm audit fix` or `npm audit fix --force` is run.

Validation:

```bash
git diff --check
git status --short
cd frontend && npm audit || true
cd frontend && npm outdated || true
```

Implementation:

- Refreshed audit baseline on `2026-07-28T22:42:40+07:00`.
- Wrote raw audit JSON to `/tmp/spec025-npm-audit.json`; it was not committed.
- Current audit remains 12 high vulnerabilities, 0 critical/moderate/low.
- No additional finding group was discovered.
- Added `docs/security/SPEC_025_REMEDIATION_MATRIX.md`.
- Matrix separates:
  - Next nested PostCSS runtime path;
  - Next nested optional Sharp runtime path;
  - ESLint/minimatch development-tooling path.
- Matrix documents current installed versions, npm force/breaking remediation
  output, decision categories, stop gates, Sprint 2 candidates, validation
  commands, rollback commands, success criteria, and defer criteria.
- No dependency manifests, lockfiles, backend/frontend code, Docker/CI,
  provider, real email, or final quote behavior changed.

Validation results:

- `git status --short` was run before the audit refresh.
- `npm audit --json` wrote raw output to `/tmp/spec025-npm-audit.json`.
- `npm audit || true` reported 12 high vulnerabilities.
- `npm outdated || true` completed and showed no newer wanted Next 15 or
  ESLint 9 targets.
- `git diff --check` passed.
- `docker compose config` passed.
- `docker compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example config`
  passed.

### TASK 025.2 - Runtime Framework Remediation Plan

Status: Planned.

Goal: Decide whether the Next/PostCSS/Sharp audit chain can be remediated with
a safe compatible upgrade or requires a major framework sprint.

Scope:

- Investigate compatible Next 15 patch options.
- Investigate whether Next 16 or another major path is required.
- Review nested PostCSS and optional Sharp paths.
- Decide whether overrides are acceptable or should be rejected.
- Do not edit manifests in the planning step.

Acceptance criteria:

- Recommended runtime remediation target is documented.
- Compatibility risks for app routes, build, image handling, and production
  demo images are documented.
- Stop gate is explicit if force/major movement is required.

Validation:

```bash
git diff --check
git status --short
```

### TASK 025.3 - Development Tooling Remediation Plan

Status: Planned.

Goal: Decide how to remediate the ESLint/minimatch tooling chain separately
from runtime framework findings.

Scope:

- Review ESLint/plugin/minimatch dependency paths.
- Identify exact package targets if safe compatible updates exist.
- Determine whether ESLint 10 or major plugin changes are required.
- Keep tooling changes separate from runtime changes unless a future task
  explicitly combines them.

Acceptance criteria:

- Tooling remediation target or deferral reason is documented.
- Dev-only risk classification is documented.
- Any major tooling migration is scoped as a separate compatibility task.

Validation:

```bash
git diff --check
git status --short
```

### TASK 025.4 - Controlled Runtime Upgrade Implementation

Status: Future implementation task.

Goal: Apply the approved runtime framework package change, if TASK 025.2
identifies a safe target.

Scope:

- Edit only approved frontend manifest/lockfile entries.
- Do not run broad `npm update`.
- Do not run `npm audit fix --force`.
- Preserve routes, auth, workflow semantics, and no-key demo behavior.

Acceptance criteria:

- `npm audit` result improves or remaining runtime findings are documented.
- Frontend lint/build/typecheck/tests pass.
- Production-demo image build passes.
- Manual smoke covers core frontend routes.

Validation:

```bash
git status --short
git diff --check
cd frontend && npm audit || true
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
```

### TASK 025.5 - Controlled Tooling Upgrade Implementation

Status: Future implementation task.

Goal: Apply the approved ESLint/minimatch development-tooling package change,
if TASK 025.3 identifies a safe target.

Scope:

- Edit only approved frontend dev dependency manifest/lockfile entries.
- Keep runtime dependency changes out of this task unless explicitly approved.
- Do not run `npm audit fix --force`.
- Preserve lint configuration intent.

Acceptance criteria:

- Lint still runs with `--max-warnings=0`.
- Tests and build remain stable.
- Any remaining dev-tooling findings are documented honestly.

Validation:

```bash
git status --short
git diff --check
cd frontend && npm audit || true
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
bash scripts/ci/frontend-gate.sh
```

### TASK 025.6 - Backend Dependency Review

Status: Optional / planned if Poetry is available.

Goal: Complete the backend dependency outdated review that SPEC-024 could not
perform on the host.

Scope:

- Run Poetry outdated review in a prepared environment.
- Do not edit backend dependencies unless a future implementation task approves
  exact targets.
- Classify FastAPI, Starlette/Uvicorn, Pydantic, SQLAlchemy, asyncpg, JWT,
  password hashing, Redis, Qdrant, MinIO, and LangGraph upgrade risks.

Acceptance criteria:

- Backend outdated state is documented or the environment blocker is recorded.
- No backend manifest/lockfile change is made in the review task.

Validation:

```bash
git diff --check
git status --short
cd backend && poetry show --outdated || true
```

### TASK 025.7 - Validation, Documentation, And Closeout

Status: Planned.

Goal: Close SPEC-025 by recording actual remediation results, remaining
findings, validation proof, and any future upgrade requirements.

Scope:

- Update SPEC-025 status.
- Update security triage report with before/after audit.
- Update release limitations if findings remain.
- Update README only if public status changes.
- Update handoff with validation and next work.
- Do not overclaim vulnerability remediation.

Acceptance criteria:

- Fixed, unchanged, and deferred findings are clearly separated.
- All validation commands required by implemented upgrade tasks are recorded.
- No stable demo behavior changes are introduced.
- Remaining risk and future work are explicit.

Validation:

```bash
git diff --check
git status --short
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
bash scripts/ci/frontend-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/all-gates.sh
```

## Planning Deliverables

- `.ai/specs/SPEC-025-controlled-dependency-upgrade-remediation/spec.md`
- `.ai/specs/SPEC-025-controlled-dependency-upgrade-remediation/tasks.md`
- `docs/security/SPEC_025_REMEDIATION_MATRIX.md`
- `.ai/specs/SPEC_INDEX.md` update
- `.codex/HANDOFF.md` update

Planning task boundaries:

- No dependency changes.
- No product behavior changes.
- No backend/frontend/Telegram/API/database/Docker/CI/provider behavior
  changes.
- No real email.
- No final quote behavior.
