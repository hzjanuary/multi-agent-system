# SPEC-002 — Database Foundation

## Goal

Implement PostgreSQL persistence foundation using SQLAlchemy 2 async and Alembic.

## In Scope

- Async database engine/session
- Alembic configuration
- Base model
- User
- Role
- Workflow
- WorkflowEvent
- AuditLog
- Generic repository pattern
- Migration tests

## Out of Scope

- Auth API
- Customers
- Contracts
- Products
- Agents

## Acceptance Criteria

- alembic upgrade head creates tables
- repositories have tests
- models use UUID primary keys
- timestamps are included
