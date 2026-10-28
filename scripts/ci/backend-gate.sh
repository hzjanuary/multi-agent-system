#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPO_ROOT}/backend"
poetry check --lock
poetry run pytest
poetry run ruff check app maos_examples
poetry run black --check app maos_examples alembic
poetry run mypy app maos_examples
