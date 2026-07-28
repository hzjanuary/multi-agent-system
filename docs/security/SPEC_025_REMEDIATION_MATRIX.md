# SPEC-025 Remediation Matrix

## Purpose

This document is the SPEC-025 Sprint 1 refreshed npm audit baseline and
controlled remediation matrix.

It is documentation/analysis only. It does not change dependencies, run
`npm audit fix`, upgrade packages, change product behavior, or claim that the
remaining vulnerabilities are fixed.

## Audit Refresh Metadata

Audit refresh timestamp:

```text
2026-07-28T22:42:40+07:00
```

Commands run:

```bash
git status --short
cd frontend && npm audit --json > /tmp/spec025-npm-audit.json || true
cd frontend && npm audit || true
cd frontend && npm outdated || true
```

Raw audit JSON was written to `/tmp/spec025-npm-audit.json` and is not
committed.

## Refreshed Audit Summary

`npm audit` still reports:

| Severity | Count |
| --- | ---: |
| Critical | 0 |
| High | 12 |
| Moderate | 0 |
| Low | 0 |
| Total | 12 |

Dependency totals from `npm audit --json`:

| Dependency type | Count |
| --- | ---: |
| Production | 19 |
| Development | 470 |
| Optional | 92 |
| Total | 523 |

No additional finding group was discovered beyond the SPEC-024 closeout set.

## Current Installed Versions

| Package path | Installed version |
| --- | --- |
| `node_modules/next` | `15.5.22` |
| `node_modules/next/node_modules/postcss` | `8.4.31` |
| `node_modules/next/node_modules/sharp` | `0.34.5` |
| `node_modules/postcss` | `8.5.23` |
| `node_modules/eslint` | `9.39.5` |
| `node_modules/eslint-config-next` | `15.5.22` |
| `node_modules/@eslint/eslintrc` | `3.3.6` |
| `node_modules/@eslint/config-array` | `0.21.2` |
| `node_modules/brace-expansion` | `1.1.16` |
| `node_modules/minimatch` | `3.1.5` |
| `node_modules/eslint-plugin-import` | `2.32.0` |
| `node_modules/eslint-plugin-jsx-a11y` | `6.10.2` |
| `node_modules/eslint-plugin-react` | `7.37.5` |

## Outdated Summary

Current `npm outdated || true` output:

| Package | Current | Wanted | Latest | Initial classification |
| --- | --- | --- | --- | --- |
| `@types/node` | `22.20.1` | `22.20.1` | `26.1.2` | Major types upgrade, not audit remediation target |
| `eslint` | `9.39.5` | `9.39.5` | `10.8.0` | Major tooling compatibility candidate |
| `eslint-config-next` | `15.5.22` | `15.5.22` | `16.2.12` | Major framework/tooling candidate |
| `jsdom` | `25.0.1` | `25.0.1` | `30.0.0` | Major test-environment candidate, not audit target |
| `next` | `15.5.22` | `15.5.22` | `16.2.12` | Major runtime framework candidate |
| `postcss` | `8.5.23` | `8.5.24` | `8.5.24` | Safe patch/minor candidate for direct dependency only |
| `tailwind-merge` | `2.6.1` | `2.6.1` | `3.6.0` | Major UI utility candidate, not audit target |
| `tailwindcss` | `3.4.19` | `3.4.19` | `4.3.3` | Major CSS framework candidate, not audit target |
| `typescript` | `5.9.3` | `5.9.3` | `7.0.2` | Major compiler candidate, not audit target |

The direct `postcss` package has a wanted patch update to `8.5.24`, but the
current audit finding is for `node_modules/next/node_modules/postcss@8.4.31`.
Updating direct `postcss` alone should not be assumed to resolve the nested
Next path.

## Remediation Matrix

### 1. Next/PostCSS Runtime Path

| Field | Value |
| --- | --- |
| Finding group | Next nested PostCSS runtime/build path |
| Affected package path | `node_modules/next/node_modules/postcss` |
| Direct or transitive | Transitive nested dependency |
| Runtime or dev/tooling | Runtime/build framework dependency via Next |
| Current installed version | `postcss@8.4.31` nested under `next@15.5.22` |
| Audit range | `postcss <=8.5.17`; `next 9.3.4-canary.0 - 16.3.0-preview.7` depends on vulnerable `postcss` |
| Available patched version from npm output | npm does not provide a safe direct nested patch; it reports `npm audit fix --force` and `next@9.3.3`, which is a breaking/invalid downgrade path for this app |
| Likely owning direct dependency | `next` |
| Current direct package state | `next@15.5.22`, wanted `15.5.22`, latest `16.2.12` |
| Risk level | High priority runtime/framework risk |
| Decision category | Requires framework compatibility check; current npm force path is blocked |

Remediation options:

