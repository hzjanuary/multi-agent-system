# Enterprise Multi-Agent OS Backend

FastAPI backend foundation for Enterprise Multi-Agent OS.

This backend contains the foundation layer for Enterprise Multi-Agent OS:
project structure, settings, logging, middleware, health endpoints, Docker
support, a reproducible Docker-based quality gate, the SPEC-002 database
foundation, and SPEC-003 authentication/RBAC foundation. Workflow runtime,
agents, storage clients, and business modules are intentionally out of scope for
the current backend foundation.

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

## Authentication Utilities

Password hashing utilities live in `app/auth/password.py`.

```text
hash_password()            hashes plain-text passwords with Argon2
verify_password()          verifies plain text against an Argon2 hash
password_needs_rehash()    reports whether an Argon2 hash should be refreshed
```

The password utility layer is intentionally narrow. It does not log plain-text
passwords, create users, implement registration, or expose API endpoints by
itself.

JWT token utilities live in `app/auth/tokens.py`.

```text
create_access_token()   signs an access token with sub, token_type, iat, exp
create_refresh_token()  signs a refresh token with sub, token_type, iat, exp
decode_token()          validates signature, expiration, and token type
verify_token()          returns a payload or None for invalid tokens
```

JWT settings are loaded from environment variables:

```text
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
```

The default JWT secret is for local development only. Production deployments
must provide a strong secret through environment configuration. The token
utility layer does not log tokens, create users, implement registration, or
expose API endpoints by itself.

Auth API routes are mounted under `/api/v1/auth`:

```text
POST /api/v1/auth/login    returns access and refresh tokens
POST /api/v1/auth/refresh  returns a new token pair from a refresh token
POST /api/v1/auth/logout   stateless MVP logout success response
GET  /api/v1/auth/me       returns the current safe user profile
```

The Auth API uses the existing `User` model, Argon2 password verification, JWT
token utilities, and request-scoped `AsyncSession` dependency. It does not log
plain-text passwords or tokens, and it does not return `hashed_password` in
responses. Logout is stateless for now; server-side token revocation can be
added later with Redis-backed storage.

RBAC dependency utilities live in `app/auth/rbac.py`.

```text
RoleName             supported role names: Admin, Manager, Sales, Legal, Finance, Viewer
get_user_role_names  returns case-sensitive role names assigned to a user
require_any_role     allows users with any listed role
require_all_roles    allows users with every listed role
require_admin        convenience dependency for Admin-only access
```

RBAC dependencies build on the existing current-user dependency. Missing or
invalid credentials return `401`; authenticated users without required roles
return `403`. Role comparison is case-sensitive. This layer does not implement
role assignment APIs, user management APIs, registration, permission tables, or
fine-grained permissions.

## Storage Interfaces

Cache provider interfaces live in `app/cache`.

```text
CacheProvider.get()     reads a string value by key
CacheProvider.set()     stores a string value with an optional TTL
CacheProvider.delete()  removes a key if present
CacheProvider.exists()  checks key presence
CacheProvider.expire()  applies or replaces a TTL
CacheProvider.close()   releases provider resources
```

The cache layer is interface-only at this stage. Redis client behavior,
distributed locks, queues, workflow state, Qdrant, MinIO, document indexing, and
RAG are deferred to later SPEC-004 tasks.

Redis-backed cache support lives in `app/cache/redis.py`.

```text
RedisCacheProvider.from_url()      creates a provider from a Redis URL
create_redis_cache_provider()      creates a provider from REDIS_URL settings
RedisCacheProvider.health_check()  verifies Redis responds to ping
```

`RedisCacheProvider` implements the `CacheProvider` contract with async Redis
operations for string values, optional TTL on `set`, `expire`, `exists`,
`delete`, and `close`. Redis operation failures are wrapped as cache operation
errors. The provider does not implement workflow state, distributed locks,
queues, or token blacklists.

Vector store provider interfaces live in `app/vectorstore`.

```text
VectorPoint                 vector id, float vector, and payload metadata
VectorSearchResult          result id, score, and payload metadata
VectorStore.create_collection()
VectorStore.collection_exists()
VectorStore.upsert()
VectorStore.search()
VectorStore.delete()
VectorStore.close()
```

The vector store layer is interface-only at this stage. Qdrant client behavior,
embeddings, document chunking, document indexing, RAG, hybrid search, Retrieval
Agent logic, LangGraph, agents, MinIO, and frontend work are deferred to later
tasks.

Qdrant-backed vector store support lives in `app/vectorstore/qdrant.py`.

```text
QdrantVectorStore.from_url()       creates a provider from a Qdrant URL
create_qdrant_vector_store()       creates a provider from QDRANT_URL settings
QdrantVectorStore.health_check()   verifies Qdrant responds
```

`QdrantVectorStore` implements the `VectorStore` contract with async operations
for collection creation, collection existence checks, point upsert, vector
search, point deletion, and client close. It uses cosine distance for created
collections and supports simple exact-match payload filters. Qdrant operation
failures are wrapped as vector store operation errors. The provider does not
implement embeddings, chunking, indexing, RAG, hybrid search, Retrieval Agent
logic, LangGraph, agents, MinIO, or frontend behavior.

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
