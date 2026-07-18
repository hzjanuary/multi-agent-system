#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"

cd "${REPO_ROOT}"

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
DEMO_MANAGER_EMAIL="${DEMO_MANAGER_EMAIL:-manager@example.test}"
DEMO_MANAGER_PASSWORD="${DEMO_MANAGER_PASSWORD:-DemoPassword123!}"
DEMO_VIEWER_EMAIL="${DEMO_VIEWER_EMAIL:-viewer@example.test}"
DEMO_VIEWER_PASSWORD="${DEMO_VIEWER_PASSWORD:-DemoPassword123!}"
TARGET_WORKFLOW_ID="${TARGET_WORKFLOW_ID:-dc5e7963-c2a4-5ad6-8f70-0741431597f0}"
APPROVAL_COMMENT="${APPROVAL_COMMENT:-Approved by final E2E local-demo validation.}"
HTTP_TIMEOUT_SECONDS="${HTTP_TIMEOUT_SECONDS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-}"
BACKEND_CLI_SERVICE="${BACKEND_CLI_SERVICE:-backend-test}"

CONFIRM_LOCAL_DEMO=0
INCLUDE_READY=0
INCLUDE_RAG=0
INCLUDE_RBAC=0
INCLUDE_METRICS=0
SKIP_FRONTEND=0
SKIP_MIGRATIONS=0
SKIP_SEED=0
SKIP_INGEST=0
JSON_SUMMARY=0

SUMMARY_FILE="$(mktemp)"
TEMP_FILES=("${SUMMARY_FILE}")

cleanup() {
  for file in "${TEMP_FILES[@]}"; do
    [[ -n "${file}" && -f "${file}" ]] && rm -f "${file}"
  done
}
trap cleanup EXIT

usage() {
  cat <<'USAGE'
Usage: bash scripts/final/e2e-demo-validation.sh [options]

Default mode is non-mutating: checks backend /health, backend /live, and the
frontend root URL. The full workflow lifecycle validation requires
--confirm-local-demo because it runs migrations/seed commands and mutates demo
workflow state through existing APIs.

Options:
  --confirm-local-demo      Enable the full mutating local-demo E2E flow.
  --backend-url URL         Backend base URL. Default: http://localhost:8000
  --frontend-url URL        Frontend base URL. Default: http://localhost:3000
  --manager-email EMAIL     Demo Manager/Admin login email.
  --manager-password VALUE  Demo Manager/Admin password; never printed.
  --include-ready           Also check backend /ready.
  --include-rag             Run knowledge ingestion and verify RAG/search evidence.
  --include-rbac            Optionally verify Viewer approval/resume 403 behavior.
  --include-metrics         Optionally verify /api/v1/observability/metrics.
  --skip-frontend           Skip frontend root check.
  --skip-migrations         Do not run alembic upgrade head before full E2E.
  --skip-seed               Do not run demo seed before full E2E.
  --skip-ingest             Do not run knowledge ingestion for --include-rag.
  --json-summary            Print a machine-readable summary at the end.
  -h, --help                Show this help text.

Environment overrides:
  BACKEND_URL, FRONTEND_URL, TARGET_WORKFLOW_ID, APPROVAL_COMMENT
  DEMO_MANAGER_EMAIL, DEMO_MANAGER_PASSWORD
  DEMO_VIEWER_EMAIL, DEMO_VIEWER_PASSWORD
  HTTP_TIMEOUT_SECONDS, PYTHON_BIN
  COMPOSE_FILE, COMPOSE_ENV_FILE, BACKEND_CLI_SERVICE

Production-demo CLI example:
  COMPOSE_FILE=docker-compose.prod.yml \
  COMPOSE_ENV_FILE=docs/deployment/.env.production.example \
  BACKEND_CLI_SERVICE=backend \
  bash scripts/final/e2e-demo-validation.sh --confirm-local-demo --include-ready

Safety:
  Tokens, passwords, cookies, and Authorization headers are never printed.
  The script uses existing endpoints/CLIs only and never calls /run for resume.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --confirm-local-demo)
      CONFIRM_LOCAL_DEMO=1
      shift
      ;;
    --backend-url)
      BACKEND_URL="${2:?--backend-url requires a value}"
      shift 2
      ;;
    --frontend-url)
      FRONTEND_URL="${2:?--frontend-url requires a value}"
      shift 2
      ;;
    --manager-email)
      DEMO_MANAGER_EMAIL="${2:?--manager-email requires a value}"
      shift 2
      ;;
    --manager-password)
      DEMO_MANAGER_PASSWORD="${2:?--manager-password requires a value}"
      shift 2
      ;;
    --include-ready)
      INCLUDE_READY=1
      shift
      ;;
    --include-rag)
      INCLUDE_RAG=1
      shift
      ;;
    --include-rbac)
      INCLUDE_RBAC=1
      shift
      ;;
    --include-metrics)
      INCLUDE_METRICS=1
      shift
      ;;
    --skip-frontend)
      SKIP_FRONTEND=1
      shift
      ;;
    --skip-migrations)
      SKIP_MIGRATIONS=1
      shift
      ;;
    --skip-seed)
      SKIP_SEED=1
      shift
      ;;
    --skip-ingest)
      SKIP_INGEST=1
      shift
      ;;
    --json-summary)
      JSON_SUMMARY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required for E2E demo validation." >&2
  exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python is required for bounded JSON parsing. Set PYTHON_BIN if needed." >&2
  exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
