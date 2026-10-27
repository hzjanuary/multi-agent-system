# Contributing

Read SPEC-029, AGENTS.md and docs/WORKFLOW.md. Keep product changes scoped to the
headless runtime and provide behavior-appropriate proof. Installed extensions
are trusted code; never add arbitrary imports or executable code to public input.

Python 3.12 and Poetry 1.8.5 are used by the container build. From `backend/`,
install the committed lock with `poetry install --with dev --no-root`. Development
and tests are excluded from the runtime image. CI runs Ruff, Black, strict MyPy,
unit/integration tests, the lock check and Compose configuration validation.
See `scripts/ci/backend-gate.sh` and `scripts/ci/compose-gate.sh` for exact commands.
Database/concurrency tests require actual isolated PostgreSQL/Redis services;
never run them against operator data. CI creates disposable services.

Use injected test providers only under tests. Contract tests do not establish
live provider compatibility. Real inference must be explicit and bounded; remote
calls need operator enablement. Do not download weights in tests or normal startup.
The public text_review extension is opt-in and consumes operator input.
For the explicitly optional, isolated free-model verification procedure, see
[OpenRouter free smoke](docs/openrouter-free-smoke.md) and
[direct Groq/Cloudflare campaign](docs/direct-smoke-campaign.md). Retained campaigns
are closed; a new live campaign needs separate explicit authorization. The OpenRouter permissive test data
policy is not the default for confidential deployments.

Use immutable workflow/extension versions and reproducible source fingerprints;
see docs/extending.md. Cover validation, approval, failure and recovery behavior
when affected. Keep README commands and release evidence honest. Do not suppress
failing acceptance checks or substitute fabricated successful output.

Contributions are under the project MIT license for material you have the right
to contribute. Preserve third-party notices. Do not commit secrets, auth files,
operator backups, database volumes or generated model data.
