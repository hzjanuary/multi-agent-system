# Enterprise Multi-Agent OS Backend

FastAPI backend foundation for Enterprise Multi-Agent OS.

This skeleton belongs to `SPEC-001` / `TASK 001.1` and intentionally contains
only the base project structure. Database models, authentication, workflow
runtime, agents, storage clients, health endpoints, and Docker setup are
implemented by later tasks.

## Requirements

- Python 3.12
- Poetry

## Install

```bash
poetry install
```

## Run Locally

```bash
poetry run uvicorn app.main:app --reload
```

The OpenAPI documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Settings

Application settings live in `app/config/settings.py` and are loaded with
Pydantic v2 through `pydantic-settings`.

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Supported environments are:

```text
development
testing
production
```

Settings can be overridden with environment variables such as:

```bash
APP_ENV=testing
DEBUG=false
LOG_LEVEL=DEBUG
```

Do not commit real API keys, database credentials, or object storage secrets.

## Test And Check

```bash
poetry run pytest
poetry run ruff check .
poetry run black --check .
poetry run mypy app
```