elif docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
else
  COMPOSE=()
fi

if [[ "${CONFIRM_LOCAL_DEMO}" == "1" && "${#COMPOSE[@]}" -eq 0 ]]; then
  echo "Docker Compose is required for migration, seed, and ingestion commands." >&2
  exit 1
fi

BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

log() {
  echo "$*" >&2
}

record_check() {
  local status="$1"
  local name="$2"
  local detail="$3"
  printf '%s\t%s\t%s\n' "${status}" "${name}" "${detail}" >>"${SUMMARY_FILE}"
}

new_temp_file() {
  local file
  file="$(mktemp)"
  TEMP_FILES+=("${file}")
  printf '%s' "${file}"
}

json_eval() {
  local file="$1"
  local expression="$2"
  "${PYTHON_BIN}" - "${file}" "${expression}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
value = eval(sys.argv[2], {"__builtins__": {}}, {"data": data, "len": len, "any": any, "str": str})
if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("")
else:
    print(value)
PY
}

safe_error_summary() {
  local file="$1"
  "${PYTHON_BIN}" - "${file}" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
except Exception:
    print("non-json response")
    raise SystemExit(0)

detail = data.get("detail", data)
if isinstance(detail, dict):
    message = detail.get("message") or detail.get("code") or "request failed"
elif isinstance(detail, str):
    message = detail
else:
    message = "request failed"
print(str(message).replace("\n", " ")[:300])
PY
}

http_request() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local body="${4:-}"
  HTTP_RESPONSE_FILE="$(new_temp_file)"
  local args=(-sS --max-time "${HTTP_TIMEOUT_SECONDS}" -o "${HTTP_RESPONSE_FILE}" -w "%{http_code}" -X "${method}")
  if [[ -n "${token}" ]]; then
    args+=(-H "Authorization: Bearer ${token}")
  fi
  if [[ -n "${body}" ]]; then
    args+=(-H "Content-Type: application/json" --data "${body}")
  fi
  set +e
  HTTP_STATUS="$(curl "${args[@]}" "${url}" 2>/dev/null)"
  local curl_exit=$?
  set -e
  if [[ "${curl_exit}" -ne 0 ]]; then
    HTTP_STATUS="000"
  fi
}

