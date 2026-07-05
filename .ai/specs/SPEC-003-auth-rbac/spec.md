# SPEC-003 — Authentication and RBAC

## Goal

Implement JWT authentication, refresh token flow and role-based access control.

## In Scope

- Argon2 password hashing
- Login
- Refresh
- Logout
- Current user endpoint
- RBAC dependencies
- Roles: Admin, Manager, Sales, Legal, Finance, Viewer

## Out of Scope

- OAuth
- SSO
- MFA

## Acceptance Criteria

- User can log in
- Access token protects endpoints
- Refresh token works
- RBAC blocks unauthorized role
- Tests cover auth flow
