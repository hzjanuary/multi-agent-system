# SPEC-019 Tasks - Provider Live Verification

## Task List

### TASK 019.1 - Live Verification Spec And Policy Checklist

Status: Planned.

Goal: Define the manual live-provider verification policy before adding any
live smoke command.

Scope:

- Document provider endpoint, authentication, data retention, rate-limit, and
  terms/policy checks.
- Define redaction requirements and no-key CI boundary.
- Confirm Tavily is the first target provider.
- Do not call Tavily or add scripts in this planning task.

Acceptance criteria:

- Provider policy checklist exists.
- Live verification is explicitly manual-only.
- CI remains no-key and mocked.

Validation:

```bash
git diff --check
git status --short
```

### TASK 019.2 - Manual Tavily Smoke Script With Explicit Confirmation

Status: Planned.

Goal: Add a local smoke utility that can verify Tavily configuration only when
the operator explicitly confirms live provider use.

Scope:

- Add a script such as `scripts/demo/provider_live_smoke.py`.
- Require `--confirm-live-provider` before any network call.
- Read `TAVILY_API_KEY` from local environment only.
- Use the existing SPEC-016 Tavily provider/service boundary.
- Do not create workflows, poll Telegram, approve, resume, or send email.

Acceptance criteria:

- `--help` works without a key.
- Missing confirmation prevents live calls.
- Missing key fails safely when Tavily is selected.
- No raw provider payloads or keys are printed.

Validation:

```bash
python3 scripts/demo/provider_live_smoke.py --help
python3 scripts/demo/provider_live_smoke.py --provider tavily
git diff --check
```

### TASK 019.3 - Safe JSON Output And Redaction Tests

Status: Planned.

Goal: Prove live smoke output remains bounded, redacted, and evidence-only.

Scope:

- Add tests with injected/mocked transport only.
- Assert no API key, Authorization header, raw provider payload, raw HTML,
  token, cookie, prompt, or secret is printed.
- Assert output keeps `is_final_quote=false`.
- Assert no price is inferred from snippets.

Acceptance criteria:

- Tests require no real Tavily key and no network access.
- Timeout, non-2xx, invalid JSON, malformed results, and missing key cases are
  covered.

Validation:

```bash
docker compose run --rm backend-test pytest app/tests/test_price_research_tavily_provider.py -q
python3 -m unittest scripts.demo.test_provider_live_smoke
git diff --check
```

### TASK 019.4 - Docs For Local Provider Verification

Status: Planned.

Goal: Document how to run live provider verification safely outside CI.

Scope:

- Add or update docs under `docs/llm/` or `docs/demo/`.
- Include environment variables, confirmation flag, expected safe output, and
  troubleshooting.
- State that Telegram and workflows still do not call live providers by
  default.
- Warn against committing keys or output containing sensitive data.

Acceptance criteria:

- Docs are clear enough for a local operator.
- Docs do not imply live provider verification is required for the stable demo.

Validation:

```bash
git diff --check
git status --short
```

### TASK 019.5 - Final Validation And Docs

Status: Planned.

Goal: Close SPEC-019 with full validation and updated handoff.

Scope:

- Run focused script/provider tests.
- Run backend gates and all-gates.
- Confirm no CI key requirement or runtime integration was introduced.
- Update SPEC/HANDOFF status.

Acceptance criteria:

- SPEC-019 is ready for review/closure.
- Manual live smoke is isolated, explicit, redacted, and non-mutating.
- No Telegram/workflow automatic live provider behavior exists.

Validation:

```bash
git status --short
python3 scripts/demo/provider_live_smoke.py --help
docker compose run --rm backend-test pytest -q
docker compose run --rm backend-test ruff check .
docker compose run --rm backend-test black --check .
docker compose run --rm backend-test mypy app
bash scripts/ci/all-gates.sh
git diff --check
```

Manual live validation remains optional and must be run only with a private
local key:

```bash
TAVILY_API_KEY="<set locally>" python3 scripts/demo/provider_live_smoke.py --provider tavily --confirm-live-provider
```
