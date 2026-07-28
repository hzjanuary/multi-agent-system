# SPEC-024 - Dependency and Security Maintenance

## Status

Implemented / ready for closeout review

## Product Objective

Create a safe dependency and security maintenance package after
`v1.0.0-demo-release` without changing product behavior.

SPEC-024 Sprint 1 documents the current dependency/security baseline, triages
known frontend npm audit findings, defines maintenance policy, and prepares a
future bounded remediation path. Sprint 2 performs a bounded frontend
patch-level remediation attempt for selected direct packages while preserving
product behavior.

## Current Release Baseline

- Release tag context: `v1.0.0-demo-release`.
- Current branch during Sprint 1 audit: `main`.
- Current commit during Sprint 1 audit:
  `838b9146a845e185d9186553fc6013d70feb65ab`.
- SPEC-001 through SPEC-023 are completed and approved.
- Stable demo remains deterministic and no-key:
  - `LLM_PROVIDER=fake`
  - `LLM_RUNTIME_ENABLED=false`
  - `EMBEDDING_PROVIDER=fake`
  - `RAG_ENABLED=false`
  - `PRICE_RESEARCH_ENABLED=false`
  - `OUTBOUND_SEND_ENABLED=false`

## Security Maintenance Goals

- Keep dependency risk visible after release.
- Separate audit triage from dependency upgrades.
- Avoid automatic upgrades that could break the graduation/demo flow.
- Preserve deterministic demo behavior while planning remediation.
- Document when vulnerabilities block a release and when they require a future
  upgrade sprint.
- Keep all provider keys, Telegram tokens, and local secrets out of committed
  files.

## Sprint 1 Audit Baseline

Audit date/time:

```text
2026-07-28T09:10:11+07:00
```

Commands run for baseline triage:

```bash
git status --short
git diff --check
cd frontend && npm audit --json
cd frontend && npm audit
cd frontend && npm outdated || true
cd backend && poetry show --outdated || true
```

Observed frontend npm audit summary:

- total vulnerabilities: 12
- high: 12
- moderate/low/critical: 0
- affected names reported by npm:
  - `@eslint/config-array`
  - `@eslint/eslintrc`
  - `brace-expansion`
  - `eslint`
  - `eslint-config-next`
  - `eslint-plugin-import`
  - `eslint-plugin-jsx-a11y`
  - `eslint-plugin-react`
  - `minimatch`
  - `next`
  - `postcss`
  - `sharp`

Observed backend dependency review:

- Host `poetry` command was unavailable during Sprint 1 audit.
- Backend dependency upgrade review should be rerun in a future environment with
  Poetry available, or inside a dedicated backend maintenance container if a
  future task adds such a command.

## Sprint 2 Frontend Remediation Summary

Sprint 2 applied targeted frontend package updates only:

| Package | Before | After | Change type | Reason |
| --- | --- | --- | --- | --- |
| `next` | `15.5.20` | `15.5.22` | patch | Attempt to remediate Next/PostCSS/Sharp audit chain without a major upgrade. |
| `eslint-config-next` | `15.5.21` in lockfile | `15.5.22` | patch | Align Next ESLint config with patched Next version. |
| `postcss` | `8.5.22` in lockfile | `8.5.23` | patch | Apply direct PostCSS patch available within current major. |

No React, backend, Docker/Compose/CI, API, database, Telegram, provider, real
email, or final quote behavior was changed.

Final Sprint 2 audit result:

- total vulnerabilities: 12
- high: 12
- moderate/low/critical: 0

The high count did not decrease because remaining npm remediation suggestions
require `npm audit fix --force` / breaking paths for:

- Next nested `postcss@8.4.31`;
- Next nested optional `sharp@0.34.5`;
- ESLint/minimatch development-tooling chain requiring major/force behavior.

These are deferred to a future major/framework dependency spec or a reviewed
maintenance sprint. Sprint 2 did not run `npm audit fix` or
`npm audit fix --force`.

## Dependency Triage Process

1. Run audits without mutation.
2. Save raw noisy output outside the repository, for example under `/tmp`.
3. Summarize affected packages, severity, direct/transitive status, and whether
   an automated fix would be breaking.
4. Classify each finding:
   - blocking;
   - non-blocking;
   - false positive / dev-only;
   - requires upgrade spec.
5. Check whether the vulnerable code path is reachable in the current demo or
   production-demo flow.
6. Decide whether remediation needs:
   - patch/minor dependency sprint;
   - major framework upgrade spec;
   - configuration mitigation;
   - accepted non-blocking release note.
7. Validate after any future dependency change with backend/frontend/all gates.

## Frontend npm Audit Policy

- Run `npm audit` and `npm audit --json` before release tagging and after
  dependency changes.
- Do not run `npm audit fix` automatically.
- Do not run `npm audit fix --force` without a reviewed implementation sprint.
- Treat direct runtime dependencies as higher priority than dev-only lint/test
  dependency chains.
- Treat `next`, `react`, `react-dom`, image-processing packages, build/runtime
  server packages, and request-handling packages as potentially release
  relevant.
- Treat ESLint/plugin/minimatch findings as development-tooling risk unless a
  project-specific execution path makes them runtime reachable.
- If npm suggests a version outside the currently pinned range or a major
  upgrade, create a separate spec or implementation task before changing
  manifests.

