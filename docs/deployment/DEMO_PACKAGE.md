# Board Demo Package

This checklist packages the current Enterprise Multi-Agent OS demo for a board
or stakeholder walkthrough.

## Package Goal

Show a deterministic procurement workflow that can:

- load a dashboard and workflow detail
- run to `WAITING_APPROVAL`
- optionally show RAG evidence and knowledge search
- submit human approval
- resume post-approval continuation
- finish at `COMPLETED`
- show persisted timeline, approval, resume, and grounding events
- expose safe operational health and metrics

## Pre-Demo Package Checklist

1. Choose no-key default or optional RAG evidence mode.
2. Prepare `.env.production.local` from `docs/deployment/.env.production.example`.
3. Replace placeholder secrets.
4. Validate Compose:

   ```bash
   bash scripts/ci/compose-gate.sh
   ```

5. Build production-demo app images:

   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.production.local build backend frontend
   ```

6. Start the stack:

   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.production.local up -d
   ```

7. Run migrations explicitly.
8. Run demo seed explicitly.
9. If showing evidence, run knowledge ingestion explicitly and ensure
   `RAG_ENABLED=true` for the backend runtime.
10. Run smoke checks:

    ```bash
    COMPOSE_ENV_FILE=.env.production.local bash scripts/deployment/smoke-prod-demo.sh --include-ready
    ```

11. Open the frontend and verify Manager/Admin login.

## Recommended Demo Flow

1. Login as Manager/Admin.
2. Open workflow dashboard.
3. Open the clean procurement workflow.
4. Run workflow to `WAITING_APPROVAL`.
5. Show event timeline.
6. If RAG is enabled:
   - show evidence/citations panel
   - show knowledge search results
   - show document catalog
   - point out grounding events
7. Show approval panel and empty/populated approval history.
8. Approve with a short comment.
9. Show workflow moves to `APPROVED`.
10. Click explicit Resume.
11. Show workflow reaches `COMPLETED`.
12. Show final timeline.
13. Optional: login as Viewer and show approval/resume is forbidden.
14. Optional: show Admin/Manager metrics endpoint.

## Demo Talking Points

- Default mode is deterministic and no-key.
- Real LLM providers are optional and behind feature flags.
- RAG evidence uses fake embeddings by default and local Qdrant/MinIO.
- Approval/resume is explicit and audited.
- Readiness checks dependencies but does not mutate state.
- CI gates validate backend, frontend, Compose, dry-run seed, and dry-run
  knowledge ingestion.

## Do Not Claim

Do not claim these are implemented:

- production secret vault
- enterprise SSO
- cloud deployment automation
- Kubernetes/Terraform
- zero-downtime deployment
- production-grade backups
- production email sending
- upload/admin document-management UI
- production OCR
- external document connectors
- external telemetry vendor
- token streaming or agent-thought streaming

## Evidence To Capture

For a board demo recording or handoff:

- `docker-compose ... ps`
- smoke script result
- workflow dashboard screenshot
- `WAITING_APPROVAL` detail screenshot
- evidence panel screenshot when RAG is enabled
- approval history screenshot
- `COMPLETED` timeline screenshot
- screenshot checklist reference: `docs/final/SCREENSHOT_CHECKLIST.md`
- architecture diagram source reference: `docs/report/diagrams/README.md`
- note the git commit or image tag used