| Option | Category | Notes |
| --- | --- | --- |
| Try newer exact Next 15 patch if one becomes available | Safe patch/minor candidate | Only acceptable if npm metadata shows a compatible Next 15 target and full validation passes. Current `npm outdated` shows no newer wanted Next 15 target. |
| Evaluate Next 16 upgrade | Requires major upgrade approval | Could change App Router/build/runtime behavior and must be a separate compatibility sprint. |
| Direct `postcss` patch to `8.5.24` | Safe patch for direct dependency only | May be useful hygiene, but should not be treated as remediation for the nested `next/node_modules/postcss` path. |
| Package override for nested PostCSS | Requires framework/tooling compatibility check | Avoid unless a future task proves it is supported and safer than a framework upgrade. |
| `npm audit fix --force` | Requires force upgrade, blocked | npm suggests a breaking `next@9.3.3` path and must not be used. |

Stop gate:

- Stop before any `npm audit fix --force`, Next major upgrade, package override,
  or broad lockfile churn.

Recommended next action:

- In SPEC-025 Sprint 2, refresh npm metadata again and check whether a newer
  exact Next 15 patch exists. If none exists, prepare a separate Next 16
  compatibility spike before changing manifests.

### 2. Next/Sharp Optional Runtime Path

| Field | Value |
| --- | --- |
| Finding group | Next nested optional Sharp/libvips path |
| Affected package path | `node_modules/next/node_modules/sharp` |
| Direct or transitive | Transitive optional nested dependency |
| Runtime or dev/tooling | Optional runtime image-processing dependency via Next |
| Current installed version | `sharp@0.34.5` nested under `next@15.5.22` |
| Audit range | `sharp <0.35.0`; `next` depends on vulnerable `sharp` |
| Available patched version from npm output | `sharp >=0.35.0` is implied by the vulnerable range, but npm remediation maps through `npm audit fix --force` and `next@9.3.3` |
| Likely owning direct dependency | `next` |
| Current direct package state | `next@15.5.22`, wanted `15.5.22`, latest `16.2.12` |
| Risk level | Medium/high optional runtime risk |
| Decision category | Requires framework compatibility check; direct nested remediation is not safe by default |

Remediation options:

| Option | Category | Notes |
| --- | --- | --- |
| Upgrade Next if a safe compatible patch controls nested Sharp | Safe patch/minor candidate if available | Same gating as the Next/PostCSS group. Current metadata does not show a newer wanted Next 15 target. |
| Evaluate Next 16 upgrade | Requires major upgrade approval | Must include image optimization and production-demo build checks. |
| Add direct `sharp@>=0.35.0` | Requires compatibility check | Prior SPEC-024 exploration did not reduce audit because Next still carries nested `sharp`. Do not treat this as sufficient without audit proof. |
| Package override for nested Sharp | Requires framework/tooling compatibility check | Needs explicit proof because native image packages can affect Docker image build/install behavior. |
| `npm audit fix --force` | Requires force upgrade, blocked | npm suggests a breaking `next@9.3.3` path and must not be used. |

Stop gate:

- Stop before any native `sharp` override, force downgrade, Next major upgrade,
  or Docker image behavior change.

Recommended next action:

- Pair this with the runtime Next investigation. Verify whether production-demo
  images include and exercise the optional Sharp path before prioritizing
  runtime urgency.

### 3. ESLint/Minimatch Development Tooling Path

| Field | Value |
| --- | --- |
| Finding group | ESLint/minimatch development-tooling chain |
| Affected package paths | `node_modules/brace-expansion`, `node_modules/minimatch`, `node_modules/@eslint/config-array`, `node_modules/@eslint/eslintrc`, `node_modules/eslint`, `node_modules/eslint-config-next`, `node_modules/eslint-plugin-import`, `node_modules/eslint-plugin-jsx-a11y`, `node_modules/eslint-plugin-react` |
| Direct or transitive | Mixed: direct `eslint`, `eslint-config-next`, `@eslint/eslintrc`; transitive plugin/minimatch chain |
| Runtime or dev/tooling | Development tooling |
| Current installed versions | `eslint@9.39.5`, `eslint-config-next@15.5.22`, `@eslint/eslintrc@3.3.6`, `@eslint/config-array@0.21.2`, `brace-expansion@1.1.16`, `minimatch@3.1.5`, `eslint-plugin-import@2.32.0`, `eslint-plugin-jsx-a11y@6.10.2`, `eslint-plugin-react@7.37.5` |
| Audit range | `brace-expansion <=5.0.7`; `minimatch 2.0.0 - 10.0.2`; related ESLint/plugin ranges reported by audit |
| Available patched version from npm output | npm JSON reports force/major candidates including `eslint@10.8.0`, `eslint-config-next@16.2.12`, or `@eslint/eslintrc@0.1.0`; current text output reports `@eslint/eslintrc@0.1.0`, which is breaking/unsafe |
| Likely owning direct dependency | `eslint`, `eslint-config-next`, and direct `@eslint/eslintrc` |
| Current direct package state | `eslint@9.39.5` wanted `9.39.5`, latest `10.8.0`; `eslint-config-next@15.5.22` wanted `15.5.22`, latest `16.2.12` |
| Risk level | Medium dev-tooling risk |
| Decision category | Requires tooling compatibility check; current force paths are blocked |

