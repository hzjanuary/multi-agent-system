# Graduation Report Assets

This folder contains English Markdown source material for the Enterprise
Multi-Agent OS graduation report. The files are report-ready narrative assets,
not the final thesis document and not captured evaluation evidence.

## Files

- `REPORT_OUTLINE.md` defines the proposed report structure.
- `TECHNICAL_NARRATIVE.md` explains the project problem, objectives, and major
  technical choices in reusable prose.
- `IMPLEMENTATION_PHASES.md` maps SPEC-001 through SPEC-014 to report-friendly
  implementation phases.
- `ARCHITECTURE_AND_DESIGN.md` describes the architecture in text form only.
  Diagrams are deferred to TASK 015.4.
- `EVALUATION_NARRATIVE.md` provides evaluation-methodology prose and
  placeholders linked to final evidence plans.
- `LIMITATIONS_AND_FUTURE_WORK.md` records honest limitations and deferred
  future work.
- `APPENDIX_GUIDE.md` lists appendix material and source references for setup,
  APIs, scripts, evidence, screenshots, and demo materials.
- `diagrams/` contains maintainable Mermaid diagram source files for system
  context, deployment, backend layers, workflow runtime, approval/resume, RAG,
  event streaming, and CI/deployment flow.

## Boundaries

These assets must not claim uncollected final evidence, invented metrics,
coverage percentages, benchmark results, user study results, production cloud
deployment, or real LLM-provider evaluation. They must not include real secrets,
tokens, raw prompts, raw provider payloads, raw embeddings, raw vector payloads,
chain-of-thought, or real customer data.

Final evaluation evidence should be captured through `docs/final/` after the
matching validation run is performed.

Screenshot capture planning lives in `docs/final/SCREENSHOT_CHECKLIST.md`.
