# SPEC v0.2 — Enterprise Multi-Agent OS

## Product Identity

Enterprise Multi-Agent OS is a distributed multi-agent operating system for automated business workflow orchestration.

Academic title:

Enterprise Procurement Workflow Automation using LangGraph-based Multi-Agent System

## Scope

The platform starts with procurement automation, but the core architecture supports multiple business workflows.

## MVP Domains

- IT equipment procurement
- Office furniture procurement
- Facility maintenance procurement
- Software subscription procurement
- Logistics and warehouse equipment procurement

## Primary Demo

A user submits a procurement request. The system plans the workflow, retrieves relevant contracts and policies, calculates a quotation, checks compliance, validates outputs, waits for manager approval and generates an email preview.

## Language

English only for UI, API, documentation and demo data.

## LLM Providers

Provider abstraction must support Groq, OpenRouter, Ollama and Gemini.

## Email

MVP generates preview only. It does not send email automatically.

## Quote Output

MVP generates JSON and Excel-compatible tabular data.
