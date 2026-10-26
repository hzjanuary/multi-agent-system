#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPO_ROOT}"
bash scripts/ci/backend-gate.sh
bash scripts/ci/compose-gate.sh
python3 scripts/ops/scan_secrets.py --strict --allow-test-placeholders
git diff --check
