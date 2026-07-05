# STATE CONTRACT

## WorkflowState

```json
{
  "workflow_id": "string",
  "workflow_type": "procurement_quotation",
  "domain": "it_equipment",
  "status": "CREATED",
  "request": {},
  "customer": {},
  "items": [],
  "planner": {},
  "retrieval": {},
  "quotation": {},
  "compliance": {},
  "validation": {},
  "approval": {},
  "email": {},
  "retry_count": 0,
  "events": [],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Workflow Status

- CREATED
- PLANNING
- RETRIEVING
- CALCULATING
- CHECKING_COMPLIANCE
- VALIDATING
- WAITING_APPROVAL
- APPROVED
- REJECTED
- GENERATING_EMAIL
- COMPLETED
- FAILED
- CANCELLED

## Event Model

Each event must include:

- event_id
- workflow_id
- event_type
- actor_type
- actor_id
- agent_name
- status
- message
- payload
- created_at
