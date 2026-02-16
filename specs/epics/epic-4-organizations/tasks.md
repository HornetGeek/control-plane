# Tasks — EPIC 4: Organizations Management

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 22
**Estimated Time**: 2 days

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Schemas

- [ ] T001 [P] Create `src/schemas/organization.py` with OrganizationCreate schema
- [ ] T002 [P] Create `src/schemas/organization.py` with OrganizationUpdate schema
- [ ] T003 [P] Create `src/schemas/organization.py` with OrganizationResponse schema (includes tenant_count)
- [ ] T004 [P] Create `src/schemas/organization.py` with OrganizationListResponse schema

---

## Phase 2: Service Layer

- [ ] T005 Create `src/services/organization_service.py` with OrganizationService class
- [ ] T006 Implement `list_organizations()` with role-based scoping
- [ ] T007 Implement `get_organization()` with authorization check
- [ ] T008 Implement `create_organization()` with name uniqueness check
- [ ] T009 Implement `update_organization()` with role-based access (super_admin/org_admin)
- [ ] T010 Implement `delete_organization()` with tenant check
- [ ] T011 Implement `restore_organization()` for soft-deleted orgs
- [ ] T012 Add `get_tenant_count()` helper method
- [ ] T013 Add Core sync trigger stub on create

---

## Phase 3: API Endpoints

- [ ] T014 Create `src/api/v1/organizations.py` router
- [ ] T015 Implement `GET /v1/organizations` with scoping
- [ ] T016 Implement `GET /v1/organizations/{org_id}` with auth check
- [ ] T017 Implement `POST /v1/organizations` (super_admin only)
- [ ] T018 Implement `PATCH /v1/organizations/{org_id}` with role check
- [ ] T019 Implement `DELETE /v1/organizations/{org_id}` (super_admin only)
- [ ] T020 Implement `POST /v1/organizations/{org_id}/restore` (super_admin only)
- [ ] T021 Register organizations router in `src/api/v1/router.py`

---

## Phase 4: Tests

- [ ] T022 [P] Create `tests/unit/services/test_organization_service.py`
- [ ] T023 [P] Create `tests/unit/api/test_organizations.py`
- [ ] T024 [P] Create `tests/integration/test_organizations_crud.py`

---

## Dependencies

```
T001-T004 (parallel) ──► Schemas
        │
        ▼
    T005-T013 ──► Service layer
        │
        ▼
    T014-T021 ──► API endpoints
        │
        ▼
    T022-T024 (parallel) ──► Tests
```

---

## Acceptance Checklist

- [ ] List scoped by role (super_admin=all, org_admin/tenant_admin=own org)
- [ ] Get returns single org if authorized
- [ ] Create succeeds for super_admin
- [ ] Create returns 409 for duplicate name
- [ ] Update succeeds for super_admin and org_admin (own org)
- [ ] Update returns 403 for tenant_admin
- [ ] Delete soft-deletes for super_admin
- [ ] Delete returns 409 if tenants exist
- [ ] Restore recovers soft-deleted org
- [ ] tenant_count included in responses
