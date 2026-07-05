# PROJECT CONTRACT — Enterprise Multi-Agent OS

## Project Name

Enterprise Multi-Agent OS: Automated Business Workflow Orchestration

Academic title:

Enterprise Procurement Workflow Automation using LangGraph-based Multi-Agent System

## Mission

Build a production-oriented Multi-Agent Operating System for enterprise workflows. The MVP focuses on procurement and quotation automation, but the architecture must support multiple business domains such as IT procurement, office furniture, facility maintenance, software subscriptions, and logistics equipment.

## Immutable Architecture

The system is built around:

- NextJS Dashboard
- FastAPI Backend
- LangGraph Workflow Engine
- Specialized AI Agents
- PostgreSQL for business data
- Redis for runtime state and cache
- Qdrant for vector search
- MinIO-compatible object storage for files
- Multi-provider LLM abstraction

Codex must not redesign this architecture.

## Core Product Principle

This is not a chatbot. It is a state-driven workflow orchestration system where AI Agents operate as specialized workers inside a controlled business process.

## Mandatory Engineering Rules

1. Never change the approved architecture.
2. Never introduce new frameworks without a SPEC.
3. Never implement outside the current SPEC or task.
4. Every Agent must have one responsibility.
5. Every Agent output must use Pydantic structured schemas.
6. Calculator must not use LLMs for arithmetic.
7. Retrieval must return citations and metadata.
8. Validation must review structured state, not hidden reasoning.
9. Approval must be required before customer-facing email output is finalized.
10. Files must not be stored in PostgreSQL.
11. Secrets must never be hardcoded.
12. Tests and documentation are required for every implementation task.

## Supported LLM Providers

The system must support pluggable providers:

- Groq
- OpenRouter
- Ollama
- Gemini

Provider-specific logic must stay behind an LLMProvider interface.

## Language

The product UI, API names, documentation, demo data, and generated email outputs must be in English.

## MVP Workflow

Request -> Planner -> Retrieval -> Calculator -> Compliance -> Validation -> Human Approval -> Email Preview -> Completed

## Definition of Done

A task is complete only when:

- Code compiles
- Tests pass
- Ruff passes
- MyPy passes where applicable
- Docker build succeeds where applicable
- Documentation is updated
- API schemas are documented
- No architecture rule is violated
