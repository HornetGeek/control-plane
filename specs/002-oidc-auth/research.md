# Research: OIDC Authentication

**Feature**: 002-oidc-auth
**Date**: 2026-02-11

## Overview

This document captures technical research and decisions for implementing OpenID Connect authentication with Zitadel as the identity provider.

## Research Topics

### 1. OIDC Authorization Code Flow

**Question**: What OIDC flow should be used for browser-based authentication?

**Decision**: Authorization Code Flow with PKCE (not required for confidential client but recommended)

**Rationale**:
- Authorization Code Flow is the most secure OIDC flow for server-side applications
- The control plane is a confidential client (can store client_secret securely)
- PKCE provides additional protection against authorization code interception
- Zitadel fully supports this flow

**Alternatives Considered**:
- **Implicit Flow**: Rejected due to security vulnerabilities (no longer recommended by OAuth 2.1)
- **Hybrid Flow**: More complex; benefits not needed for our use case
- **Client Credentials Flow**: Not applicable (used for service-to-service, not user auth)

**Implementation Notes**:
- Response type: `code`
- Token endpoint: `{issuer}/oauth/v2/token`
- Authorization endpoint: `{issuer}/oauth/v2/authorize`

### 2. JWKS Caching Strategy

**Question**: How should JWKS (JSON Web Key Set) be cached to balance performance and security?

**Decision**: In-memory cache with 5-minute TTL

**Rationale**:
- 5 minutes is a standard industry default (matches rotation best practices)
- Signaling key rotation is rare; most IdPs rotate keys days or weeks in advance
- Cache expiration before key rotation is acceptable (fallback to fetch)
- Signatures don't change frequently, so extended cache is safe

**Alternatives Considered**:
- **No caching (fetch every request)**: Adds ~100-500ms per request; unnecessary load on IdP
- **Longer TTL (15-60 minutes)**: Increases window for serving stale keys if rotation happens
- **Distributed cache (Redis)**: Overkill for single-service deployment; adds dependency

**Implementation Notes**:
- Use `lru_cache` or simple in-memory dict with timestamp
- Refresh on TTL expiry or JWT decode failure (key not found)
- Thread-safe for async context (use lock or asyncio.Lock)

### 3. Token Validation Library Selection

**Question**: Which Python library should be used for JWT validation?

**Decision**: `python-jose` with `cryptography` backend

**Rationale**:
- `python-jose` is actively maintained and widely used
- Supports JWKS client out of the box
- Compatible with async/await patterns
- Already in project dependencies from 001-control-plane-mvp

**Alternatives Considered**:
- **PyJWT alone**: Requires manual JWKS fetching and key matching
- **authlib**: More comprehensive but heavier dependency
- **Pure-JWT libraries**: Lack JWKS integration

**Implementation Notes**:
```python
from jwt import decode, PyJWKClient
from jwt.exceptions import InvalidTokenError

jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")
signing_key = jwks_client.get_signing_key_from_jwt(token)
payload = decode(token, key=signing_key, algorithms=["RS256"], ...)
```

### 4. Required Claims and Validation

**Question**: Which claims must be extracted and validated from the OIDC token?

**Decision**:
- **Required claims**: `sub` (user ID), `org_id` (organization), `email` (user email)
- **Optional claims**: `name` (display name, fallback to email)
- **Validation**: Issuer, Audience, Expiration

**Rationale**:
- `sub` is the standard OIDC subject claim (unique user identifier from IdP)
- `org_id` is a custom claim required by our multi-tenant architecture
- `email` is required for user identification and communication
- Issuer/Audience validation prevents token acceptance from wrong sources

**Alternatives Considered**:
- **Use `preferred_username` instead of `email`**: Email is more reliable for user identification
- **Allow missing `org_id` with default**: Would break multi-tenancy model
- **Trust `sub` as database ID**: Use separate UUID to allow IdP-independent user management

**Implementation Notes**:
- Validate `iss` against configured `OIDC_ISSUER`
- Validate `aud` against configured `OIDC_CLIENT_ID`
- Extract `sub` as `idp_sub` (store in database)
- Extract `org_id` directly (must be UUID string from IdP)

### 5. State Parameter for CSRF Protection

**Question**: How should the OAuth 2.0 state parameter be generated and validated?

**Decision**: Cryptographically random 32-byte URL-safe string, stored in session/temporary cache

**Rationale**:
- Prevents CSRF attacks on the OAuth callback
- 32 bytes (256 bits) provides sufficient entropy
- URL-safe encoding ensures safe transport in query parameters
- State should be short-lived (5-10 minutes)

**Alternatives Considered**:
- **No state parameter**: Vulnerable to CSRF attacks
- **State in server session**: Requires session management complexity
- **Signed state (HMAC)**: Overkill; random nonce is sufficient

