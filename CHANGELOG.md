# Changelog

## v0.1.0 — Initial Multi-Agent OS Source Preview

First early public source snapshot of the generic headless Multi-Agent OS.
FastAPI/LangGraph runtime, PostgreSQL/Redis durability, real provider integrations,
API/CLI operations and explicit approval/resume replace the retired procurement
and graduation-demo stack. SPEC-029 is 32 PASS / 0 BLOCKED with recorded direct
Groq chained workflow evidence; Cloudflare is offline-tested only.

Source-only pre-release: no prebuilt Docker image or production-security approval.
Known unresolved OS vulnerabilities and the image NO-GO remain disclosed in
SECURITY.md and SPEC-030 signoff. The internal CLI/package version remains 0.2.0;
this tag identifies the source-publication milestone.

## 0.2.0 — headless extraction (implementation version)

Breaking pre-1.0 API/schema release: generic typed sequential workflows, durable
PostgreSQL-backed worker execution, explicit human approvals and resume, event
replay, operator CLI and clean administrator bootstrap.

Removed the Next.js frontend, seeded accounts and business/demo data,
procurement/quotation pipeline, RAG/embedding/Qdrant/MinIO, pricing and outbound
preview/Telegram features, fake selectable providers, and obsolete development
Harness/template packaging. Legacy volumes/data are not migrated or deleted.

One backend release image provides API, worker, CLI and guarded migrations.
English onboarding/operator documentation replaces the graduation demo guide.
MIT is selected for maintainer-owned project material; dependency notices remain
applicable. See docs/release/verification.md for verification and release gates.
