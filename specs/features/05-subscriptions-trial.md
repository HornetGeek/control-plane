# Feature Spec: Trial Subscriptions

**Feature ID**: `05-subscriptions-trial`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Manages trial subscriptions that grant tenants access to applications. Trials are created automatically during onboarding and can be added manually for additional applications. This feature enforces trial expiration and prevents launch for expired subscriptions.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-011 | System MUST auto-provision organization if not exists (from onboarding `org_name`) |
| FR-012 | System MUST auto-provision tenant if not exists (from onboarding `tenant_name`) |
| FR-015 | System MUST create trial subscription with `status=trial`, `trial_ends_at = now + 14 days` |
| FR-022 | System MUST allow `org_admin` and `tenant_admin` to create trial subscriptions |
| FR-023 | System MUST make subscription creation idempotent per `(tenant_id, app_id)` |
| FR-024 | System MUST allow listing subscriptions for a tenant |

## Clarifications

| Question | Decision |
|----------|----------|
| Expired trial handling | Block launch, keep record |
| Multiple trials same app | No, idempotent (one trial per tenant+app) |

## Trial Duration

- **Duration**: 14 days from creation
- **Status**: `trial` only (MVP - no paid status)
- **Auto-creation**: During onboarding for selected app

## Endpoints

### `POST /v1/subscriptions`

Create a trial subscription for a tenant to an application.

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` or `tenant_admin` of the tenant

#### Request

```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "app_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | UUID | Yes | Tenant to subscribe |
| `app_id` | UUID | Yes | Application to subscribe to |

#### Response

**201 Created** (new subscription)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "app_id": "550e8400-e29b-41d4-a716-446655440001",
  "app_name": "PACS",
  "status": "trial",
  "trial_ends_at": "2026-02-28T10:30:00Z",
  "created_at": "2026-02-14T10:30:00Z"
}
```

**200 OK** (idempotent - existing subscription)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "app_id": "550e8400-e29b-41d4-a716-446655440001",
  "app_name": "PACS",
  "status": "trial",
  "trial_ends_at": "2026-02-28T10:30:00Z",
  "created_at": "2026-02-01T09:00:00Z",
  "_existing": true
}
```

#### Behavior

1. Validate user is `org_admin` or `tenant_admin` of the tenant
2. Validate tenant exists and user has access
3. Validate application exists and is active
4. Check if subscription already exists for `(tenant_id, app_id)`:
   - If exists → return existing subscription (idempotent)
   - If not exists → create new subscription
5. For new subscriptions:
   - Set `status = trial`
   - Set `trial_ends_at = now + 14 days`
6. Return subscription

---

### `GET /v1/tenants/{id}/subscriptions`

List all subscriptions for a tenant.

**Authentication**: Required (Bearer token)
**Authorization**: Must be member of tenant

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tenant ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter by status: `trial`, `all` |
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page (max 100) |

#### Response

**200 OK**

```json
{
  "subscriptions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
      "app_id": "550e8400-e29b-41d4-a716-446655440001",
      "app_key": "pacs",
      "app_name": "PACS",
      "status": "trial",
      "trial_ends_at": "2026-02-28T10:30:00Z",
      "is_expired": false,
      "days_remaining": 14,
      "created_at": "2026-02-14T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_expired` | boolean | `trial_ends_at < now` |
| `days_remaining` | int | Days until trial ends (0 if expired) |

#### Behavior

1. Validate user is member of tenant
2. Load subscriptions with application details
3. Calculate `is_expired` and `days_remaining`
4. Apply status filter if provided
5. Return paginated list

---

### `GET /v1/subscriptions/{id}`

Get details of a specific subscription.

**Authentication**: Required (Bearer token)
**Authorization**: Must be member of tenant that owns subscription

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Subscription ID |

#### Response

**200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "app_id": "550e8400-e29b-41d4-a716-446655440001",
  "app_key": "pacs",
  "app_name": "PACS",
  "app_base_url": "http://localhost:8001",
  "status": "trial",
  "trial_ends_at": "2026-02-28T10:30:00Z",
  "is_expired": false,
  "days_remaining": 14,
  "created_at": "2026-02-14T10:30:00Z"
}
```

#### Behavior

1. Load subscription with application details
2. Validate user is member of the subscription's tenant
3. Calculate `is_expired` and `days_remaining`
4. Return subscription details

## Entity: Subscription

```python
class Subscription:
    id: UUID
    tenant_id: UUID       # Tenant owning subscription
    app_id: UUID          # Application subscribed to
    status: str           # "trial" (MVP only)
    trial_ends_at: datetime  # End of trial period
    created_at: datetime
```

### Constraints

- `UNIQUE(tenant_id, app_id)` - one subscription per tenant+app

### Computed Fields

```python
@property
def is_expired(self) -> bool:
    return datetime.utcnow() > self.trial_ends_at

@property
def days_remaining(self) -> int:
    if self.is_expired:
        return 0
    delta = self.trial_ends_at - datetime.utcnow()
    return max(0, delta.days)
```

## Subscription Status Check (for Launch)

The launch endpoint checks subscription validity:

```python
def is_subscription_active(subscription: Subscription) -> bool:
    """Check if subscription allows launch."""
    if subscription.status != "trial":
        return False
    if subscription.is_expired:
        return False
    return True
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `FORBIDDEN` | 403 | User lacks required role |
| `NOT_TENANT_MEMBER` | 403 | User not member of tenant |
| `TENANT_NOT_FOUND` | 404 | Tenant not found |
| `APP_NOT_FOUND` | 404 | Application not found |
| `APP_INACTIVE` | 400 | Application is not active |
| `SUBSCRIPTION_NOT_FOUND` | 404 | Subscription not found |
| `TRIAL_EXPIRED` | 403 | Trial period has ended |
| `VALIDATION_ERROR` | 400 | Invalid request data |

## Acceptance Criteria

- [ ] Trial subscriptions created with 14-day expiry
- [ ] `POST /v1/subscriptions` is idempotent per (tenant, app)
- [ ] Existing subscription returns 200 with original dates
- [ ] `org_admin` and `tenant_admin` can create subscriptions
- [ ] `tenant_member` cannot create subscriptions
- [ ] Subscription list includes `is_expired` and `days_remaining`
- [ ] Expired subscriptions are retained (not deleted)
- [ ] Expired subscriptions block launch with `TRIAL_EXPIRED`
- [ ] Auto-creation during onboarding works correctly

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-011 | Org auto-provisioned (in onboarding callback) |
| FR-012 | Tenant auto-provisioned (in onboarding callback) |
| FR-015 | Trial with 14-day expiry |
| FR-022 | org_admin/tenant_admin can create |
| FR-023 | Idempotent per (tenant_id, app_id) |
| FR-024 | List subscriptions for tenant |

## Dependencies

- Feature `04-tenants-memberships` (for tenant access validation)
- Feature `01-public-apps` (for application lookup)
