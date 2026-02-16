# EPIC 7 — Dashboard APIs

**Epic ID**: `epic-7-dashboard`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-16
**Priority**: P2 (Enhancement)
**Depends On**: EPIC 0, EPIC 1 (Authorization), EPIC 3, EPIC 4, EPIC 5, EPIC 6

## Goal

Provide aggregated metrics and dashboard data scoped by user role for SaaS operations visibility.

## Features

### F7.1 Global Dashboard (super_admin)

**Endpoint**: `GET /v1/dashboard`

**Authorization**: `super_admin` only

**Response**: `200 OK`
```json
{
  "totals": {
    "organizations": 10,
    "tenants": 45,
    "subscriptions": 120,
    "applications": 3
  },
  "subscriptions_by_status": {
    "trial": 25,
    "active": 80,
    "disabled": 15
  },
  "subscriptions_by_app": {
    "pacs": 50,
    "erp": 70
  },
  "trials_expiring_soon": 8,
  "recent_activity": {
    "organizations_created_7d": 2,
    "tenants_created_7d": 5,
    "subscriptions_created_7d": 12
  },
  "sync_status": {
    "synced": 40,
    "pending": 3,
    "failed": 2
  }
}
```

### F7.2 Organization Dashboard

**Endpoint**: `GET /v1/dashboard/organizations/{org_id}`

**Authorization**: super_admin (any), org_admin (own org), tenant_admin (own org)

### F7.3 Tenant Dashboard

**Endpoint**: `GET /v1/dashboard/tenants/{tenant_id}`

**Authorization**: super_admin (any), org_admin (org tenants), tenant_admin (own tenant)

### F7.4 Trial Report

**Endpoint**: `GET /v1/dashboard/trials`

**Authorization**: super_admin (all), org_admin (org trials), tenant_admin (own trials)

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `days` | int | Days threshold (default: 3, max: 14) |
| `org_id` | UUID | Filter by organization |

### F7.5 Sync Status Report

**Endpoint**: `GET /v1/dashboard/sync-status`

**Authorization**: `super_admin` only

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by sync_status: `pending`, `failed` |

## Requirements

| ID | Requirement |
|----|-------------|
| FR-7.1 | Dashboard data MUST be scoped by user role |
| FR-7.2 | Global dashboard MUST be super_admin only |
| FR-7.3 | Organization dashboard MUST be accessible to org members |
| FR-7.4 | Tenant dashboard MUST be accessible to tenant members |
| FR-7.5 | Trial report MUST respect role scoping |
| FR-7.6 | Sync status report MUST be super_admin only |
| FR-7.7 | All counts MUST exclude soft-deleted entities |
| FR-7.8 | `days_remaining` MUST be calculated accurately |

## Aggregation Rules

| Metric | Calculation |
|--------|-------------|
| `trials_expiring_soon` | Subscriptions where status=trial AND trial_ends_at within threshold days |
| `recent_activity.*_7d` | Entities created within last 7 days |
| `subscriptions_by_app` | Count grouped by app_key |
| `subscriptions_by_status` | Count grouped by status |
| `sync_status` | Count of tenants grouped by sync_status |

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `DASHBOARD_ACCESS_DENIED` | 403 | Cannot access dashboard for this resource |
| `ORG_NOT_FOUND` | 404 | Organization not found |
| `TENANT_NOT_FOUND` | 404 | Tenant not found |

## Acceptance Criteria

- [ ] Global dashboard returns all metrics (super_admin)
- [ ] Organization dashboard returns org-scoped metrics
- [ ] Tenant dashboard returns tenant-scoped metrics
- [ ] Trial report lists expiring trials with correct days_remaining
- [ ] Sync status report shows pending/failed tenants (super_admin)
- [ ] Role scoping enforced on all endpoints
- [ ] Soft-deleted entities excluded from counts
- [ ] Response time < 500ms for all dashboard endpoints

## Dependencies

- EPIC 0 (FastAPI skeleton)
- EPIC 1 (Authorization helpers)
- EPIC 3 (Applications)
- EPIC 4 (Organizations)
- EPIC 5 (Tenants)
- EPIC 6 (Subscriptions)

## Deliverables

- [ ] Dashboard endpoints operational
- [ ] Role-based scoping enforced
- [ ] Efficient aggregation queries
- [ ] Unit tests for all endpoints
- [ ] Integration tests with auth scenarios
