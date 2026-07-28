# SPEC-025 - Controlled Dependency Upgrade Remediation

## Status

Sprint 1 implemented / ready for review

## Product Objective

Plan a controlled dependency upgrade remediation sprint that addresses the
deferred npm audit findings from SPEC-024 without changing product behavior
until an implementation task is explicitly approved.

SPEC-025 exists because SPEC-024 closed honestly with remaining frontend npm
audit findings still present. The next remediation step needs a separate,
bounded upgrade plan with explicit targets, rollback, proof, and stop gates
before any manifest or lockfile changes are made.

This is planning only. This specification does not upgrade dependencies, run
`npm audit fix`, change source code, change Docker/CI behavior, or alter the
stable deterministic demo.

## Current Baseline

Source of truth:

- SPEC-024 status: approved and closed with deferred npm audit findings.
- Sprint 2 bounded remediation already updated:
  - `next` from `15.5.20` to `15.5.22`;
  - `eslint-config-next` to `15.5.22`;
  - direct `postcss` to `8.5.23`.
- Final after-remediation npm audit still reports:
  - total vulnerabilities: 12;
  - high: 12;
  - moderate/low/critical: 0.
- Remaining chains:
  - Next nested `postcss@8.4.31`;
  - Next nested optional `sharp@0.34.5`;
  - ESLint/minimatch development-tooling chain.
- npm currently recommends force/breaking remediation paths for unresolved
  findings, so further changes must be handled as a separate compatibility
  sprint.
- SPEC-025 Sprint 1 refreshed the audit baseline and created the controlled
  remediation matrix:
  - `docs/security/SPEC_025_REMEDIATION_MATRIX.md`

Reference docs:

- `.ai/specs/SPEC-024-dependency-security-maintenance/spec.md`
- `.ai/specs/SPEC-024-dependency-security-maintenance/tasks.md`
- `docs/security/SECURITY_TRIAGE_REPORT.md`
- `docs/security/DEPENDENCY_SECURITY_MAINTENANCE.md`
- `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md`

## Scope

SPEC-025 plans future remediation for:

- refreshed frontend audit and dependency graph review;
- Next/PostCSS/Sharp runtime framework remediation options;
- ESLint/minimatch development-tooling remediation options;
- optional backend dependency review if Poetry is available;
- compatibility risks from framework/tooling major versions;
- full validation gates required after any future implementation task;
- rollback and stop conditions;
- documentation updates needed after remediation.

## Non-Goals

- No dependency upgrades in this planning task.
- No `npm audit fix`.
- No `npm audit fix --force`.
- No broad `npm update`.
- No edits to `frontend/package.json`, `frontend/package-lock.json`,
  `backend/pyproject.toml`, or `backend/poetry.lock` in the planning task.
- No backend behavior changes.
- No frontend feature or UI behavior changes.
- No Telegram bridge behavior changes.
- No API contract changes.
- No database models or migrations.
- No Docker/Compose/CI behavior changes.
- No provider calls.
- No live web calls.
- No real email.
- No final quote behavior.
- No committed secrets, provider keys, Telegram tokens, cookies, or local env
  files.

## Remediation Principles

1. Treat audit output as input, not as an automatic command to execute.
2. Prefer reviewed exact package changes over broad package-manager fixes.
3. Separate runtime framework risk from development-tooling risk.
4. Preserve the stable no-key deterministic demo by default.
5. Run validation after each coherent upgrade group.
6. Stop before force/breaking upgrades if compatibility risk is not understood.
7. Keep rollback simple: restore manifest/lockfile, reinstall, rebuild, rerun
   gates.
8. Never hide remaining findings; document what is fixed, unchanged, or newly
   introduced.

## Target Remediation Areas

### Runtime Framework Chain

Known chain:

- `next`
- nested `postcss`
- nested optional `sharp`

Investigation questions:

- Does a newer compatible Next 15 patch resolve the nested PostCSS/Sharp audit
  paths without requiring Next 16?
- Does Next 16 resolve the findings, and what app-router/build/test changes are
  required?
- Is the optional nested Sharp path present in production-demo images, and is
  it reachable through configured image optimization routes?
- Are package overrides safe, supported, and maintainable for this repository,
  or should they be avoided in favor of framework upgrades?

Planned decision points:

- Apply another exact Next 15 patch if npm and validation show it is sufficient
  and low risk.
- Open a major framework upgrade implementation if Next 16 is required.
- Defer overrides unless a future task documents why the override is safer than
  a framework upgrade.

### Development Tooling Chain

Known chain:

- `brace-expansion`
- `minimatch`
- `@eslint/config-array`
- `@eslint/eslintrc`
- `eslint`
- `eslint-config-next`
- `eslint-plugin-import`
- `eslint-plugin-jsx-a11y`
- `eslint-plugin-react`

Investigation questions:

- Which findings are dev-only and absent from runtime production-demo images?
- Does a safe ESLint 9-compatible plugin update resolve the chain?
- Does npm require ESLint 10 or other major tooling movement?
- Do lint rules or test configuration need migration for any major tooling
  change?

