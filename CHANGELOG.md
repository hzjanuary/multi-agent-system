# Changelog

## 0.2.0 — headless extraction (unreleased)

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
