# Feature Spec: Pre-login Onboarding

**Feature ID**: `02-onboarding-prelogin`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Creates a pre-login onboarding session that captures the user's intended organization name, tenant name, and selected application. The session is later consumed during OIDC callback to provision the user into the correct org/tenant with a trial subscription.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | System MUST accept pre-login form with `app_id`, `org_name`, `tenant_name` |
| FR-002 | System MUST create onboarding session with 60-minute TTL |
| FR-003 | System MUST enforce single-consume on onboarding sessions via status field |
| FR-004 | System MUST bind OIDC `state` parameter to `onboarding_token` for CSRF protection |

## Clarifications

| Question | Decision |
|----------|----------|
| Name validation | Alphanumeric + spaces/hyphens, 3-50 chars |
| org_name uniqueness | Globally unique (checked before creating session) |

## Endpoint

### `POST /v1/onboarding`

Create a new onboarding session.

**Authentication**: None required (pre-login)

#### Request

```json
{
  "app_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Acme Corporation",
  "tenant_name": "Headquarters"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `app_id` | UUID | Yes | ID of the application to subscribe to |
| `org_name` | string | Yes | Desired organization name |
| `tenant_name` | string | Yes | Desired tenant/branch name |

#### Validation Rules

| Field | Rules |
|-------|-------|
| `org_name` | 3-50 characters, alphanumeric + spaces + hyphens only, globally unique |
| `tenant_name` | 3-50 characters, alphanumeric + spaces + hyphens only |

**Regex Pattern**: `^[a-zA-Z0-9\s\-]{3,50}$`

#### Response

**201 Created**

```json
{
  "onboarding_token": "ob_abc123def456",
  "login_url": "/v1/auth/login?onboarding_token=ob_abc123def456",
  "expires_at": "2026-02-14T15:00:00Z"
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `onboarding_token` | string | Unique token to reference this session (bound to OIDC state) |
| `login_url` | string | Relative URL to initiate OIDC login with this session |
| `expires_at` | string (ISO 8601) | Session expiration timestamp |

## Entity: OnboardingSession

```python
class OnboardingSession:
    id: UUID
    token: str           # Unique session token (indexed)
    org_name: str        # Desired organization name
    tenant_name: str     # Desired tenant name
    app_id: UUID         # Selected application
    status: str          # "pending" | "consumed" | "expired"
    expires_at: datetime # TTL = created_at + 60 minutes
    created_at: datetime
```

### Status Transitions

```
pending → consumed  (on successful OIDC callback)
pending → expired   (on TTL exceeded)
```

### Constraints

- `token` must be unique
- `org_name` must be globally unique (no two pending sessions with same org_name)

## Behavior

### Session Creation

1. Validate request body against schema
2. Validate `app_id` exists and `status=active`
3. Check `org_name` is not already used by an existing organization
4. Check `org_name` is not used by another `pending` onboarding session
5. Generate unique `token` (cryptographically random)
6. Set `expires_at = now + 60 minutes`
7. Set `status = pending`
8. Persist session and return response

### Session Consumption (during OIDC callback)

1. Validate session exists and `status = pending`
2. Validate session has not expired (`expires_at > now`)
3. Mark `status = consumed`
4. Proceed with provisioning

### Session Expiration

- Expired sessions are detected during callback
- Expired sessions return `ONBOARDING_SESSION_EXPIRED` error
- **Note**: Expired sessions are deleted on access attempt (not proactively cleaned)

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request body or field values |
| `APP_NOT_FOUND` | 404 | Application with given `app_id` not found |
| `ORG_NAME_EXISTS` | 409 | Organization name already in use |
| `ORG_NAME_RESERVED` | 409 | org_name used by pending onboarding session |

## Acceptance Criteria

- [ ] `POST /v1/onboarding` creates session with 60-minute TTL
- [ ] `org_name` and `tenant_name` validated as alphanumeric + spaces/hyphens, 3-50 chars
- [ ] `org_name` globally unique (no duplicate orgs, no duplicate pending sessions)
- [ ] Returns `onboarding_token`, `login_url`, and `expires_at`
- [ ] Session status starts as `pending`
- [ ] Attempting to reuse consumed session returns `ONBOARDING_SESSION_CONSUMED`
- [ ] Expired session returns `ONBOARDING_SESSION_EXPIRED`
- [ ] Non-existent application returns `APP_NOT_FOUND`

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-001 | Endpoint accepts `app_id`, `org_name`, `tenant_name` |
| FR-002 | Session TTL of 60 minutes |
| FR-003 | Status field enforces single-consume |
| FR-004 | Token bound to OIDC state parameter |

## Dependencies

- Feature `01-public-apps` (for application lookup/validation)
