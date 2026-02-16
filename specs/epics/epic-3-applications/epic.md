# EPIC 3 — Applications Catalog

**Epic ID**: `epic-3-applications`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-16
**Priority**: P1 (Core)
**Depends On**: EPIC 0, EPIC 2 (Application entity), EPIC 1 (Authorization)

## Goal

Implement CRUD operations for the application catalog with super_admin-only management.

## Features

### F3.1 List Applications

**Endpoint**: `GET /v1/applications`

**Authorization**: Any CP role (super_admin, org_admin, tenant_admin)

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status: `active`, `disabled` |
| `include_deleted` | boolean | Include soft-deleted apps (super_admin only) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "app_key": "pacs",
      "name": "PACS Service",
      "base_url": "https://pacs.example.com",
      "status": "active",
      "created_at": "2026-02-16T10:00:00Z",
      "updated_at": "2026-02-16T10:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

### F3.2 Get Application

**Endpoint**: `GET /v1/applications/{app_id_or_key}`

**Authorization**: Any CP role

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `app_id_or_key` | string | Application UUID or app_key |

**Response**: `200 OK`

### F3.3 Create Application

**Endpoint**: `POST /v1/applications`

**Authorization**: `super_admin` only

**Request Body**:
```json
{
  "app_key": "pacs",
  "name": "PACS Service",
  "base_url": "https://pacs.example.com"
}
```

**Response**: `201 Created`

### F3.4 Update Application

**Endpoint**: `PATCH /v1/applications/{app_id}`

**Authorization**: `super_admin` only

### F3.5 Delete Application

**Endpoint**: `DELETE /v1/applications/{app_id}`

**Authorization**: `super_admin` only

**Response**: `204 No Content`

### F3.6 Restore Application

**Endpoint**: `POST /v1/applications/{app_id}/restore`

**Authorization**: `super_admin` only

## Requirements

| ID | Requirement |
|----|-------------|
| FR-3.1 | app_key MUST be unique and match `^[a-z][a-z0-9_]*$` |
| FR-3.2 | base_url MUST be a valid HTTPS URL |
| FR-3.3 | Only super_admin can create/update/delete applications |
| FR-3.4 | Delete MUST be soft (set deleted_at) |
| FR-3.5 | List MUST exclude soft-deleted by default |
| FR-3.6 | Applications with active subscriptions MUST NOT be deletable |

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `APP_NOT_FOUND` | 404 | Application not found |
| `APP_KEY_EXISTS` | 409 | app_key already in use |
| `APP_HAS_SUBSCRIPTIONS` | 409 | Cannot delete app with active subscriptions |
| `INVALID_APP_KEY` | 400 | app_key format invalid |
| `INVALID_BASE_URL` | 400 | base_url is not a valid HTTPS URL |

## Acceptance Criteria

- [ ] List returns active applications with pagination
- [ ] Get by ID returns single application
- [ ] Get by app_key returns single application
- [ ] Create succeeds with valid data (super_admin)
- [ ] Create fails with duplicate app_key
- [ ] Update succeeds with partial data (super_admin)
- [ ] Delete soft-deletes application (super_admin)
- [ ] Delete fails if active subscriptions exist
- [ ] Restore recovers soft-deleted application (super_admin)
- [ ] Non-super_admin receives 403 for CUD operations

## Dependencies

- EPIC 0 (FastAPI skeleton)
- EPIC 1 (Authorization helpers)
- EPIC 2 (Application entity + migrations)

## Deliverables

- [ ] Application CRUD endpoints operational
- [ ] Unit tests for all endpoints
- [ ] Integration tests with auth scenarios
