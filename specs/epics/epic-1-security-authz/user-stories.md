# User Stories — EPIC 1: Security & Delegated Authorization

**Epic**: [epic.md](./epic.md)
**User Personas**: Platform Administrator, Developer
**Total Stories**: 5
**Total Points**: 16

---

## US-1.1: Local OIDC Token Validation

**As a** platform administrator,
**I want** the system to validate OIDC access tokens locally,
**So that** authentication is fast and doesn't depend on external calls for every request.

### Acceptance Criteria
- [ ] JWKS fetched and cached from Keycloak
- [ ] Token `iss` claim validated against configured issuer
- [ ] Token `aud` claim validated against client ID
- [ ] Token `exp` validated with clock skew tolerance (±30s)
- [ ] Invalid/expired tokens return 401 with `INVALID_TOKEN` error code
- [ ] Valid tokens extract `sub` claim for user identity

### Files to Create
- `src/auth/__init__.py`
- `src/auth/jwks.py`
- `src/auth/token.py`

**Priority**: P0
**Points**: 5

---

## US-1.2: Mock Core AuthZ Client

**As a** developer,
**I want** a mock Core authorization client,
**So that** I can develop and test authorization logic without a real Core service.

### Acceptance Criteria
- [ ] Mock client returns predictable allow/deny based on configured scenarios
- [ ] Supports all roles: super_admin, org_admin, tenant_admin, tenant_member
- [ ] Returns org_id and tenant_ids for scoped roles
- [ ] Configurable delay for timeout testing
- [ ] Returns `AUTHZ_SERVICE_UNAVAILABLE` (503) when configured to fail

### Files to Create
- `src/clients/__init__.py`
- `src/clients/mock_core.py`

**Priority**: P0
**Points**: 3

---

## US-1.3: Redis Cache for AuthZ Decisions

**As a** platform administrator,
**I want** authorization decisions cached in Redis,
**So that** repeated requests are fast and Core service load is reduced.

### Acceptance Criteria
- [ ] Cache key: `sha256(token) + action + resource_type + org_id? + tenant_id?`
- [ ] Allow decisions cached for min(token_expiry, 60-300s)
- [ ] Deny decisions cached for 30-60s (negative cache)
- [ ] Cache TTL never exceeds token expiry
- [ ] Cache hit returns decision without calling Core

### Files to Create
- `src/auth/cache.py`

**Priority**: P0
**Points**: 3

---

## US-1.4: Authorization Helpers

**As a** backend developer,
**I want** reusable authorization dependency functions,
**So that** I can easily protect endpoints with role-based access control.

### Acceptance Criteria
- [ ] `require_super_admin()` - returns 403 if not super_admin
- [ ] `require_org_admin(org_id)` - returns 403 if not org_admin for org
- [ ] `require_tenant_admin(tenant_id)` - returns 403 if not tenant_admin for tenant
- [ ] `require_any_role(org_id)` - returns 403 for tenant_member (no CP access)
- [ ] All helpers return User object with role and scope info

### Files to Create
- `src/auth/deps.py`

**Priority**: P0
**Points**: 3

---

## US-1.5: Tenant Context Resolver

**As a** backend developer,
**I want** a tenant context resolver,
**So that** I can determine which tenant a request is operating on.

### Acceptance Criteria
- [ ] Supports `X-Tenant-ID` header OR path/query parameter
- [ ] Validates user has membership in resolved tenant
- [ ] Mismatch returns 403 with `TENANT_CONTEXT_MISMATCH` error code

### Files to Create
- `src/auth/context.py`

**Priority**: P1
**Points**: 2

---

## Story Dependencies

```
US-1.1 (Token Validation)
     │
     ▼
US-1.2 (Mock Core) ──► US-1.3 (Redis Cache)
     │                        │
     └────────┬───────────────┘
              ▼
       US-1.4 (Auth Helpers)
              │
              ▼
       US-1.5 (Context Resolver)
```
