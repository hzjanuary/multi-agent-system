# API CONTRACT

## Response Envelope

Successful response:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "string"
}
```

Error response:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  },
  "request_id": "string"
}
```

## Auth API

- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

## Workflow API

- POST /api/v1/workflows
- GET /api/v1/workflows
- GET /api/v1/workflows/{workflow_id}
- POST /api/v1/workflows/{workflow_id}/run
- POST /api/v1/workflows/{workflow_id}/resume
- POST /api/v1/workflows/{workflow_id}/cancel

## Approval API

- GET /api/v1/approvals/pending
- POST /api/v1/approvals/{workflow_id}/approve
- POST /api/v1/approvals/{workflow_id}/reject

## Events API

- GET /api/v1/workflows/{workflow_id}/events
- GET /api/v1/workflows/{workflow_id}/state
- WS /api/v1/workflows/{workflow_id}/stream
