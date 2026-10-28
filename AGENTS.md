# Agent instructions

Multi-Agent OS is a headless Python/FastAPI/LangGraph runtime. Read the requested
outcome, `docs/WORKFLOW.md` and relevant current product/code/test evidence.
`docs/specs/SPEC-029-headless-oss-selfhost.md` supersedes the graduation web,
procurement, demo and RAG requirements. Do not restore those removed features.

Answers/reviews/status reports are read-only. Bounded changes use an ephemeral
plan. Work spanning sessions/agents/dependencies uses one resumable plan under
`docs/plans/active/`; archive only after validation. No legacy Harness
intake/story/trace database operation is required.

Before adding observable policy, identify product authority. Pause for unresolved
product choices, insufficient authority, difficult recovery or weakened security.
Do not delete existing operator data/volumes or publish/push/deploy remotely.
Use isolated named databases/Compose projects for persistence/recovery tests.

From `backend/`, run `poetry check --lock`, `poetry run ruff check app`,
`poetry run black --check app`, `poetry run mypy app`, and `poetry run pytest`.
Integration proof needs explicit `MAOS_TEST_DATABASE_URL`; test providers stay
inside tests. Live inference is separate and explicitly enabled/budgeted. Use
`scripts/ci/` for backend and Compose gates. Document exact proof and limitations;
fixture success does not prove live-provider or clean-release-image acceptance.

Keep secrets, prompts/raw provider bodies and token files out of logs/Git.
Report reusable agent friction; change guidance/tools for that purpose only when
explicitly requested through `$improve-harness`.
