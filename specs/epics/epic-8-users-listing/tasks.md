# Tasks — EPIC 8: Users Listing (via Mock Core)

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 18
**Estimated Time**: 2 days

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Schemas

- [ ] T001 [P] Create `src/schemas/user.py` with UserResponse schema
- [ ] T002 [P] Create `src/schemas/user.py` with UserListResponse schema
- [ ] T003 [P] Create `src/schemas/user.py` with CurrentUserResponse schema (includes tenants, permissions)

---

## Phase 2: Mock Core Users Extension

- [ ] T004 Extend `src/clients/mock_core.py` with user scenarios
- [ ] T005 Add `list_users()` method with scoping (global/org/tenant)
- [ ] T006 Add `get_user_by_sub()` method
- [ ] T007 Add `get_current_user()` method with tenant details

---

## Phase 3: Service Layer

- [ ] T008 Create `src/services/user_service.py` with UserService class
- [ ] T009 Implement `list_users_global()` with role filter support
- [ ] T010 Implement `list_users_by_org()` with role-based scoping
- [ ] T011 Implement `list_users_by_tenant()` with role-based scoping
- [ ] T012 Implement `get_current_user()` with full profile

---

## Phase 4: API Endpoints

- [ ] T013 Create `src/api/v1/users.py` router
- [ ] T014 Implement `GET /v1/users` (super_admin only) with filters
- [ ] T015 Add `GET /v1/organizations/{org_id}/users` to organizations router
- [ ] T016 Add `GET /v1/tenants/{tenant_id}/users` to tenants router
- [ ] T017 Implement `GET /v1/users/me` (any authenticated user)
- [ ] T018 Register users router in `src/api/v1/router.py`

---

## Phase 5: Tests

- [ ] T019 [P] Create `tests/unit/services/test_user_service.py`
- [ ] T020 [P] Create `tests/unit/api/test_users.py`
- [ ] T021 [P] Create `tests/integration/test_users_listing.py`

---

## Dependencies

```
T001-T003 (parallel) ──► Schemas
        │
        ▼
    T004-T007 ──► Mock Core extension
        │
        ▼
    T008-T012 ──► Service layer
        │
        ▼
    T013-T018 ──► API endpoints
        │
        ▼
    T019-T021 (parallel) ──► Tests
```

---

## Acceptance Checklist

- [ ] Global user list returns all mock users (super_admin)
- [ ] Global list supports role, org_id, tenant_id filters
- [ ] Global list supports search by email/name
- [ ] Org user list scoped to org members
- [ ] Org user list filtered by tenant for tenant_admin
- [ ] Tenant user list scoped to tenant members
- [ ] `/users/me` returns current user with tenants and permissions
- [ ] Pagination works correctly
- [ ] Core unavailable returns 503
