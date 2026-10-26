# Breaking migration boundary

Version 0.2 is a new headless product schema. The procurement_quotation state,
business roles, frontend, demo catalogs/accounts, RAG/vector/object services,
pricing, outbound preview and Telegram contracts are removed. There are no hidden
compatibility endpoints or automatic old-data conversion.

Preserve old volumes, databases and secrets. Do not point headless migration at
an old or unknown nonempty database. Migrations require a new empty database or a
recognized headless instance marker and migration lineage. Refusal must happen
before DDL. No existing business data is deleted by this release.

To inspect legacy runs, check out baseline
`92e5f1cfb2b0144bdb39a48db99371974bd372a5` in a separate directory and run its
original stack with isolated names/configuration. Never attach a legacy database
to the headless service. Historical documentation remains in that Git revision.

Headless backups include run inputs/outputs, jobs, node attempts, approvals,
ordered events, users/roles, hashed refresh sessions and idempotency records.
Follow the separate-instance [backup/restore procedure](self-hosting.md). Keep
secrets and exact trusted extension source artifacts separately. Verify pending
approvals and completed outputs after restoration, not just table counts.
