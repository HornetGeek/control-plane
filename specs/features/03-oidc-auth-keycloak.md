# Feature Spec: OIDC Authentication (Keycloak)

**Feature ID**: `03-oidc-auth-keycloak`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Implements OpenID Connect authentication using Keycloak as the identity provider. Supports both new user onboarding (with pre-selected org/tenant) and returning user login. Handles user provisioning, session management, and token validation.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-005 | System MUST authenticate users via OIDC authorization code flow with Keycloak |
| FR-006 | System MUST validate bearer tokens using issuer URL and JWKS endpoint |
| FR-007 | System MUST enforce `aud` claim validation |
| FR-008 | System MUST extract user identity (`sub` claim) and profile (`email`, `name`) from validated tokens |
| FR-009 | System MUST support `GET /v1/auth/login` with optional `onboarding_token` parameter |
| FR-010 | System MUST reject same `idp_sub` attempting to onboard into different org |

## Clarifications

| Question | Decision |
|----------|----------|
| Expired session handling | Delete on access attempt, return error |
| Returning user response | Access token + refresh hint |

## Provider Configuration

| Setting | Value |
|---------|-------|
| Provider | Keycloak |
| Realm | `control-plane` |
| Issuer | `http://localhost:18080/realms/control-plane` |
| Authorization Endpoint | `{issuer}/protocol/openid-connect/auth` |
| Token Endpoint | `{issuer}/protocol/openid-connect/token` |
| JWKS Endpoint | `{issuer}/protocol/openid-connect/certs` |
| Client ID | `control-plane` |
| Redirect URI | `/v1/auth/callback` |

## Endpoints

### `GET /v1/auth/login`

Initiate OIDC authentication flow.

**Authentication**: None required

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `onboarding_token` | string | No | Pre-login session token for new users |

#### Response

**302 Found**

Redirects to Keycloak authorization endpoint with the following parameters:

| Parameter | Value |
|-----------|-------|
| `client_id` | `control-plane` |
| `response_type` | `code` |
| `redirect_uri` | `/v1/auth/callback` |
| `state` | JWT containing `{onboarding_token?, nonce, csrf}` |
| `scope` | `openid profile email` |

#### Behavior

1. Generate cryptographically random `state` JWT
2. If `onboarding_token` provided:
   - Look up onboarding session
   - If expired → delete session, return `ONBOARDING_SESSION_EXPIRED`
   - If consumed → return `ONBOARDING_SESSION_CONSUMED`
   - Bind `onboarding_token` to `state` JWT
3. Store `state` in session/cookie for CSRF verification
4. Return 302 redirect to Keycloak

---

### `GET /v1/auth/callback`

Handle OIDC callback after user authentication.

**Authentication**: None required

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | Authorization code from Keycloak |
| `state` | string | Yes | State parameter from login request |

#### Response

**New User (with onboarding_token)**

```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "org_id": "550e8400-e29b-41d4-a716-446655440001",
    "role": "org_admin"
  },
  "tenant": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Headquarters"
  }
}
```

**Returning User (without onboarding_token)**

```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_hint": "Session active. Use /v1/auth/refresh to renew.",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### Behavior

1. Validate `state` parameter:
   - Verify signature
   - Verify CSRF token matches session
   - Extract `onboarding_token` if present

2. Exchange `code` for tokens at Keycloak token endpoint

3. Validate ID token:
   - Verify signature using JWKS
   - Verify `iss` claim matches configured issuer
   - Verify `aud` claim includes `control-plane`
   - Verify token not expired

4. Extract claims: `sub`, `email`, `name`

5. **If onboarding_token present (New User)**:
   - Load onboarding session
   - If expired → delete session, return `ONBOARDING_SESSION_EXPIRED`
   - If consumed → return `ONBOARDING_SESSION_CONSUMED`
   - Check if user exists by `idp_sub`:
     - If exists in different org → return `USER_ORG_CONFLICT`
   - Provision: org, tenant, user, membership, subscription
   - Mark session as `consumed`
   - Return access token + user + tenant info

6. **If no onboarding_token (Returning User)**:
   - Look up user by `idp_sub`
   - If not found → return `USER_NOT_FOUND` (user must onboard first)
   - Update `last_login_at`
   - Return access token + user + refresh hint

---

### `GET /v1/auth/me`

Get current authenticated user profile.

**Authentication**: Required (Bearer token)

#### Response

**200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "org_id": "550e8400-e29b-41d4-a716-446655440001",
  "last_login_at": "2026-02-14T10:30:00Z",
  "created_at": "2026-02-01T09:00:00Z"
}
```

#### Behavior

1. Validate bearer token (JWKS, issuer, audience)
2. Extract `sub` claim
3. Look up user by `idp_sub`
4. Return user profile

## Entity: User

```python
class User:
    id: UUID
    org_id: UUID         # Organization user belongs to
    idp_sub: str         # Keycloak subject (unique)
    email: str           # From IdP
    name: str            # From IdP
    last_login_at: datetime
    created_at: datetime
```

### Constraints

- `idp_sub` must be unique
- `email` should be unique (soft constraint)

## Token Validation

All protected endpoints must validate bearer tokens:

1. Extract token from `Authorization: Bearer <token>` header
2. Fetch JWKS from `{issuer}/protocol/openid-connect/certs`
3. Verify token signature
4. Verify claims:
   - `iss` matches configured issuer
   - `aud` includes `control-plane`
   - `exp` is in the future
   - `iat` is in the past
5. Extract `sub` claim for user lookup

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_STATE` | 400 | State parameter invalid or expired |
| `CODE_EXCHANGE_FAILED` | 400 | Failed to exchange code for tokens |
| `TOKEN_VALIDATION_FAILED` | 401 | Token signature or claims invalid |
| `ONBOARDING_SESSION_EXPIRED` | 400 | Session TTL exceeded |
| `ONBOARDING_SESSION_CONSUMED` | 400 | Session already used |
| `USER_ORG_CONFLICT` | 409 | User exists in different org |
| `USER_NOT_FOUND` | 404 | User not found (must onboard first) |
| `INVALID_TOKEN` | 401 | Invalid or expired bearer token |

## Acceptance Criteria

- [ ] `GET /v1/auth/login` redirects to Keycloak with proper OIDC parameters
- [ ] `GET /v1/auth/login?onboarding_token=...` binds token to state
- [ ] `GET /v1/auth/callback` exchanges code for tokens
- [ ] ID token validated against JWKS with issuer and audience checks
- [ ] New user with onboarding_token gets provisioned with org/tenant/membership
- [ ] Expired onboarding session is deleted and returns `ONBOARDING_SESSION_EXPIRED`
- [ ] Returning user gets access token with refresh hint
- [ ] Same `idp_sub` attempting different org returns `USER_ORG_CONFLICT`
- [ ] `GET /v1/auth/me` returns authenticated user profile
- [ ] Protected endpoints reject invalid/expired tokens

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-005 | OIDC authorization code flow implemented |
| FR-006 | Token validation via JWKS |
| FR-007 | Audience claim validation |
| FR-008 | User identity extraction from claims |
| FR-009 | Optional onboarding_token parameter |
| FR-010 | Reject same idp_sub in different org |

## Dependencies

- Feature `02-onboarding-prelogin` (for onboarding session lookup)
- Keycloak instance running and configured
