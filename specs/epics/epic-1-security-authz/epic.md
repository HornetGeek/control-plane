# EPIC 1 — Security & Delegated Authorization

**Epic ID**: `epic-1-security-authz`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-15
**Priority**: P0 (Core)
**Depends On**: EPIC 0, EPIC 2 (for tenant context)

## Goal

Implement local OIDC token validation and delegated authorization to mock Core with Redis caching.

## Features

### F1.1 Local OIDC Access Token Validation

- JWKS caching (refresh on unknown key)
- Verify `iss` matches configured issuer
- Verify `aud` matches client ID
- Verify `exp` (with clock skew tolerance)
- Extract `sub` claim for user identity

### F1.2 Mock Core AuthZ Client

**MVP Note**: Core service is out of scope. This is a mock client.

- Returns predictable allow/deny based on configured scenarios
- Simulates role-based access (super_admin, org_admin, tenant_admin)
- Simulates scope resolution (org_id, tenant_ids)
- Configurable delay/timeout for testing

### F1.3 Redis Cache for AuthZ Decisions

**Cache Key**: `sha256(token) + action + resource_type + org_id? + tenant_id?`

**Cache Value**:
```json
{
  "allow": true,
  "sub": "user-uuid",
  "org_id": "org-uuid",
  "tenant_ids": ["tenant-uuid-1"],
  "effective_role": "tenant_admin",
  "expires_at": 1739584800
}
```

**TTL Rules**:
- Allow decisions: min(token_expiry, 60-300s)
- Deny decisions: 30-60s (negative cache)

### F1.4 Authorization Helpers

```python
async def require_super_admin(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Raises 403 if not super_admin"""

async def require_org_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    org_id: UUID
) -> User:
    """Raises 403 if not org_admin for this org"""

async def require_tenant_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    tenant_id: UUID
) -> User:
    """Raises 403 if not tenant_admin for this tenant"""

async def require_any_role(
    token: Annotated[str, Depends(oauth2_scheme)],
    org_id: UUID
) -> User:
    """Returns user with role info, tenant_member gets 403 for CP access"""
```

### F1.5 Tenant Context Resolver

- Support `X-Tenant-ID` header OR path/query parameter
- Validate user has membership in resolved tenant
- Mismatch → `TENANT_CONTEXT_MISMATCH` error

## Requirements

| ID | Requirement |
|----|-------------|
| FR-1.1 | System MUST validate bearer tokens locally via JWKS |
| FR-1.2 | System MUST verify iss, aud, exp claims |
| FR-1.3 | System MUST delegate authorization to mock Core |
| FR-1.4 | System MUST cache authorization decisions in Redis |
| FR-1.5 | Cache TTL MUST NOT exceed token expiry |
| FR-1.6 | tenant_member MUST be denied CP access |
| FR-1.7 | System MUST fail closed if mock Core is unreachable |

## AuthZ Decision Flow

```
1. Extract bearer token from Authorization header
2. Validate token locally (JWKS, iss, aud, exp)
3. Build request context: action, resource_type, org_id?, tenant_id?
4. Generate cache key: sha256(token) + context
5. Check Redis cache
   ├─ HIT: Return cached decision
   └─ MISS: Call mock Core → Cache result → Return decision
6. Enforce allow/deny
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_TOKEN` | 401 | Invalid or expired token |
| `TOKEN_EXPIRED` | 401 | Token has expired |
| `INVALID_ISSUER` | 401 | Token issuer mismatch |
| `INVALID_AUDIENCE` | 401 | Token audience mismatch |
| `FORBIDDEN` | 403 | Authorization denied by Core |
| `TENANT_MEMBER_DENIED` | 403 | tenant_member cannot access CP |
| `TENANT_CONTEXT_MISMATCH` | 403 | User not member of resolved tenant |
| `AUTHZ_SERVICE_UNAVAILABLE` | 503 | Core (mock) unreachable |

## Mock Core Configuration

```python
MOCK_CORE_SCENARIOS = {
    "super_admin": {
        "sub": "super-admin-uuid",
        "effective_role": "super_admin",
        "org_id": None,
        "tenant_ids": [],
    },
    "org_admin_acme": {
        "sub": "org-admin-uuid",
        "effective_role": "org_admin",
        "org_id": "acme-org-uuid",
        "tenant_ids": ["tenant-1", "tenant-2"],
    },
    "tenant_admin_acme_t1": {
        "sub": "tenant-admin-uuid",
        "effective_role": "tenant_admin",
        "org_id": "acme-org-uuid",
        "tenant_ids": ["tenant-1"],
    },
    "tenant_member_acme_t1": {
        "sub": "tenant-member-uuid",
        "effective_role": "tenant_member",
        "org_id": "acme-org-uuid",
        "tenant_ids": ["tenant-1"],
    },
}
```

## Acceptance Criteria

- [ ] Invalid token returns 401 `INVALID_TOKEN`
- [ ] Expired token returns 401 `TOKEN_EXPIRED`
- [ ] Valid token with tenant_member role returns 403 `TENANT_MEMBER_DENIED`
- [ ] super_admin passes `require_super_admin()`
- [ ] org_admin passes `require_org_admin(org_id)` for their org only
- [ ] tenant_admin passes `require_tenant_admin(tenant_id)` for their tenant only
- [ ] Authorization decisions cached in Redis
- [ ] Cache hits return cached decision without mock Core call
- [ ] Mock Core unreachable returns 503 with `AUTHZ_SERVICE_UNAVAILABLE`

## Dependencies

- EPIC 0 (Redis bootstrap)
- EPIC 2 (Tenant entities for context resolver)

## Deliverables

- [ ] All protected endpoints enforce mock Core decisions
- [ ] Consistent error envelope on auth failures
- [ ] Redis caching operational
