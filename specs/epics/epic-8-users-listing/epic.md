# EPIC 8 — Users Listing (via Mock Core)

**Epic ID**: `epic-8-users-listing`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-16
**Priority**: P2 (Enhancement)
**Depends On**: EPIC 0, EPIC 1 (Authorization, Mock Core), EPIC 4, EPIC 5

## Goal

Provide user listing functionality by delegating to mock Core service with proper scoping.

## Features

### F8.1 List Users (Global)

**Endpoint**: `GET /v1/users`

**Authorization**: `super_admin` only

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Search by email or name |
| `role` | string | Filter by role: `super_admin`, `org_admin`, `tenant_admin`, `tenant_member` |
| `org_id` | UUID | Filter by organization |
| `tenant_id` | UUID | Filter by tenant |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "admin@example.com",
      "name": "Admin User",
      "effective_role": "org_admin",
      "org_id": "uuid",
      "org_name": "Acme Corp",
      "tenant_ids": ["uuid-1", "uuid-2"],
      "last_login_at": "2026-02-15T10:00:00Z",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

**MVP Note**: Data comes from mock Core client, not a real service.

### F8.2 List Users by Organization

**Endpoint**: `GET /v1/organizations/{org_id}/users`

**Authorization**: super_admin (any), org_admin (own org), tenant_admin (own org)

**Scoping**:
- `super_admin`: All users in org
- `org_admin`: All users in org
- `tenant_admin`: Only users in their tenant(s)

### F8.3 List Users by Tenant

**Endpoint**: `GET /v1/tenants/{tenant_id}/users`

**Authorization**: super_admin (any), org_admin (org tenants), tenant_admin (own tenant)

### F8.4 Get Current User

**Endpoint**: `GET /v1/users/me`

**Authorization**: Any authenticated user

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "Current User",
  "effective_role": "org_admin",
  "org_id": "uuid",
  "org_name": "Acme Corp",
  "tenant_ids": ["uuid-1", "uuid-2"],
  "tenants": [
    {"id": "uuid-1", "name": "Headquarters"},
    {"id": "uuid-2", "name": "Branch Office"}
  ],
  "permissions": ["org:read", "org:write", "tenant:read"],
  "last_login_at": "2026-02-15T10:00:00Z",
  "created_at": "2026-01-01T00:00:00Z"
}
```

## Mock Core Client

The mock Core client returns predictable user data based on configured scenarios.

**Configuration**:
```python
MOCK_USERS = [
    {
        "id": "super-admin-uuid",
        "email": "super@example.com",
        "name": "Super Admin",
        "effective_role": "super_admin",
        "org_id": None,
        "tenant_ids": [],
    },
    {
        "id": "org-admin-uuid",
        "email": "orgadmin@acme.com",
        "name": "Org Admin",
        "effective_role": "org_admin",
        "org_id": "acme-org-uuid",
        "tenant_ids": ["tenant-1", "tenant-2"],
    },
    # ... more users
]
```

## Requirements

| ID | Requirement |
|----|-------------|
| FR-8.1 | User data MUST come from mock Core client |
| FR-8.2 | Global user listing MUST be super_admin only |
| FR-8.3 | Org user listing MUST be scoped to org members |
| FR-8.4 | Tenant user listing MUST be scoped to tenant members |
| FR-8.5 | tenant_admin can only see users in their tenant(s) |
| FR-8.6 | Search MUST be case-insensitive |
| FR-8.7 | Results MUST be paginated |
| FR-8.8 | `/users/me` MUST return current authenticated user |

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `USER_NOT_FOUND` | 404 | User not found |
| `USERS_ACCESS_DENIED` | 403 | Cannot list users for this scope |
| `CORE_UNAVAILABLE` | 503 | Core service unavailable |

## Acceptance Criteria

- [ ] Global user list returns all mock users (super_admin)
- [ ] Org user list returns org-scoped users
- [ ] Tenant user list returns tenant-scoped users
- [ ] Role filtering works correctly
- [ ] Search filters by email and name
- [ ] Pagination works correctly
- [ ] `/users/me` returns current user profile
- [ ] Role scoping enforced on all endpoints
- [ ] Mock Core client returns predictable data
- [ ] Error handling for Core unavailability

## Dependencies

- EPIC 0 (FastAPI skeleton)
- EPIC 1 (Authorization, Mock Core client)
- EPIC 4 (Organizations - for org context)
- EPIC 5 (Tenants - for tenant context)

## Deliverables

- [ ] User listing endpoints operational
- [ ] Mock Core client with predictable scenarios
- [ ] Role-based scoping enforced
- [ ] Unit tests for all endpoints
- [ ] Integration tests with auth scenarios
