# Feature Spec: Launch Token + Redirect

**Feature ID**: `06-launch-token`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Issues short-lived Launch JWTs that allow authenticated users to access subscribed applications. The JWT is passed to the target application via query parameter, enabling seamless SSO into downstream SaaS applications.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-025 | System MUST validate user is member of tenant before issuing Launch JWT |
| FR-026 | System MUST validate tenant has active/trial subscription to requested app |
| FR-027 | System MUST issue short-lived Launch JWT with fixed claims |
| FR-028 | System MUST return 302 redirect to `{app.base_url}/launch?token=...&tenant_id=...` |

## Clarifications

| Question | Decision |
|----------|----------|
| JWT validation method | Shared secret (HMAC-SHA256) |
| Redirect URL format | `{base_url}/launch?token=JWT&tenant_id=ID` |

## JWT Configuration

| Setting | Value |
|---------|-------|
| Algorithm | HMAC-SHA256 (`HS256`) |
| TTL | 5 minutes |
| Shared Secret | Configured via `LAUNCH_JWT_SECRET` env var |
| Issuer | `control-plane` |

## Endpoint

### `GET /v1/launch`

Generate a Launch JWT and redirect to the target application.

**Authentication**: Required (Bearer token)

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | UUID | Yes | Tenant to launch as |
| `app_id` | UUID | Yes | Application to launch |

#### Response

**302 Found**

Redirects to: `{app.base_url}/launch?token={jwt}&tenant_id={tenant_id}`

**Headers**:
```
Location: http://localhost:8001/launch?token=eyJhbGc...&tenant_id=550e8400-e29b-41d4-a716-446655440000
```

#### Behavior

1. **Validate Membership**:
   - Look up membership for `(user_id, tenant_id)`
   - If not found → return `NOT_TENANT_MEMBER`

2. **Validate Subscription**:
   - Look up subscription for `(tenant_id, app_id)`
   - If not found → return `NO_SUBSCRIPTION`
   - If `status != trial` → return `NO_SUBSCRIPTION`
   - If `trial_ends_at < now` → return `TRIAL_EXPIRED`

3. **Load Application**:
   - Look up application by `app_id`
   - If not found or inactive → return `APP_NOT_FOUND`

4. **Generate Launch JWT**:
   - Create JWT with claims (see below)
   - Sign with shared secret
   - Set 5-minute expiration

5. **Return Redirect**:
   - Construct URL: `{base_url}/launch?token={jwt}&tenant_id={tenant_id}`
   - Return 302 with Location header

## Launch JWT Structure

### Header

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload (Claims)

| Claim | Type | Description |
|-------|------|-------------|
| `iss` | string | `control-plane` (issuer) |
| `sub` | UUID | User ID |
| `tenant_id` | UUID | Tenant ID |
| `app_id` | UUID | Application ID |
| `app_key` | string | Application key (e.g., "pacs") |
| `email` | string | User email |
| `name` | string | User display name |
| `role` | string | User's role in this tenant |
| `exp` | number | Expiration timestamp (Unix) |
| `iat` | number | Issued at timestamp (Unix) |
| `jti` | UUID | Unique token identifier (for revocation) |

### Example Payload

```json
{
  "iss": "control-plane",
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
  "app_id": "550e8400-e29b-41d4-a716-446655440002",
  "app_key": "pacs",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "tenant_admin",
  "exp": 1739584800,
  "iat": 1739584500,
  "jti": "550e8400-e29b-41d4-a716-446655440003"
}
```

## Application Contract

Target applications MUST implement the following:

### Launch Endpoint

```
GET /launch?token={jwt}&tenant_id={id}
```

### Token Validation

Applications should:

1. Extract JWT from `token` query parameter
2. Validate signature using shared secret
3. Validate claims:
   - `iss` == `control-plane`
   - `exp` > now
   - `tenant_id` matches query parameter
4. Extract user identity from claims
5. Create session for user

### Error Response (Invalid Token)

```json
{
  "error": "INVALID_LAUNCH_TOKEN",
  "message": "Launch token is invalid or expired"
}
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `NOT_TENANT_MEMBER` | 403 | User is not a member of the specified tenant |
| `NO_SUBSCRIPTION` | 403 | Tenant has no subscription to this app |
| `TRIAL_EXPIRED` | 403 | Trial subscription has expired |
| `APP_NOT_FOUND` | 404 | Application not found or inactive |
| `TENANT_NOT_FOUND` | 404 | Tenant not found |
| `VALIDATION_ERROR` | 400 | Invalid query parameters |

## Security Considerations

1. **Short TTL**: 5-minute expiration limits exposure if token is leaked
2. **Single Use**: The `jti` claim enables token revocation/blacklisting
3. **Tenant Binding**: Token includes `tenant_id` to prevent cross-tenant use
4. **HTTPS Required**: In production, all endpoints must use HTTPS
5. **Secret Rotation**: Shared secret should be rotatable without downtime

## Acceptance Criteria

- [ ] Returns 302 redirect with Launch JWT
- [ ] JWT signed with HMAC-SHA256
- [ ] JWT expires in 5 minutes
- [ ] JWT contains all required claims
- [ ] Non-members receive `NOT_TENANT_MEMBER`
- [ ] No subscription returns `NO_SUBSCRIPTION`
- [ ] Expired trial returns `TRIAL_EXPIRED`
- [ ] Redirect URL format: `{base_url}/launch?token=JWT&tenant_id=ID`
- [ ] Token validation succeeds at target app

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-025 | Membership validation before JWT issuance |
| FR-026 | Subscription validation (active/trial) |
| FR-027 | Short-lived JWT with fixed claims |
| FR-028 | 302 redirect to app launch endpoint |

## Dependencies

- Feature `04-tenants-memberships` (for membership validation)
- Feature `05-subscriptions-trial` (for subscription validation)
- Feature `01-public-apps` (for application lookup)
- Shared secret configuration with target applications
