# Tasks — EPIC 5: Tenants Management + Sync

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 26
**Estimated Time**: 3 days

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Schemas

- [ ] T001 [P] Create `src/schemas/tenant.py` with TenantCreate schema
- [ ] T002 [P] Create `src/schemas/tenant.py` with TenantUpdate schema
- [ ] T003 [P] Create `src/schemas/tenant.py` with TenantResponse schema (includes org_name, subscription_count)
- [ ] T004 [P] Create `src/schemas/tenant.py` with TenantListResponse schema

---

## Phase 2: Service Layer

- [ ] T005 Create `src/services/tenant_service.py` with TenantService class
- [ ] T006 Implement `list_tenants()` with role-based scoping (super_admin/org_admin/tenant_admin)
- [ ] T007 Implement `get_tenant()` with authorization check
- [ ] T008 Implement `create_tenant()` with org_id validation
- [ ] T009 Add name uniqueness check per org (case-insensitive via name_normalized)
- [ ] T010 Auto-generate `name_normalized` as lowercase on create
- [ ] T011 Implement `update_tenant()` with role-based field restrictions
- [ ] T012 Add tenant_admin restriction (name only, not status)
- [ ] T013 Implement `delete_tenant()` with subscription check
- [ ] T014 Implement `restore_tenant()` (super_admin only)
- [ ] T015 Implement `sync_tenant()` stub that sets sync_status to "synced"
- [ ] T016 Add `get_subscription_count()` helper method

---

## Phase 3: API Endpoints

- [ ] T017 Create `src/api/v1/tenants.py` router
- [ ] T018 Implement `GET /v1/tenants` with scoping and filters (org_id, status, sync_status, search)
- [ ] T019 Implement `GET /v1/tenants/{tenant_id}` with auth check
- [ ] T020 Implement `POST /v1/tenants` with role check (super_admin/org_admin)
- [ ] T021 Implement `PATCH /v1/tenants/{tenant_id}` with role-based field access
- [ ] T022 Implement `DELETE /v1/tenants/{tenant_id}` with role check
- [ ] T023 Implement `POST /v1/tenants/{tenant_id}/restore` (super_admin only)
- [ ] T024 Implement `POST /v1/tenants/{tenant_id}/sync` with role check
- [ ] T025 Register tenants router in `src/api/v1/router.py`

---

## Phase 4: Tests

- [ ] T026 [P] Create `tests/unit/services/test_tenant_service.py`
- [ ] T027 [P] Create `tests/unit/api/test_tenants.py`
- [ ] T028 [P] Create `tests/integration/test_tenants_crud.py`
- [ ] T029 Create test for name uniqueness per org (case-insensitive)

---

## Dependencies

```
T001-T004 (parallel) ──► Schemas
        │
        ▼
    T005-T016 ──► Service layer
        │
        ▼
    T017-T025 ──► API endpoints
        │
        ▼
    T026-T029 (parallel) ──► Tests
```

---

## Acceptance Checklist

- [ ] List scoped by role
- [ ] Get returns single tenant if authorized
- [ ] Create succeeds with unique name in org
- [ ] Create fails with duplicate name (case-insensitive)
- [ ] name_normalized auto-generated
- [ ] Update succeeds based on role permissions
- [ ] tenant_admin can only update name
- [ ] Delete soft-deletes with subscription check
- [ ] Restore recovers soft-deleted tenant (super_admin)
- [ ] Sync endpoint sets sync_status to synced
- [ ] subscription_count included in responses
