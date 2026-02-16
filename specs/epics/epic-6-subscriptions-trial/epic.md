# EPIC 6 — Subscriptions + 14-Day Trial

**Epic ID**: `epic-6-subscriptions-trial`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-16
**Priority**: P1 (Core)
**Depends On**: EPIC 0, EPIC 2 (Subscription entity), EPIC 1 (Authorization), EPIC 3, EPIC 5

## Goal

Implement CRUD operations for subscriptions with automatic 14-day trial creation and status transitions.

## Features

### F6.1 List Subscriptions

**Endpoint**: `GET /v1/subscriptions`

**Authorization**: super_admin (all), org_admin (org subscriptions), tenant_admin (own tenant subscriptions)

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |
| `app_id` | UUID | Filter by application |
| `status` | string | Filter by status: `trial`, `active`, `disabled` |
| `trial_expiring` | boolean | Only subscriptions expiring within 3 days |
| `include_deleted` | boolean | Include soft-deleted (super_admin only) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Scoping**:
- `super_admin`: All subscriptions
- `org_admin`: Subscriptions for tenants in their organization
- `tenant_admin`: Subscriptions for their tenant only

### F6.2 Get Subscription

**Endpoint**: `GET /v1/subscriptions/{subscription_id}`

**Authorization**: super_admin (any), org_admin/tenant_admin (accessible only)

### F6.3 Create Subscription (Trial)

**Endpoint**: `POST /v1/subscriptions`

**Authorization**: super_admin (any), org_admin (org tenants), tenant_admin (own tenant)

**Business Logic**:
- `status` defaults to `trial`
- `trial_ends_at` auto-set to `now + TRIAL_DURATION_DAYS` (default: 14)
- One subscription per tenant+app combination

### F6.4 Activate Subscription

**Endpoint**: `POST /v1/subscriptions/{subscription_id}/activate`

**Authorization**: super_admin (any), org_admin (org subscriptions)

**MVP Note**: No actual payment integration. This is a manual status change.

### F6.5 Disable Subscription

**Endpoint**: `POST /v1/subscriptions/{subscription_id}/disable`

**Authorization**: super_admin (any), org_admin (org subscriptions)

### F6.6 Re-enable Subscription

**Endpoint**: `POST /v1/subscriptions/{subscription_id}/enable`

**Authorization**: super_admin (any), org_admin (org subscriptions)

**Note**: Re-enabling a trial that has expired will require activation.

### F6.7 Delete Subscription

**Endpoint**: `DELETE /v1/subscriptions/{subscription_id}`

**Authorization**: super_admin (any), org_admin (org subscriptions)

### F6.8 Restore Subscription

**Endpoint**: `POST /v1/subscriptions/{subscription_id}/restore`

**Authorization**: `super_admin` only

### F6.9 Trial Expiration Check (Background Task)

**Endpoint**: `POST /v1/admin/check-trials` (super_admin only for MVP)

**Behavior**:
- Find subscriptions where `status = 'trial'` AND `trial_ends_at < now()`
- Set `status = 'disabled'`
- Log the expiration

## Requirements

| ID | Requirement |
|----|-------------|
| FR-6.1 | New subscriptions MUST start as `trial` status |
| FR-6.2 | `trial_ends_at` MUST be auto-calculated (now + 14 days) |
| FR-6.3 | Only one subscription per tenant+app combination |
| FR-6.4 | Expired trials MUST be disabled |
| FR-6.5 | `days_remaining` MUST be calculated in responses |
| FR-6.6 | tenant_admin cannot activate/disable subscriptions |
| FR-6.7 | Delete MUST be soft (set deleted_at) |
| FR-6.8 | List MUST be scoped by user role |

## Status Transitions

```
                ┌─────────────┐
                │   trial     │
                └──────┬──────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             │             ▼
   ┌───────────┐       │       ┌───────────┐
   │  active   │◄──────┼──────►│  disabled │
   └───────────┘       │       └───────────┘
```

**Allowed Transitions**:
- `trial` → `active` (activate)
- `trial` → `disabled` (disable or expire)
- `active` → `disabled` (disable)
- `disabled` → `active` (enable - only if not expired trial)

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `SUBSCRIPTION_NOT_FOUND` | 404 | Subscription not found |
| `SUBSCRIPTION_EXISTS` | 409 | Subscription already exists for tenant+app |
| `SUBSCRIPTION_ACCESS_DENIED` | 403 | Cannot access this subscription |
| `TRIAL_EXPIRED` | 400 | Trial has expired, activation required |
| `INVALID_STATUS_TRANSITION` | 400 | Invalid status transition |
| `APP_DISABLED` | 400 | Application is disabled |
| `TENANT_DISABLED` | 400 | Tenant is disabled |

## Acceptance Criteria

- [ ] List returns scoped subscriptions based on role
- [ ] Get returns single subscription (if authorized)
- [ ] Create starts 14-day trial with correct trial_ends_at
- [ ] Create fails if subscription exists for tenant+app
- [ ] Activate converts trial to active
- [ ] Disable sets status to disabled
- [ ] Enable re-activates (if not expired trial)
- [ ] Delete soft-deletes subscription
- [ ] Restore recovers soft-deleted subscription (super_admin)
- [ ] days_remaining calculated correctly
- [ ] Trial expiration check disables expired trials
- [ ] Cannot create subscription for disabled app or tenant

## Dependencies

- EPIC 0 (FastAPI skeleton)
- EPIC 1 (Authorization helpers)
- EPIC 2 (Subscription entity + migrations)
- EPIC 3 (Applications - for app validation)
- EPIC 5 (Tenants - for tenant validation)

## Deliverables

- [ ] Subscription CRUD endpoints operational
- [ ] 14-day trial auto-creation
- [ ] Status transition logic
- [ ] Trial expiration check task
- [ ] Unit tests for all endpoints
- [ ] Integration tests with auth scenarios