Planned decision points:

- Patch ESLint/plugin dependencies only when exact target versions are known.
- Treat ESLint 10 as a separate compatibility upgrade if required.
- Keep dev-tooling remediation separate from runtime Next remediation when that
  reduces blast radius.

### Backend Dependency Review

SPEC-024 could not complete host Poetry outdated review because Poetry was not
available on the host.

SPEC-025 should plan a backend review only if a reliable command is available:

```bash
cd backend
poetry show --outdated || true
```

Backend dependency upgrades remain out of scope unless a future task explicitly
approves `pyproject.toml` and `poetry.lock` changes with backend gate coverage.

## Stable Defaults To Preserve

Any future remediation implementation must preserve:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
PRICE_RESEARCH_ENABLED=false
OUTBOUND_SEND_ENABLED=false
TELEGRAM_LLM_EXTRACTION_ENABLED=false
TELEGRAM_SALES_REPLY_ENABLED=false
```

Dependency upgrades must not require provider keys, live LLM calls, Tavily/live
web calls, real email, or cloud resources.

## Validation Strategy

Planning validation:

```bash
git diff --check
git status --short
```

Required implementation validation for any future dependency changes:

```bash
git status --short
git diff --check
cd frontend && npm audit
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run typecheck
cd frontend && npm test
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
bash scripts/ci/frontend-gate.sh
bash scripts/ci/backend-gate.sh
bash scripts/ci/all-gates.sh
```

Optional implementation validation:

```bash
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example build backend frontend
bash scripts/final/final-quality-gate.sh
python3 scripts/evaluation/evaluate_telegram_parser.py
python3 scripts/evaluation/evaluate_demo_safety.py
```

Manual smoke after frontend framework changes:

- `/login`
- `/demo`
- `/agent-monitor`
- `/agent-monitor?workflowId=<workflow_id>`
- `/workflows`
- `/workflows/<workflow_id>`
- `/dashboard`
- approval/resume path remains visible;
- Agent Monitor still renders real workflow state;
- reference evidence panel still avoids fabricated evidence and final quote
  claims.

## Stop Gates

Stop and request review before implementation if:

- npm suggests `--force`;
- npm suggests a major Next, React, ESLint, Tailwind, TypeScript, or testing
  upgrade;
- lockfile churn includes unrelated packages outside the named target group;
- build output changes route semantics or runtime mode;
- tests fail in a way that requires source behavior changes;
- Docker production-demo image build changes runtime assumptions;
- validation would be weakened or skipped;
- the remediation would require new secrets, provider keys, live web calls, or
  external services.

## Rollback Plan

For any future implementation sprint:

1. Record the pre-change manifest/lockfile versions.
2. Apply one coherent upgrade group.
3. Validate immediately.
4. If validation fails, restore the previous `frontend/package.json` and
   `frontend/package-lock.json` or backend lock files as applicable.
5. Reinstall from the restored lockfile.
6. Rerun affected gates.
7. Document the failed target and reason in `docs/security/SECURITY_TRIAGE_REPORT.md`.

Do not revert unrelated user changes.

## Documentation Updates Required After Future Remediation

After any future dependency remediation implementation:

- update SPEC-025 task status and validation evidence;
- update `docs/security/SECURITY_TRIAGE_REPORT.md` with before/after audit;
- update `docs/security/DEPENDENCY_SECURITY_MAINTENANCE.md` if policy changes;
- update `docs/release/KNOWN_LIMITATIONS_AND_ROADMAP.md` if limitations change;
- update `README.md` only if public status changes;
- update `.codex/HANDOFF.md` with remaining findings and next work.

## Acceptance Criteria

- SPEC-025 spec and tasks planning docs exist.
- SPEC index assigns SPEC-025 to Controlled Dependency Upgrade Remediation and
  retires the old placeholder number conflict.
- Handoff references SPEC-025 Sprint 1 as implemented / ready for review.
- Current SPEC-024 deferred npm audit findings are summarized.
- Runtime framework and development-tooling remediation paths are separated.
- Stable deterministic demo defaults are documented.
- Optional feature/provider behavior remains disabled and unaffected.
- Stop gates, rollback, and validation commands are defined.
- Planning docs do not claim vulnerabilities are fixed.
- Planning docs do not require real provider keys, live web calls, real email,
  or cloud resources.
- No dependency manifests, lockfiles, backend code, frontend code, Telegram
  behavior, API contract, database model/migration, Docker/Compose/CI behavior,
  provider call, real email, or final quote behavior is changed.

## Future Roadmap After SPEC-025

Recommended follow-up implementation sequence:

1. Refresh audit and dependency graph evidence.
2. Attempt exact compatible runtime framework remediation if available.
3. Attempt exact compatible dev-tooling remediation if available.
4. Open a major framework/tooling upgrade spec if force/breaking movement is
   required.
5. Revalidate the full demo, production-demo build, and release docs.
6. Close or defer remaining findings honestly.