require_status() {
  local name="$1"
  local expected="$2"
  if [[ "${HTTP_STATUS}" != "${expected}" ]]; then
    local detail
    detail="$(safe_error_summary "${HTTP_RESPONSE_FILE}")"
    record_check "fail" "${name}" "HTTP ${HTTP_STATUS}; ${detail}"
    echo "${name} failed: expected HTTP ${expected}, got ${HTTP_STATUS}; ${detail}" >&2
    exit 1
  fi
  record_check "pass" "${name}" "HTTP ${HTTP_STATUS}"
}

check_http_ok() {
  local name="$1"
  local url="$2"
  log "==> ${name}"
  http_request "GET" "${url}"
  require_status "${name}" "200"
}

compose_run_backend() {
  local args=(-f "${COMPOSE_FILE}")
  if [[ -n "${COMPOSE_ENV_FILE}" ]]; then
    args+=(--env-file "${COMPOSE_ENV_FILE}")
  fi
  "${COMPOSE[@]}" "${args[@]}" run --rm "${BACKEND_CLI_SERVICE}" "$@"
}

compact_cli_summary() {
  local file="$1"
  "${PYTHON_BIN}" - "${file}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

keys = [
    "committed",
    "dry_run",
    "documents_seen",
    "chunks_seen",
    "vectors_upserted",
]
parts = [f"{key}={data[key]}" for key in keys if key in data]
workflow_seed = data.get("workflow_seed")
if isinstance(workflow_seed, dict):
    for key in ("workflows_created", "workflows_reused", "workflows_updated", "events_created", "events_reused", "events_updated"):
        if key in workflow_seed:
            parts.append(f"{key}={workflow_seed[key]}")
print(", ".join(parts)[:500])
PY
}

login_user() {
  local email="$1"
  local password="$2"
  local label="$3"
  local body
  body="$("${PYTHON_BIN}" - "${email}" "${password}" <<'PY'
import json
import sys

print(json.dumps({"email": sys.argv[1], "password": sys.argv[2]}))
PY
)"
  log "==> Authenticating ${label}"
  http_request "POST" "${BACKEND_URL}/api/v1/auth/login" "" "${body}"
  require_status "login ${label}" "200"
  local token
  token="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('access_token', '')")"
  if [[ -z "${token}" ]]; then
    record_check "fail" "login ${label} token" "access_token missing"
    echo "login ${label} failed: access_token missing" >&2
    exit 1
  fi
  record_check "pass" "login ${label} token" "token received but not printed"
  printf '%s' "${token}"
}

event_contains() {
  local file="$1"
  local needle="$2"
  "${PYTHON_BIN}" - "${file}" "${needle}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
needle = sys.argv[2]
events = data.get("events", [])
found = any(
    needle in str(event.get("event_type", ""))
    or needle in str(event.get("message", ""))
    for event in events
)
print("true" if found else "false")
PY
}

rag_evidence_count() {
  local file="$1"
  "${PYTHON_BIN}" - "${file}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
workflow = data.get("workflow", data)
state_sources = [
    workflow.get("runtime_context", {}).get("rag", {}),
    workflow.get("outputs", {}).get("evidence", {}),
]
stage_outputs = workflow.get("stage_outputs") or {}
if isinstance(stage_outputs, dict):
    state_sources.extend(
        value.get("evidence", {}) for value in stage_outputs.values() if isinstance(value, dict)
    )

count = 0
for source in state_sources:
    if isinstance(source, dict):
        citations = source.get("citations") or source.get("evidence") or source.get("results") or []
        if isinstance(citations, list):
            count += len(citations)
        elif isinstance(citations, dict):
            count += len(citations.get("citations", []))
    elif isinstance(source, list):
        count += len(source)
print(count)
PY
}

assert_status_value() {
  local name="$1"
  local file="$2"
  local expected="$3"
  local actual
  actual="$(json_eval "${file}" "(data.get('workflow') or data).get('status', data.get('status', ''))")"
  if [[ "${actual}" != "${expected}" ]]; then
    record_check "fail" "${name}" "expected ${expected}, got ${actual}"
    echo "${name} failed: expected ${expected}, got ${actual}" >&2
    exit 1
  fi
  record_check "pass" "${name}" "status=${actual}"
}

