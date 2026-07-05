# SPEC-001 — Bootstrap Backend

## Goal

Create the production-ready FastAPI backend foundation.

## Required Stack

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic v2
- Poetry
- Ruff
- Black
- MyPy
- Pytest
- Structlog
- Docker
- Docker Compose

## In Scope

- Backend app structure
- Settings
- Logging
- Middleware
- Health endpoints
- Dockerfile
- Docker Compose with backend, postgres, redis, qdrant and minio
- Unit tests
- README

## Out of Scope

- Database models
- Authentication
- LangGraph
- Agents
- LLM
- RAG

## Required Endpoints

- GET /
- GET /health
- GET /ready
- GET /live

## Acceptance Criteria

- docker compose up works
- GET /health returns 200
- /docs loads
- pytest passes
- ruff passes
