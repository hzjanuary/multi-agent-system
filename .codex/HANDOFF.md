# Context Handoff

## Current Project Status

Closed specs:

- SPEC-001 Bootstrap Backend - Approved / Closed
- SPEC-002 Database Foundation - Approved / Closed
- SPEC-003 Authentication and RBAC - Approved / Closed
- SPEC-004 Storage Infrastructure - Approved / Closed
- SPEC-005 Workflow State - Approved / Closed

Current active spec:

- SPEC-007 Workflow API Endpoints

## Completed SPEC-007 Tasks

- TASK 007.1 Workflow API Schemas and Error Mapping - Approved
- TASK 007.2 Workflow API Router Foundation - Approved
- TASK 007.3 Create/Get/List Workflow Endpoints - Approved
- TASK 007.4 Workflow Status Transition Endpoint - Approved
- TASK 007.5 Workflow State Update Endpoint - Approved
- TASK 007.6 Workflow Events Read Endpoint - Approved
- TASK 007.7 Workflow API Auth/RBAC Tests and Hardening - Implemented, awaiting review

## Next Task

- SPEC-007 Final Review

## Current Quality Gate

- `git status --short`
- `docker-compose config`
- `docker-compose up -d postgres`
- `docker-compose run --rm backend-test alembic upgrade head`
- `docker-compose build backend-test`
- `docker-compose run --rm backend-test pytest`
- `docker-compose run --rm backend-test ruff check .`
- `docker-compose run --rm backend-test black --check .`
- `docker-compose run --rm backend-test mypy app`
- `git diff --check`

## Important Constraints For SPEC-007 Final Review

- Review only; do not implement application code during final review.
- Confirm workflow REST endpoints use existing SPEC-005 services.
- Confirm auth/RBAC policies match the SPEC-007 baseline.
- Confirm direct Pydantic response models remain in use; no global envelope was
  introduced.
- Confirm run/resume routes remain deferred to SPEC-006.
- Confirm event streaming remains deferred to SPEC-008.
- Confirm no LangGraph runtime, agents, LLM providers, RAG, document indexing,
  frontend, audit query APIs, migrations, model changes, or procurement-specific
  runtime logic were implemented.

## Known Warnings

- Existing FastAPI/TestClient StarletteDeprecationWarning is non-blocking.
- LF/CRLF README and Python file warnings from `git diff --check` are
  non-blocking when no whitespace errors are reported.

## Harness State

- TASK 007.1 recorded and validated.
- TASK 007.2 recorded and validated.
- TASK 007.3 recorded and validated.
- TASK 007.4 recorded and validated.
- TASK 007.5 recorded and validated.
- TASK 007.6 recorded and validated.
- TASK 007.7 should be recorded after review of current changes.

## Files Likely Relevant For Next Task

- `.ai/specs/SPEC-007-workflow-api/spec.md`
- `.ai/specs/SPEC-007-workflow-api/tasks.md`
- `backend/app/api/v1/workflows.py`
- `backend/app/api/v1/workflow_errors.py`
- `backend/app/schemas/workflows_api.py`
- `backend/app/workflows/`
- `backend/app/tests/test_workflow_api_create_get_list.py`
- `backend/app/tests/test_workflow_api_router.py`
- `backend/app/tests/test_workflow_api_schemas.py`
- `backend/README.md`
