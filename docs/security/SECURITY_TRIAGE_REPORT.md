# Security Triage Report - SPEC-024 Sprint 1

## Audit Metadata

Audit date/time:

```text
2026-07-28T09:10:11+07:00
```

Repository state:

```text
branch: main
commit: 838b9146a845e185d9186553fc6013d70feb65ab
release baseline: v1.0.0-demo-release
```

Sprint 1 is audit and documentation only. No dependency changes were made.

## Commands Run

```bash
git status --short
git diff --check
cd frontend && npm audit --json
cd frontend && npm audit
cd frontend && npm outdated || true
cd backend && poetry show --outdated || true
```

Raw npm audit JSON was written outside the repository to `/tmp` during local
triage and was not committed.

## Frontend Audit Summary

`npm audit --json` summary:

```text
total dependencies: 523
production dependencies: 19
development dependencies: 470
optional dependencies: 92
total vulnerabilities: 12
critical: 0
high: 12
moderate: 0
low: 0
```

Affected npm names reported by audit:

| Package | Classification | Notes |
| --- | --- | --- |
| `next` | Runtime framework, requires upgrade spec/patch sprint | Audit recommends `next@15.5.22`; current package pins `15.5.20`. Findings include Server Actions, cache confusion, rewrite SSRF, image optimization, and internal endpoint disclosure advisories. |
| `postcss` | Transitive runtime/build chain through Next | Audit maps remediation through `next@15.5.22`; do not patch ad hoc during audit-only work. |
| `sharp` | Transitive/optional image processing through Next | Audit maps remediation through `next@15.5.22`; relevant to image optimization paths. |
| `brace-expansion` | Dev-tooling transitive chain | Affects `minimatch` chain used by ESLint tooling. |
| `minimatch` | Dev-tooling transitive chain | Affects ESLint and ESLint plugin dependency graph. |
| `@eslint/config-array` | Dev-tooling transitive chain | Affected through `minimatch`. |
| `@eslint/eslintrc` | Direct dev dependency chain | Audit suggests force downgrade in one path; requires review, not automatic fix. |
| `eslint` | Direct dev tooling | Audit suggests `eslint@10.8.0` with force semantics. |
| `eslint-config-next` | Direct dev tooling | Latest compatible wanted version is `15.5.22`; latest major is `16.2.12`. |
| `eslint-plugin-import` | Dev-tooling transitive chain | Affected through `minimatch`. |
| `eslint-plugin-jsx-a11y` | Dev-tooling transitive chain | Affected through `minimatch`. |
| `eslint-plugin-react` | Dev-tooling transitive chain | Affected through `minimatch`. |

`npm audit` exited non-zero because vulnerabilities are present. This is
expected for the current baseline and is tracked by SPEC-024; no fix command was
run.

## Frontend Outdated Summary

`npm outdated || true` reported:

| Package | Current | Wanted | Latest |
| --- | --- | --- | --- |
| `@types/node` | `22.20.1` | `22.20.1` | `26.1.2` |
| `eslint` | `9.39.5` | `9.39.5` | `10.8.0` |
| `eslint-config-next` | `15.5.21` | `15.5.22` | `16.2.12` |
| `jsdom` | `25.0.1` | `25.0.1` | `30.0.0` |
| `next` | `15.5.20` | `15.5.20` | `16.2.12` |
| `postcss` | `8.5.22` | `8.5.23` | `8.5.23` |
| `tailwind-merge` | `2.6.1` | `2.6.1` | `3.6.0` |
| `tailwindcss` | `3.4.19` | `3.4.19` | `4.3.3` |
| `typescript` | `5.9.3` | `5.9.3` | `7.0.2` |

## Backend Outdated Summary

Host command result:

```text
poetry unavailable
```

Backend dependency review is not complete from the host environment. It should
be rerun in a future dependency maintenance sprint with Poetry available. No
backend dependency files were changed.

## Risk Assessment

Release baseline assessment:

- `v1.0.0-demo-release` remains stable and demo-ready.
- Configured release gates passed before this Sprint 1 task and are not changed
  by this audit/docs work.
- Current frontend npm audit findings should be remediated in a bounded future
  dependency patch sprint, not through automatic `npm audit fix`.
- Next/PostCSS/sharp findings are higher priority because they relate to
  frontend runtime/build framework paths.
- ESLint/minimatch findings appear primarily development-tooling related and
  should be handled separately from runtime findings.

Blocking status for `v1.0.0-demo-release`:

```text
Not blocking for the already tagged deterministic demo release, with documented
limitations and no dependency changes in Sprint 1.
```

This does not mean the findings should be ignored. They should be reviewed and
remediated in a future patch sprint before broader deployment or public
production use.

## Recommended Next Action

1. Review this triage report.
2. Open a bounded dependency patch sprint for safe frontend upgrades.
3. Prioritize `next` patch-level remediation if compatible with the existing
   Next 15 app.
4. Re-run `npm audit`, frontend gate, backend gate, all gates, and
   production-demo image build after any dependency change.
5. Prepare a separate major upgrade spec if remediation requires Next 16,
   ESLint 10, Tailwind 4, TypeScript 7, or other major upgrades.

## Explicit Sprint 1 Boundaries

- No dependency upgrades were made.
- `npm audit fix` was not run.
- `npm audit fix --force` was not run.
- `frontend/package.json` was not edited.
- `frontend/package-lock.json` was not edited.
- `backend/pyproject.toml` was not edited.
- `backend/poetry.lock` was not edited.
- No backend/frontend runtime behavior changed.
- No Docker/Compose/CI behavior changed.
- No provider calls, live web calls, real email, or final quote behavior were
  introduced.

