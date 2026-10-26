# Multi-Agent OS backend

Python 3.12, FastAPI, LangGraph, SQLAlchemy/Alembic, PostgreSQL and Redis.

Follow the root [README](../README.md) for the canonical release-image install.
See [CONTRIBUTING](../CONTRIBUTING.md) for development checks,
[architecture](../docs/architecture.md) for transaction ownership, and
[extending](../docs/extending.md) for trusted typed workflows.

Entrypoints: `app.main:app`, `python -m app.worker`, `python -m app.cli`.
No frontend or Node.js is required. The dev image includes tests; runtime excludes
them. Real-provider verification is distinct from injected provider fixtures.