## Backend Dependency Review Policy

- Use Poetry metadata as the source of truth for backend dependency review.
- Run:

```bash
cd backend
poetry show --outdated || true
```

- If Poetry is unavailable on the host, rerun in a prepared development
  environment before starting a backend dependency patch sprint.
- Do not change `pyproject.toml` or `poetry.lock` during audit-only work.
- Treat FastAPI, Starlette/Uvicorn, Pydantic, SQLAlchemy, asyncpg, JWT,
  password hashing, object storage, Redis, Qdrant, and LangGraph upgrades as
  compatibility-sensitive.

## Risk Classification

### Blocking

A finding blocks release when it is:

- directly exploitable in the shipped demo path;
- reachable without authentication where auth should be required;
- a secret exposure or credential leak;
- a remote code execution, authentication bypass, or data exfiltration issue in
  an active runtime path;
- a vulnerability with a safe reviewed patch available and low regression risk.

### Non-Blocking

A finding may be non-blocking when:

- configured quality gates pass;
- the issue is not exercised in the stable deterministic demo;
- remediation requires a larger framework upgrade;
- the release is an academic/demo package with documented limitations;
- mitigation is documented and no real secrets/customer data are used.

### False Positive / Dev-Only

A finding may be classified as false positive or dev-only when:

- it only affects lint/test/build tooling;
- it is not shipped in runtime images;
- exploitation would require trusted developer input;
- the project does not expose the vulnerable behavior in any deployed route.

### Requires Upgrade Spec

A finding requires a future upgrade spec when:

- npm recommends `--force`;
- npm recommends a major Next/React/ESLint/Tailwind/TypeScript change;
- package manager lockfile churn is broad;
- compatibility changes affect routing, rendering, tests, auth, workflow UI, or
  production-demo images.

## Upgrade Policy

- Patch/minor upgrades may be performed only in a future implementation sprint
  with scoped dependency changes and full validation.
- Major upgrades require separate spec approval.
- `npm audit fix` is allowed only after reviewing the planned package changes.
- `npm audit fix --force` is prohibited unless a task explicitly approves the
  resulting major/breaking changes.
- Backend dependency upgrades must update `poetry.lock` intentionally and pass
  backend gates.
- Dependency changes must preserve no-key deterministic demo behavior.

## CI and Gate Requirements

Required validation before closing a dependency remediation sprint:

```bash
git diff --check
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
```

If frontend dependencies change, also run:

```bash
cd frontend
npm audit
npm run lint
npm run build
npm run typecheck
npm test
```

If backend dependencies change, also run:

```bash
cd backend
poetry show --outdated || true
```

## Rollback Plan

If a future dependency sprint regresses behavior:

1. Stop the upgrade branch before merging.
2. Restore the previous manifest and lockfile versions.
3. Reinstall dependencies from the restored lockfile.
4. Rebuild local and production-demo images.
5. Rerun backend/frontend/all gates.
6. Record the failed upgrade path in security triage notes.

Do not revert unrelated user changes.

## User Stories

- As a maintainer, I can see the current dependency/security state without
  reading raw audit JSON.
- As a reviewer, I can distinguish demo-release readiness from dependency
  remediation work.
- As a future implementer, I know when `npm audit fix` is appropriate and when
  it is unsafe.
- As an evaluator, I can confirm dependency triage did not alter demo behavior.
- As a security reviewer, I can see which findings are blocking,
  non-blocking, dev-only, or deferred to an upgrade spec.

## Acceptance Criteria

- SPEC-024 spec and tasks docs exist.
- Security maintenance guidance exists.
- Security triage report exists.
- README links to the security maintenance docs.
- SPEC index and handoff reference SPEC-024 Sprint 1.
- Current npm audit findings are summarized.
- No dependency manifests or lock files are changed.
- No `npm audit fix` is run.
- No backend code, frontend code, Telegram behavior, API, database,
  Docker/Compose/CI behavior, provider call, real email, or final quote behavior
  is changed.

## Non-Goals

- No dependency upgrades in Sprint 1.
- No `npm audit fix`.
- No package manifest or lockfile edits.
- No backend behavior changes.
- No frontend behavior changes.
- No Telegram bridge changes.
- No API changes.
- No database/migration changes.
- No Docker/Compose/CI behavior changes.
- No provider calls.
- No real email.
- No final quote behavior.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Automatic audit fix introduces breaking framework changes | Require separate reviewed dependency patch sprint |
| Runtime Next vulnerability remains present | Track as future remediation priority and keep release warning visible |
| Dev-tooling vulnerabilities are overtreated as runtime blockers | Classify dev-only chains separately |
| Backend outdated state is unknown from host | Rerun Poetry review in a prepared future environment |
| Dependency remediation breaks demo | Require all gates and manual smoke before merging |
| Secrets leak during audit | Store raw audit output outside repo and do not paste tokens/keys into docs |

## Future Tasks

- Future major/framework dependency remediation for unresolved Next nested
  PostCSS/Sharp and ESLint/minimatch audit chains.
- Future backend dependency review sprint with Poetry available.
- Future major framework upgrade spec if Next/ESLint remediation requires
  incompatible changes.
- Future CI enhancement for audit reporting after a reviewed policy decision.