print_summary() {
  if [[ "${JSON_SUMMARY}" != "1" ]]; then
    return
  fi
  "${PYTHON_BIN}" - "${SUMMARY_FILE}" "${BACKEND_URL}" "${FRONTEND_URL}" "${CONFIRM_LOCAL_DEMO}" "${INCLUDE_RAG}" <<'PY'
import json
import sys
from datetime import UTC, datetime

checks = []
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        status, name, detail = line.rstrip("\n").split("\t", 2)
        checks.append({"status": status, "name": name, "detail": detail})

print(json.dumps({
    "timestamp": datetime.now(UTC).isoformat(),
    "backend_url": sys.argv[2],
    "frontend_url": sys.argv[3],
    "mutating_local_demo": sys.argv[4] == "1",
    "rag_enabled_validation": sys.argv[5] == "1",
    "status": "passed" if all(check["status"] == "pass" for check in checks) else "failed",
    "checks": checks,
}, indent=2))
PY
}

log "==> Final E2E demo validation"
record_check "pass" "script mode" "confirm_local_demo=${CONFIRM_LOCAL_DEMO}, include_rag=${INCLUDE_RAG}"

check_http_ok "backend /health" "${BACKEND_URL}/health"
check_http_ok "backend /live" "${BACKEND_URL}/live"

if [[ "${INCLUDE_READY}" == "1" ]]; then
  check_http_ok "backend /ready" "${BACKEND_URL}/ready"
else
  record_check "pass" "backend /ready" "skipped"
fi

if [[ "${SKIP_FRONTEND}" == "1" ]]; then
  record_check "pass" "frontend root" "skipped"
else
  check_http_ok "frontend root" "${FRONTEND_URL}/"
fi

if [[ "${CONFIRM_LOCAL_DEMO}" != "1" ]]; then
  log "Non-mutating checks passed. Add --confirm-local-demo for the full workflow lifecycle validation."
  print_summary
  exit 0
fi

if [[ "${SKIP_MIGRATIONS}" != "1" ]]; then
  log "==> Running migrations explicitly"
  compose_run_backend alembic upgrade head >/dev/null
  record_check "pass" "migrations" "alembic upgrade head completed"
else
  record_check "pass" "migrations" "skipped"
fi

if [[ "${SKIP_SEED}" != "1" ]]; then
  log "==> Running deterministic demo seed"
  seed_file="$(new_temp_file)"
  compose_run_backend python -m app.demo.seed --confirm-local-demo --json >"${seed_file}"
  seed_detail="$(compact_cli_summary "${seed_file}")"
  record_check "pass" "demo seed" "${seed_detail}"
else
  record_check "pass" "demo seed" "skipped"
fi

if [[ "${INCLUDE_RAG}" == "1" && "${SKIP_INGEST}" != "1" ]]; then
  log "==> Running deterministic knowledge ingestion"
  ingest_file="$(new_temp_file)"
  compose_run_backend python -m app.knowledge.ingest_demo --confirm-local-demo --json >"${ingest_file}"
  ingest_detail="$(compact_cli_summary "${ingest_file}")"
  record_check "pass" "knowledge ingestion" "${ingest_detail}"
elif [[ "${INCLUDE_RAG}" == "1" ]]; then
  record_check "pass" "knowledge ingestion" "skipped"
fi

MANAGER_TOKEN="$(login_user "${DEMO_MANAGER_EMAIL}" "${DEMO_MANAGER_PASSWORD}" "manager/admin demo user")"

log "==> Listing workflows"
http_request "GET" "${BACKEND_URL}/api/v1/workflows?limit=100" "${MANAGER_TOKEN}"
require_status "workflow list" "200"
workflow_count="$(json_eval "${HTTP_RESPONSE_FILE}" "len(data.get('workflows', []))")"
record_check "pass" "workflow list count" "count=${workflow_count}"

