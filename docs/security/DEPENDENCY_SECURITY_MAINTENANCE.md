# Dependency Security Maintenance

## Purpose

This guide defines how to review and remediate dependency security findings for
Multi-Agent System / Enterprise Multi-Agent OS without destabilizing the
deterministic demo path.

Audit and triage work is separate from dependency upgrade work. Do not run
automatic fix commands during audit-only tasks.

## Frontend Audit Commands

Run from the repository root:

```bash
cd frontend
npm audit --json > /tmp/multi-agent-system-npm-audit.json
npm audit
npm outdated || true
```

Keep raw JSON outside the repository unless a future task explicitly asks for a
sanitized artifact. The JSON can be noisy and may include paths that are not
useful in public docs.

## How To Read npm audit

Review:

- severity count;
- direct versus transitive dependency;
- production/runtime dependency versus development tooling;
- advisory title and affected package range;
- whether a fix is available;
- whether npm requires `--force`;
- whether npm recommends a major or out-of-range upgrade;
- whether the vulnerable path is reachable in the deployed/runtime flow.

Do not equate every high-severity finding with an immediate release blocker.
Classify the issue first.

## When To Use npm audit fix

Use `npm audit fix` only in a future dependency remediation sprint when:

- the exact package changes are reviewed;
- the change stays inside the accepted dependency range;
- lockfile changes are expected;
- frontend lint/build/typecheck/test are run afterward;
- full repository gates are run afterward.

## When Not To Use npm audit fix

Do not use `npm audit fix` during:

- audit-only tasks;
- release snapshot/report-only tasks;
- demo preparation immediately before presentation;
- any task that forbids dependency changes;
- any task where package manager output recommends `--force`.

Do not use `npm audit fix --force` unless a spec or task explicitly approves the
breaking changes it may introduce.

## Dev Dependency Vulnerabilities

For dev dependency chains, such as ESLint plugins or test/build tooling:

- classify separately from runtime vulnerabilities;
- check whether the vulnerable package is included in production runtime images;
- check whether exploitation requires trusted local developer input;
- remediate in a planned maintenance sprint, not by emergency force upgrade,
  unless the project risk changes.

## Transitive Vulnerabilities

For transitive dependencies:

- identify the top-level package that brings them in;
- prefer upgrading the top-level package in a reviewed sprint;
- avoid direct overrides unless a future task documents the reason;
- rerun tests and production-demo builds after changes.

## Backend Dependency Review

Run when Poetry is available:

```bash
cd backend
poetry show --outdated || true
```

Backend dependency updates must be scoped because they can affect FastAPI,
Pydantic, SQLAlchemy, auth, storage providers, LangGraph runtime behavior, and
test fixtures.

Do not edit `backend/pyproject.toml` or `backend/poetry.lock` during audit-only
work.

## Required Validation After Upgrades

After any future frontend dependency change:

```bash
cd frontend
npm audit
npm run lint
npm run build
npm run typecheck
npm test
```

After any future backend dependency change:

```bash
cd backend
poetry show --outdated || true
```

From the repository root:

```bash
git diff --check
docker compose config
docker compose -f docker-compose.prod.yml \
  --env-file docs/deployment/.env.production.example config
bash scripts/ci/backend-gate.sh
bash scripts/ci/frontend-gate.sh
bash scripts/ci/all-gates.sh
```

## Rollback Steps

If a dependency update fails validation:

1. Stop and keep the failed branch unmerged.
2. Restore the previous package manifest and lockfile versions.
3. Reinstall dependencies from the restored lockfile.
4. Rebuild local and production-demo images.
5. Rerun the relevant gates.
6. Record the failure and package versions in the triage report.

Do not revert unrelated user changes.

## No-Secrets Reminder

Never commit:

- provider API keys;
- Telegram bot tokens;
- backend access tokens;
- JWT production secrets;
- cookies;
- local `.env` files;
- `docker-compose.override.yml`;
- raw provider payloads;
- raw prompts;
- embeddings/vector payloads;
- real customer data.

Security reports should summarize findings without exposing secrets or local
machine-specific tokens.

