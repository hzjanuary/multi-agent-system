# Enterprise Multi-Agent OS Backend

FastAPI backend foundation for Enterprise Multi-Agent OS.

This backend contains the foundation layer for Enterprise Multi-Agent OS:
project structure, settings, logging, middleware, health endpoints, Docker
support, a reproducible Docker-based quality gate, and the SPEC-002 database
foundation. Authentication, workflow runtime, agents, storage clients, and
business modules are intentionally out of scope for the current backend
foundation.

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

## Health Endpoints

The backend exposes lightweight service endpoints:

```text
GET /       service metadata and endpoint links
GET /health overall application health
GET /ready  readiness with lightweight placeholder checks
GET /live   liveness status
```

Readiness does not perform database, Redis, Qdrant, or MinIO checks yet. Those
clients are introduced by later implementation tasks.

## Database

The async SQLAlchemy foundation lives in `app/db/session.py`.

It provides:

```text
create_database_engine()  builds an AsyncEngine from DATABASE_URL
create_session_factory()  builds an async_sessionmaker[AsyncSession]
provide_db_session()      FastAPI dependency for request-scoped sessions
```

`DATABASE_URL` is loaded from the typed settings model. This foundation prepares
the async engine/session layer; repositories are introduced by later SPEC-002
tasks.

The declarative model base and shared mixins live in:

```text
app/db/base.py    DeclarativeBase with Alembic-friendly naming conventions
app/db/mixins.py  UUID primary key, timestamp, and soft-delete mixins
```

Models should inherit from `Base` and the relevant mixins. Repositories and
business services are intentionally deferred to later SPEC-002 tasks.

Phase 1 core models are registered through `app/models/__init__.py` so
`Base.metadata` can discover:

```text
users
roles
user_roles
workflows
workflow_events
audit_logs
```

The model layer defines table shape and relationships only. Authentication
services and workflow runtime behavior are separate tasks.

Generic repository primitives live in:

```text
app/repositories/base.py  BaseRepository with caller-owned AsyncSession
app/repositories/crud.py  CRUDRepository with reusable async model operations
```

Repositories receive an `AsyncSession` from the caller. They do not create
sessions and do not commit transactions automatically; transaction boundaries
stay in the service or request layer.

Alembic is configured for async SQLAlchemy in:

```text
alembic.ini
alembic/env.py
alembic/versions/0001_create_phase_1_core_tables.py
```

Run migrations through the Docker test environment from the repository root:

```bash
docker-compose up -d postgres
docker-compose run --rm backend-test alembic upgrade head
docker-compose run --rm backend-test alembic current
docker-compose run --rm backend-test alembic downgrade base
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

## Docker

Build and run the backend plus Phase 1 infrastructure services from the
repository root:

```bash
docker-compose config
docker-compose up --build backend
```

The Compose stack includes:

```text
backend   FastAPI API on http://localhost:8000
postgres  PostgreSQL on localhost:5432
redis     Redis on localhost:6379
qdrant    Qdrant on http://localhost:6333
minio     MinIO API on http://localhost:9000 and console on http://localhost:9001
```

After the backend starts, verify:

```bash
curl http://localhost:8000/health
```

The Docker Compose file uses development defaults only. Do not reuse demo
passwords or API keys for production deployments.

## Logging And Middleware

`app/main.py` wires the core middleware foundation:

- `RequestIdMiddleware` attaches a request ID to every request.
- If `X-Request-ID` is provided, the same value is reused.
- If `X-Request-ID` is missing, a UUID request ID is generated.
- Every response includes `X-Request-ID`.
- `RequestLoggingMiddleware` emits JSON-compatible request logs with
  `request_id`, `method`, `path`, `status_code`, and `duration_ms`.
- CORS origins are loaded from `BACKEND_CORS_ORIGINS`.
- GZip response compression is enabled.
- The global exception handler returns the standard JSON error envelope.

## Test And Check

Run the reproducible Python 3.12 Docker quality gate from the repository root:

```bash
docker-compose run --rm backend-test pytest
docker-compose run --rm backend-test ruff check .
docker-compose run --rm backend-test black --check .
docker-compose run --rm backend-test mypy app
```

The `backend` image installs only runtime dependencies. The `backend-test`
service uses the Dockerfile `dev` target and installs development dependencies
for validation.