log "==> Fetching target workflow ${TARGET_WORKFLOW_ID}"
http_request "GET" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}" "${MANAGER_TOKEN}"
require_status "workflow detail before run" "200"
assert_status_value "target workflow before run" "${HTTP_RESPONSE_FILE}" "CREATED"

log "==> Running workflow to WAITING_APPROVAL"
http_request "POST" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/run" "${MANAGER_TOKEN}"
require_status "workflow run" "200"
run_status="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('status', '')")"
waiting_for_approval="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('waiting_for_approval', False)")"
if [[ "${run_status}" != "WAITING_APPROVAL" || "${waiting_for_approval}" != "true" ]]; then
  record_check "fail" "workflow run wait state" "status=${run_status}, waiting_for_approval=${waiting_for_approval}"
  echo "workflow run did not stop at WAITING_APPROVAL" >&2
  exit 1
fi
record_check "pass" "workflow run wait state" "status=${run_status}, waiting_for_approval=${waiting_for_approval}"

http_request "GET" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}" "${MANAGER_TOKEN}"
require_status "workflow detail after run" "200"
assert_status_value "target workflow after run" "${HTTP_RESPONSE_FILE}" "WAITING_APPROVAL"
detail_after_run_file="${HTTP_RESPONSE_FILE}"

http_request "GET" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/events?limit=100" "${MANAGER_TOKEN}"
require_status "workflow events after run" "200"
event_count="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('count', len(data.get('events', [])))")"
record_check "pass" "workflow event count after run" "count=${event_count}"

if [[ "${INCLUDE_RAG}" == "1" ]]; then
  log "==> Checking knowledge search and RAG evidence"
  http_request "GET" "${BACKEND_URL}/api/v1/knowledge/documents" "${MANAGER_TOKEN}"
  require_status "knowledge document catalog" "200"
  document_count="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('count', len(data.get('documents', [])))")"
  record_check "pass" "knowledge document count" "count=${document_count}"

  search_body='{"query":"procurement policy approval evidence","top_k":3,"domain":"procurement"}'
  http_request "POST" "${BACKEND_URL}/api/v1/knowledge/search" "${MANAGER_TOKEN}" "${search_body}"
  require_status "knowledge search" "200"
  search_count="$(json_eval "${HTTP_RESPONSE_FILE}" "len(data.get('results', []))")"
  if [[ "${search_count}" -lt 1 ]]; then
    record_check "fail" "knowledge search results" "count=0"
    echo "RAG validation failed: knowledge search returned no results" >&2
    exit 1
  fi
  record_check "pass" "knowledge search results" "count=${search_count}"

  evidence_count="$(rag_evidence_count "${detail_after_run_file}")"
  if [[ "${evidence_count}" -lt 1 ]]; then
    record_check "fail" "workflow RAG evidence" "citation_count=0"
    echo "RAG validation failed: workflow detail has no attached evidence citations" >&2
    exit 1
  fi
  record_check "pass" "workflow RAG evidence" "citation_count=${evidence_count}"
fi

log "==> Submitting approval"
approval_body="$("${PYTHON_BIN}" - "${APPROVAL_COMMENT}" <<'PY'
import json
import sys

print(json.dumps({
    "decision": "approve",
    "comment": sys.argv[1],
    "request_id": "final-e2e-approval",
    "metadata": {"source": "final_e2e_demo_validation"},
}))
PY
)"
http_request "POST" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/approval" "${MANAGER_TOKEN}" "${approval_body}"
require_status "workflow approval" "200"
approval_next_status="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('next_status', '')")"
if [[ "${approval_next_status}" != "APPROVED" ]]; then
  record_check "fail" "approval status" "next_status=${approval_next_status}"
  echo "approval did not produce APPROVED status" >&2
  exit 1
fi
record_check "pass" "approval status" "next_status=${approval_next_status}"

