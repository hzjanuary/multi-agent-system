# CODING STANDARD

## General

- Use strong typing.
- Prefer async I/O.
- Use dependency injection.
- Avoid hidden global state.
- Prefer explicit schemas over dictionaries.
- Every public function must have type hints.
- Every service must be testable without external services.

## Backend Layers

API -> Service -> Repository/Tool -> External System

API must never call repositories directly.

## Pydantic

Use Pydantic v2 models for:

- API request/response
- Agent input/output
- Workflow state
- Tool input/output
- Configuration

## SQLAlchemy

Use SQLAlchemy 2.0 async style.

## Logging

Use structlog JSON logging. Include request_id, workflow_id, agent_name and event_type when available.

## Error Handling

Use typed custom exceptions and map them to API responses through exception handlers.

## Tests

- Unit tests for services, repositories and tools
- Integration tests for API
- Mock external services
- Mock LLM providers