**Implementation Notes**:
```python
import secrets

state = secrets.token_urlsafe(32)
# Store state with timestamp (e.g., Redis or in-memory cache)
# Validate on callback; reject if mismatch or expired (>5 min)
```

### 6. User Provisioning Strategy

**Question**: How should users be provisioned on first login?

**Decision**: Automatic get-or-create by `idp_sub` (sub claim)

**Rationale**:
- `idp_sub` is the unique identifier from IdP (never changes for same user)
- Get-or-create is idempotent (safe for retries)
- Organization is assigned from `org_id` claim (must exist or be created separately)
- Last login timestamp updated on every successful authentication

**Alternatives Considered**:
- **Manual user creation before login**: Poor UX; creates barrier to entry
- **Create by email**: Email can change; not a stable identifier
- **Require pre-existing organization**: Could be done; organization creation is separate process

**Implementation Notes**:
- Query user by `idp_sub`
- If not found, create new user with `organization_id=org_id`, `status=active`
- If found, update `last_login_at` only
- Do NOT update `organization_id` on existing user (fixed at creation)

### 7. Organization Pre-Creation

**Question**: Should organizations be auto-created if they don't exist?

**Decision**: No - organizations must exist before user authentication

**Rationale**:
- Organization creation is a separate business process (customer onboarding)
- Auto-creating organizations could enable unauthorized org creation
- Allows for validation and approval workflow during customer signup
- Consistent with assumption: "Organizations are created in the system before users authenticate"

**Alternatives Considered**:
- **Auto-create org from `org_id` claim**: Could work but bypasses business validation
- **Allow orphan users**: User record created but can't access anything until org exists

**Implementation Notes**:
- User's `organization_id` is set from `org_id` claim regardless of whether org exists
- FK constraint may be deferred or org_id stored as string (no FK enforcement)
- Authorization checks will fail if user tries to access non-existent org resources

### 8. Bearer Token Authentication for API Calls

**Question**: How should API clients authenticate after receiving the access token?

**Decision**: Standard `Authorization: Bearer <token>` header

**Rationale**:
- RFC 6750 standard for OAuth 2.0 Bearer tokens
- Supported by all HTTP clients and FastAPI's HTTPBearer security
- Simple and widely understood

**Alternatives Considered**:
- **Cookie-based session**: Not suitable for API clients
- **API key in header**: Additional authentication method; not OAuth 2.0 compliant
- **Token in query parameter**: Security risk (logged in URLs, browser history)

**Implementation Notes**:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()
credentials = await security(request)
token = credentials.credentials
```

### 9. Error Handling and User-Facing Messages

**Question**: What errors should be exposed to clients and how should they be formatted?

**Decision**: Structured error responses with safe messages

**Rationale**:
- Security: Don't expose internal errors or token details
- Usability: Provide actionable error messages
- Consistency: Follow constitution's error format standard

**Error Categories**:
- **400 Bad Request**: Invalid code, missing claims, malformed token
- **401 Unauthorized**: Expired token, invalid signature, missing token
- **500 Internal Server Error**: IdP unavailability (use generic message)

**Implementation Notes**:
```python
{
    "code": "AUTH_INVALID_TOKEN",
    "message": "The provided token is invalid or expired",
    "details": {}
}
```

### 10. Testing Strategy

**Question**: How should the OIDC authentication flow be tested?

**Decision**: Three-tier testing approach

**Unit Tests**:
- Token validation logic with mock JWKS
- Claim extraction with various token payloads
- State parameter generation
- User provisioning get-or-create logic

**Integration Tests**:
- Full authentication flow with test IdP (or mocked responses)
- Database integration for user creation/retrieval
- Token endpoint mocking with httpx mock transport

**Contract Tests**:
- API response format verification
- Error response structure validation
- OpenAPI schema compliance

**Alternatives Considered**:
- **Tests against real Zitadel**: Requires external dependency; slower test suite
- **No integration tests**: Insufficient coverage for critical auth flow

## Summary of Decisions

| Topic | Decision | Key Consideration |
|-------|----------|-------------------|
| OIDC Flow | Authorization Code Flow | Most secure for server-side apps |
| JWKS Caching | 5-minute in-memory TTL | Balance performance vs. key rotation |
| JWT Library | python-jose | JWKS support, async-compatible |
| Required Claims | sub, org_id, email | Multi-tenancy requires org_id |
| State Parameter | 32-byte random string | CSRF protection |
| User Provisioning | Auto get-or-create by idp_sub | Idempotent, no barriers |
| Organization Creation | Separate process | Business validation required |
| API Auth | Bearer header | RFC 6750 standard |
| Error Format | Structured, safe messages | Security + usability |

## Open Questions

None - all technical decisions have been resolved.

## References

- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 6750 - Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [Zitadel Documentation](https://zitadel.com/docs)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
