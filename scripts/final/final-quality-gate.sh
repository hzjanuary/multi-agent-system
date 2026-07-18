#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SKIP_PROD_IMAGE_BUILD=0
INCLUDE_SCRIPT_HELP=1

usage() {
  cat <<'USAGE'
Usage: bash scripts/final/final-quality-gate.sh [options]

Runs the non-deploying final graduation quality gate wrapper.

Options:
  --skip-prod-image-build  Skip production-demo backend/frontend image build.
  --no-script-help         Skip smoke/E2E script help checks.
  -h, --help               Show this help.

The wrapper delegates to existing gates, does not start the production stack,
does not run mutating E2E validation, does not delete volumes, and does not
require real provider keys.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-prod-image-build)
      SKIP_PROD_IMAGE_BUILD=1
      shift
      ;;
    --no-script-help)
      INCLUDE_SCRIPT_HELP=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "${REPO_ROOT}"

run_step() {
  echo
  echo "==> $*"
  "$@"
}

run_step bash scripts/ci/compose-gate.sh
run_step bash scripts/ci/backend-gate.sh
run_step bash scripts/ci/frontend-gate.sh
run_step bash scripts/ci/all-gates.sh

if [[ "${SKIP_PROD_IMAGE_BUILD}" -eq 0 ]]; then
  run_step docker-compose -f docker-compose.prod.yml --env-file docs/deployment/.env.production.example build backend frontend
fi

if [[ "${INCLUDE_SCRIPT_HELP}" -eq 1 ]]; then
  run_step bash scripts/deployment/smoke-prod-demo.sh --help
  run_step bash scripts/final/e2e-demo-validation.sh --help
fi

run_step git diff --check
run_step git diff --cached --check

echo
echo "Final quality gate wrapper completed."

