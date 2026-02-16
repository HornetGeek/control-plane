# Tasks — EPIC 1: Security & Delegated Authorization

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 24
**Estimated Time**: 3-4 days

---

## Format: `[ID] [P?] [US] Description`

- **[P]**: Parallelizable
- **[US]**: User Story reference

---

## Phase 1: Auth Module Setup

- [x] T001 [P] Create `src/auth/__init__.py`
- [x] T002 [P] Create `src/clients/__init__.py`

---

## Phase 2: OIDC Token Validation (US-1.1)

- [x] T003 Create `src/auth/jwks.py` with JWKS client and caching
- [x] T004 Add JWKS refresh on unknown key in `src/auth/jwks.py`
- [x] T005 Create `src/auth/token.py` with token validation function
- [x] T006 Implement `iss` claim validation in `src/auth/token.py`
- [x] T007 Implement `aud` claim validation in `src/auth/token.py`
- [x] T008 Implement `exp` claim validation with clock skew in `src/auth/token.py`
- [x] T009 Add `sub` claim extraction in `src/auth/token.py`
- [x] T010 Create `src/schemas/__init__.py` and `src/schemas/user.py` with User schema

---

## Phase 3: Mock Core Client (US-1.2)

- [x] T011 Create `src/clients/mock_core.py` with MockCoreClient class
- [x] T012 Add scenario-based responses in `src/clients/mock_core.py`
- [x] T013 Add configurable delay/timeout support
- [x] T014 Add `check_authorization()` method returning allow/deny with role/scope

---

## Phase 4: AuthZ Cache (US-1.3)

- [x] T015 Create `src/auth/cache.py` with AuthZ cache class
- [x] T016 Implement cache key generation: `sha256(token) + context`
- [x] T017 Implement `get_cached_decision()` method
- [x] T018 Implement `cache_decision()` method with TTL logic
- [x] T019 Add negative caching for deny decisions (30-60s TTL)

---

## Phase 5: Authorization Helpers (US-1.4)

- [x] T020 Create `src/auth/deps.py` with OAuth2 scheme
- [x] T021 Implement `require_super_admin()` dependency
- [x] T022 Implement `require_org_admin(org_id)` dependency
- [x] T023 Implement `require_tenant_admin(tenant_id)` dependency
- [x] T024 Implement `require_any_role(org_id)` dependency
- [x] T025 Add tenant_member denial (403) in all helpers

---

## Phase 6: Tenant Context (US-1.5)

- [x] T026 Create `src/auth/context.py` with TenantContextResolver
- [x] T027 Support `X-Tenant-ID` header resolution
- [x] T028 Support path/query parameter resolution
- [x] T029 Add membership validation with `TENANT_CONTEXT_MISMATCH` error

---

## Phase 7: Integration & Tests

- [x] T030 [P] Create `tests/unit/auth/test_token.py`
- [x] T031 [P] Create `tests/unit/auth/test_cache.py`
- [x] T032 [P] Create `tests/unit/clients/test_mock_core.py`
- [ ] T033 Create `tests/integration/test_auth_flow.py`
- [ ] T034 Verify 401 for invalid token
- [ ] T035 Verify 403 for tenant_member
- [ ] T036 Verify caching reduces Core calls

---

## Dependencies

```
T001-T002 (parallel)
     │
     ▼
T003-T010 (US-1.1) ──► T010 depends on T003-T009
     │
     ▼
T011-T014 (US-1.2)
     │
     ▼
T015-T019 (US-1.3) ──► depends on T011-T014
     │
     ▼
T020-T025 (US-1.4) ──► depends on T015-T019
     │
     ▼
T026-T029 (US-1.5) ──► depends on T020-T025
     │
     ▼
T030-T036 (Tests)
```

---

## Acceptance Checklist

- [ ] Invalid token returns 401 `INVALID_TOKEN`
- [ ] Expired token returns 401 `TOKEN_EXPIRED`
- [ ] tenant_member returns 403 `TENANT_MEMBER_DENIED`
- [ ] super_admin passes `require_super_admin()`
- [ ] org_admin passes `require_org_admin(org_id)` for their org
- [ ] tenant_admin passes `require_tenant_admin(tenant_id)` for their tenant
- [ ] AuthZ decisions cached in Redis
- [ ] Cache hit skips Core call
- [ ] Core unreachable returns 503 `AUTHZ_SERVICE_UNAVAILABLE`
