# DATABASE CONTRACT

## Phase 1 Tables

- users
- roles
- user_roles
- workflows
- workflow_events
- audit_logs

## Later Tables

- customers
- products
- pricing_rules
- contracts
- policies
- documents
- approvals
- generated_files

## Naming

- Tables: snake_case plural
- Columns: snake_case
- Primary keys: id UUID
- Timestamps: created_at, updated_at
- Soft delete where needed: deleted_at

## Relationships

Role many-to-many User.  
Workflow one-to-many WorkflowEvent.  
Workflow one-to-many AuditLog.  
Workflow one-to-many Approval later.
