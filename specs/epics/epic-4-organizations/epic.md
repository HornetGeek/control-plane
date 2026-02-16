# EPIC 4 — Organizations Management

**Epic ID**: `epic-4-organizations`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-16
**Priority**: P1 (Core)
**Depends On**: EPIC 0, EPIC 2 (Organization entity), EPIC 1 (Authorization)

## Goal

Implement CRUD operations for organizations with role-based access control.

## Features

### F4.1 List Organizations

**Endpoint**: `GET /v1/organizations`

**Authorization**: super_admin (all), org_admin (own org), tenant_admin (own org)

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status: `active`, `disabled` |
| `include_deleted` | boolean | Include soft-deleted (super_admin only) |
| `search` | string | Search by name (case-insensitive) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Acme Corp",
      "status": "active",
      "tenant_count": 5,
      "created_at": "2026-02-16T10:00:00Z",
      "updated_at": "2026-02-16T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Scoping**:
- `super_admin`: All organizations
- `org_admin`, `tenant_admin`: Only their assigned organization

### F4.2 Get Organization

**Endpoint**: `GET /v1/organizations/{org_id}`

**Authorization**: super_admin (any), org_admin/tenant_admin (own org only)

### F4.3 Create Organization

**Endpoint**: `POST /v1/organizations`

**Authorization**: `super_admin` only

**Request Body**:
```json
{
  "name": "Acme Corp"
}
```

**Side Effects**:
- Syncs organization to mock Core

### F4.4 Update Organization

**Endpoint**: `PATCH /v1/organizations/{org_id}`

**Authorization**: super_admin (any), org_admin (own org only)

### F4.5 Delete Organization

**Endpoint**: `DELETE /v1/organizations/{org_id}`

**Authorization**: `super_admin` only

**Preconditions**:
- Organization must have no active tenants

### F4.6 Restore Organization

**Endpoint**: `POST /v1/organizations/{org_id}/restore`

**Authorization**: `super_admin` only

## Requirements

| ID | Requirement |
|----|-------------|
| FR-4.1 | Organization name MUST be unique |
| FR-4.2 | org_admin can only update their own organization |
| FR-4.3 | tenant_admin cannot update organizations |
| FR-4.4 | Delete MUST be soft (set deleted_at) |
| FR-4.5 | Organizations with active tenants MUST NOT be deletable |
| FR-4.6 | List MUST be scoped by user role |
| FR-4.7 | Creation MUST trigger Core sync (stubbed for MVP) |

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `ORG_NOT_FOUND` | 404 | Organization not found |
| `ORG_NAME_EXISTS` | 409 | Organization name already in use |
| `ORG_HAS_TENANTS` | 409 | Cannot delete org with active tenants |
| `ORG_ACCESS_DENIED` | 403 | Cannot access this organization |

## Acceptance Criteria

- [ ] List returns scoped organizations based on role
- [ ] Get returns single organization (if authorized)
- [ ] Create succeeds with valid data (super_admin)
- [ ] Create fails with duplicate name
- [ ] Update succeeds (super_admin or org_admin for own org)
- [ ] Update fails for tenant_admin
- [ ] Delete soft-deletes organization (super_admin)
- [ ] Delete fails if active tenants exist
- [ ] Restore recovers soft-deleted organization (super_admin)
- [ ] tenant_count included in responses

## Dependencies

- EPIC 0 (FastAPI skeleton)
- EPIC 1 (Authorization helpers)
- EPIC 2 (Organization entity + migrations)

## Deliverables

- [ ] Organization CRUD endpoints operational
- [ ] Role-based scoping enforced
- [ ] Unit tests for all endpoints
- [ ] Integration tests with auth scenarios
