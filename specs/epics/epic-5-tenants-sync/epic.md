# EPIC 5 — Tenants Management + Sync

**Epic ID**: `epic-5-tenants-sync`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-16
**Priority**: P1 (Core)
**Depends On**: EPIC 0, EPIC 2 (Tenant entity), EPIC 1 (Authorization), EPIC 3, EPIC 4

## Goal

Implement CRUD operations for tenants with Core synchronization and unique name enforcement per organization.

## Features

### F5.1 List Tenants

**Endpoint**: `GET /v1/tenants`

**Authorization**: super_admin (all), org_admin (org tenants), tenant_admin (own tenant)

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `org_id` | UUID | Filter by organization |
| `status` | string | Filter by status: `active`, `disabled` |
| `sync_status` | string | Filter by sync_status: `synced`, `pending`, `failed` |
| `include_deleted` | boolean | Include soft-deleted (super_admin only) |
| `search` | string | Search by name (case-insensitive) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Scoping**:
- `super_admin`: All tenants (can filter by org_id)
- `org_admin`: Tenants in their organization only
- `tenant_admin`: Only their assigned tenant

### F5.2 Get Tenant

**Endpoint**: `GET /v1/tenants/{tenant_id}`

**Authorization**: super_admin (any), org_admin/tenant_admin (accessible tenants only)

### F5.3 Create Tenant

**Endpoint**: `POST /v1/tenants`

**Authorization**: super_admin (any org), org_admin (own org only)

**Request Body**:
```json
{
  "org_id": "uuid",
  "name": "Headquarters"
}
```

**Validation**:
- Tenant name must be unique within organization (case-insensitive)
- `name_normalized` auto-generated as lowercase

### F5.4 Update Tenant

**Endpoint**: `PATCH /v1/tenants/{tenant_id}`

**Authorization**: super_admin (any), org_admin (org tenants), tenant_admin (own tenant - limited)

**Role Restrictions**:
- `tenant_admin`: Can only update name, not status

### F5.5 Delete Tenant

**Endpoint**: `DELETE /v1/tenants/{tenant_id}`

**Authorization**: super_admin (any), org_admin (org tenants)

**Preconditions**:
- All subscriptions must be disabled or deleted

### F5.6 Restore Tenant

**Endpoint**: `POST /v1/tenants/{tenant_id}/restore`

**Authorization**: `super_admin` only

### F5.7 Sync Tenant with Core

**Endpoint**: `POST /v1/tenants/{tenant_id}/sync`

**Authorization**: super_admin (any), org_admin (org tenants)

**MVP Note**: This is a stub that sets `sync_status` to `synced` and logs the action.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-5.1 | Tenant name MUST be unique per organization (case-insensitive) |
| FR-5.2 | `name_normalized` MUST be auto-generated as lowercase |
| FR-5.3 | Creation MUST set `sync_status` to `pending` |
| FR-5.4 | tenant_admin can only update their own tenant name |
| FR-5.5 | Delete MUST be soft (set deleted_at) |
| FR-5.6 | Tenants with active subscriptions MUST NOT be deletable |
| FR-5.7 | List MUST be scoped by user role |
| FR-5.8 | sync_status MUST reflect sync state |

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `TENANT_NOT_FOUND` | 404 | Tenant not found |
| `TENANT_NAME_EXISTS` | 409 | Tenant name already exists in this org |
| `TENANT_HAS_SUBSCRIPTIONS` | 409 | Cannot delete tenant with active subscriptions |
| `TENANT_ACCESS_DENIED` | 403 | Cannot access this tenant |
| `INVALID_ORG_ID` | 400 | Organization does not exist |

## Acceptance Criteria

- [ ] List returns scoped tenants based on role
- [ ] Get returns single tenant (if authorized)
- [ ] Create succeeds with unique name in org
- [ ] Create fails with duplicate name (same org, case-insensitive)
- [ ] Update succeeds based on role permissions
- [ ] Delete soft-deletes tenant
- [ ] Delete fails if active subscriptions exist
- [ ] Restore recovers soft-deleted tenant (super_admin)
- [ ] Sync endpoint sets sync_status to synced
- [ ] subscription_count included in responses

## Dependencies

- EPIC 0 (FastAPI skeleton)
- EPIC 1 (Authorization helpers)
- EPIC 2 (Tenant entity + migrations)
- EPIC 3 (Applications - for subscription validation)
- EPIC 4 (Organizations - for org scoping)

## Deliverables

- [ ] Tenant CRUD endpoints operational
- [ ] Role-based scoping enforced
- [ ] Unique name validation per org
- [ ] Core sync stub operational
- [ ] Unit tests for all endpoints
- [ ] Integration tests with auth scenarios