http_request "GET" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/approval/history" "${MANAGER_TOKEN}"
require_status "approval history" "200"
history_count="$(json_eval "${HTTP_RESPONSE_FILE}" "len(data.get('approvals', []))")"
can_resume="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('can_resume', False)")"
if [[ "${history_count}" -lt 1 || "${can_resume}" != "true" ]]; then
  record_check "fail" "approval history final" "count=${history_count}, can_resume=${can_resume}"
  echo "approval history did not show a resumable final approval" >&2
  exit 1
fi
record_check "pass" "approval history final" "count=${history_count}, can_resume=${can_resume}"

log "==> Resuming through /resume"
http_request "POST" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/resume" "${MANAGER_TOKEN}" '{"request_id":"final-e2e-resume","metadata":{"source":"final_e2e_demo_validation"}}'
require_status "workflow resume" "200"
resume_status="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('next_status', '')")"
resumed="$(json_eval "${HTTP_RESPONSE_FILE}" "data.get('resumed', False)")"
if [[ "${resume_status}" != "COMPLETED" || "${resumed}" != "true" ]]; then
  record_check "fail" "resume completed" "next_status=${resume_status}, resumed=${resumed}"
  echo "resume did not complete workflow" >&2
  exit 1
fi
record_check "pass" "resume completed" "next_status=${resume_status}, resumed=${resumed}; endpoint=/resume"

http_request "GET" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}" "${MANAGER_TOKEN}"
require_status "workflow detail after resume" "200"
assert_status_value "target workflow after resume" "${HTTP_RESPONSE_FILE}" "COMPLETED"

http_request "GET" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/events?limit=100" "${MANAGER_TOKEN}"
require_status "workflow events after resume" "200"
resume_event_found="$(event_contains "${HTTP_RESPONSE_FILE}" "workflow.resumed")"
email_event_found="$(event_contains "${HTTP_RESPONSE_FILE}" "email_preparation")"
approval_event_found="$(event_contains "${HTTP_RESPONSE_FILE}" "approval")"
if [[ "${resume_event_found}" != "true" || "${email_event_found}" != "true" || "${approval_event_found}" != "true" ]]; then
  record_check "fail" "timeline approval/resume events" "approval=${approval_event_found}, resume=${resume_event_found}, email_preparation=${email_event_found}"
  echo "timeline did not include expected approval/resume/email_preparation events" >&2
  exit 1
fi
record_check "pass" "timeline approval/resume events" "approval=${approval_event_found}, resume=${resume_event_found}, email_preparation=${email_event_found}"

if [[ "${INCLUDE_RBAC}" == "1" ]]; then
  VIEWER_TOKEN="$(login_user "${DEMO_VIEWER_EMAIL}" "${DEMO_VIEWER_PASSWORD}" "viewer demo user")"
  log "==> Checking Viewer mutation denial"
  http_request "POST" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/approval" "${VIEWER_TOKEN}" "${approval_body}"
  if [[ "${HTTP_STATUS}" != "403" ]]; then
    record_check "fail" "viewer approval forbidden" "HTTP ${HTTP_STATUS}"
    echo "viewer approval mutation was not forbidden" >&2
    exit 1
  fi
  record_check "pass" "viewer approval forbidden" "HTTP ${HTTP_STATUS}"
  http_request "POST" "${BACKEND_URL}/api/v1/workflows/${TARGET_WORKFLOW_ID}/resume" "${VIEWER_TOKEN}" '{}'
  if [[ "${HTTP_STATUS}" != "403" ]]; then
    record_check "fail" "viewer resume forbidden" "HTTP ${HTTP_STATUS}"
    echo "viewer resume mutation was not forbidden" >&2
    exit 1
  fi
  record_check "pass" "viewer resume forbidden" "HTTP ${HTTP_STATUS}"
fi

if [[ "${INCLUDE_METRICS}" == "1" ]]; then
  log "==> Checking metrics endpoint"
  http_request "GET" "${BACKEND_URL}/api/v1/observability/metrics" "${MANAGER_TOKEN}"
  require_status "observability metrics" "200"
  record_check "pass" "metrics safety" "response fetched with bearer auth; token not printed"
fi

log "Final E2E demo validation passed."
print_summary
