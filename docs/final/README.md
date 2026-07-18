# Final Evaluation Planning

This folder is the SPEC-015 evaluation planning area for Enterprise
Multi-Agent OS. It defines how the final graduation evidence will be measured,
captured, and traced back to the implemented SPEC-001 through SPEC-014 product
surface.

These files are planning and evidence templates only. They do not contain final
screenshots, diagrams, slides, thesis chapters, or completed evaluation
results yet.

## Files

- `EVALUATION_MATRIX.md` maps final evaluation dimensions to implemented
  specs, measurable acceptance criteria, automated proof, manual demo proof,
  expected artifacts, and known risks.
- `ACCEPTANCE_EVIDENCE_PLAN.md` defines the command output, manual walkthrough,
  safety, and no-secret evidence to capture in later SPEC-015 tasks.
- `EVALUATION_REPORT_TEMPLATE.md` is a placeholder structure for the later
  final evaluation report. It must be filled only after evidence is actually
  collected.
- `E2E_DEMO_VALIDATION.md` defines the repeatable end-to-end board-demo
  validation script, manual checklist, expected outcomes, troubleshooting
  notes, and evidence capture checklist.
- `E2E_EVIDENCE_CAPTURE_TEMPLATE.md` is a placeholder-only note template for a
  future E2E validation run.
- `SCREENSHOT_CHECKLIST.md` defines final screenshot naming, storage,
  redaction, capture-status placeholders, and evaluation-dimension mapping.

## Evaluation Modes

The default final evaluation mode is deterministic and no-key:

```text
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
EMBEDDING_PROVIDER=fake
RAG_ENABLED=false
```

Optional RAG evidence can be evaluated without real LLM keys:

```text
RAG_ENABLED=true
EMBEDDING_PROVIDER=fake
LLM_PROVIDER=fake
LLM_RUNTIME_ENABLED=false
```

The optional RAG path also requires explicit knowledge ingestion before the
workflow run:

```bash
docker-compose run --rm backend-test python -m app.knowledge.ingest_demo --confirm-local-demo
```

## Evidence Boundaries

Final evidence must not include real secrets, API keys, tokens, raw provider
payloads, raw prompts, raw embeddings, raw vector payloads, full unbounded
documents, real customer data, or chain-of-thought.

Use existing runbooks and gates as source material:

- `docs/demo/DEMO_RUNBOOK.md`
- `docs/demo/FRONTEND_SMOKE_FLOW.md`
- `docs/deployment/RUNBOOK.md`
- `docs/deployment/DEMO_PACKAGE.md`
- `docs/deployment/SMOKE_CHECKS.md`
- `scripts/ci/all-gates.sh`
- `scripts/deployment/smoke-prod-demo.sh`
- `scripts/final/e2e-demo-validation.sh`

Graduation report narrative assets live in:

- `docs/report/README.md`
- `docs/report/REPORT_OUTLINE.md`
- `docs/report/TECHNICAL_NARRATIVE.md`
- `docs/report/IMPLEMENTATION_PHASES.md`
- `docs/report/ARCHITECTURE_AND_DESIGN.md`
- `docs/report/EVALUATION_NARRATIVE.md`
- `docs/report/LIMITATIONS_AND_FUTURE_WORK.md`
- `docs/report/APPENDIX_GUIDE.md`
- `docs/report/diagrams/README.md`
