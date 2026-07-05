# SPEC-004 — Storage Infrastructure

## Goal

Prepare cache, vector store and object storage abstractions.

## In Scope

- Redis client abstraction
- Qdrant client abstraction
- MinIO storage abstraction
- Health checks for external services
- Tests with mocks

## Out of Scope

- Document indexing
- RAG retrieval
- Agent implementation

## Interfaces

- CacheProvider
- VectorStore
- ObjectStorageProvider

## Acceptance Criteria

- Redis connection check works
- Qdrant connection check works
- MinIO upload/download abstraction works
- Tests use mocks or local containers
