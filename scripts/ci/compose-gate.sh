#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${REPO_ROOT}"
docker compose --env-file "${MAOS_ENV_FILE:-.maos/.env}" config --quiet
docker compose --env-file "${MAOS_ENV_FILE:-.maos/.env}" -f docker-compose.yml -f docker-compose.override.example.yml config --quiet