Remediation options:

| Option | Category | Notes |
| --- | --- | --- |
| Identify ESLint 9-compatible plugin/minimatch patches | Safe patch/minor candidate if available | Preferred first step if exact targets exist and lint remains stable. Current `npm outdated` does not show wanted patch updates for `eslint` or `eslint-config-next`. |
| Evaluate ESLint 10 | Requires major upgrade approval | Must be a separate tooling compatibility sprint if needed. |
| Evaluate `eslint-config-next@16.2.12` | Requires framework/tooling compatibility check | Couples tooling to Next 16 major line and should not be mixed into runtime remediation without approval. |
| Force path to `@eslint/eslintrc@0.1.0` | Requires force upgrade, blocked | This is a breaking downgrade-like path relative to installed `3.3.6`; do not use. |
| Defer dev-tooling chain | Deferred because no safe non-breaking path is visible | Acceptable only with documented risk, passing gates, and no runtime image reachability. |

Stop gate:

- Stop before ESLint 10, Next 16 ESLint config, force remediation, or lint rule
  migration unless a tooling compatibility task is approved.

Recommended next action:

- In SPEC-025 Sprint 2, keep tooling remediation separate from runtime Next
  remediation. First inspect whether the vulnerable minimatch chain appears in
  production-demo runtime images; then evaluate exact ESLint/plugin targets.

## Additional Findings

No additional npm audit finding group was discovered by the current audit
refresh.

Packages shown by `npm outdated` but not currently tied to audit findings
include `@types/node`, `jsdom`, `tailwind-merge`, `tailwindcss`, and
`typescript`. They should not be upgraded inside SPEC-025 unless a future task
explicitly expands scope, because they are major compatibility candidates and
not direct remediation evidence for the current high findings.

## Global Stop Gates

Do not proceed with a future implementation if the remediation path requires:

- `npm audit fix --force`;
- React major upgrade without explicit spec approval;
- Next major upgrade without explicit spec approval;
- broad `npm update`;
- package manager migration;
- unreviewed `overrides`;
- frontend build/typecheck/test failures after a trial upgrade;
- product behavior changes;
- route, auth, workflow, approval/resume, Agent Monitor, Telegram, backend API,
  Docker/Compose/CI, provider, real email, or final quote behavior changes.

## Proposed SPEC-025 Sprint 2 Plan

Sprint 2 should remain bounded and reversible.

### Exact Candidates To Try First

1. Refresh npm metadata immediately before implementation:

   ```bash
   cd frontend
   npm audit --json > /tmp/spec025-sprint2-npm-audit-before.json || true
   npm audit || true
   npm outdated || true
   ```

2. If npm shows a newer compatible Next 15 patch beyond `15.5.22`, try only
   that exact Next patch plus matching `eslint-config-next` patch when needed.

3. If no compatible Next 15 patch exists, do not change Next in Sprint 2.
   Instead, open a Next 16 compatibility spike before implementation.

4. If npm shows direct `postcss@8.5.24` as the only safe wanted patch, it may be
   attempted as hygiene only, but success criteria must not claim it remediates
   the nested Next PostCSS audit path unless audit output proves it.

5. For ESLint/minimatch, try only exact ESLint 9-compatible plugin or transitive
   remediation targets if npm metadata identifies them without force/major
   movement. Otherwise defer to a tooling compatibility sprint.

### Sprint 2 Validation Commands

Run after any trial dependency change:

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

### Rollback Commands

Use exact Git restore commands only for files changed by the dependency sprint:

```bash
git restore frontend/package.json frontend/package-lock.json
cd frontend
npm ci
```

Then rerun the affected validation commands. Do not restore unrelated user
changes.

### Success Criteria

- Audit count decreases, or the targeted finding group is removed.
- No new audit finding group is introduced.
- Frontend lint/build/typecheck/tests pass.
- Compose and production-demo Compose config pass.
- `bash scripts/ci/all-gates.sh` passes.
- Security docs are updated with before/after audit evidence.
- Stable deterministic demo behavior remains unchanged.

### Fallback / Defer Criteria

Defer instead of forcing remediation when:

- npm still requires force/major upgrades;
- no compatible Next 15 patch exists;
- lockfile churn is broad or unrelated;
- frontend tests or build fail;
- route behavior or runtime mode changes;
- native `sharp` installation changes Docker build behavior;
- remediation requires Next 16, ESLint 10, Tailwind 4, TypeScript 7, or package
  manager migration.

## Sprint 1 Conclusion

SPEC-025 Sprint 1 refreshed the audit baseline and produced a controlled
remediation matrix. The repository remains in the same dependency/product state
as before this sprint:

- 12 high npm audit findings remain.
- No dependencies were changed.
- No product behavior was changed.
- Next safe action is a reviewed SPEC-025 Sprint 2 remediation attempt or a
  separate major compatibility spec if force/major movement is required.
