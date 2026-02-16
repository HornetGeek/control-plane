# Tasks — EPIC 3: Applications Catalog

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 20
**Estimated Time**: 2 days

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Schemas

- [ ] T001 [P] Create `src/schemas/application.py` with ApplicationCreate schema
- [ ] T002 [P] Create `src/schemas/application.py` with ApplicationUpdate schema
- [ ] T003 [P] Create `src/schemas/application.py` with ApplicationResponse schema
- [ ] T004 [P] Create `src/schemas/application.py` with ApplicationListResponse schema

---

## Phase 2: Service Layer

- [ ] T005 Create `src/services/__init__.py`
- [ ] T006 Create `src/services/application_service.py` with ApplicationService class
- [ ] T007 Implement `list_applications()` with pagination and filtering
- [ ] T008 Implement `get_application()` supporting ID or app_key lookup
- [ ] T009 Implement `create_application()` with app_key validation
- [ ] T010 Implement `update_application()` with partial update support
- [ ] T011 Implement `delete_application()` with soft delete
- [ ] T012 Implement `restore_application()` for soft-deleted apps
- [ ] T013 Add subscription check before delete in `delete_application()`

---

## Phase 3: API Endpoints

- [ ] T014 Create `src/api/v1/applications.py` router
- [ ] T015 Implement `GET /v1/applications` with pagination
- [ ] T016 Implement `GET /v1/applications/{app_id_or_key}`
- [ ] T017 Implement `POST /v1/applications` with super_admin check
- [ ] T018 Implement `PATCH /v1/applications/{app_id}` with super_admin check
- [ ] T019 Implement `DELETE /v1/applications/{app_id}` with super_admin check
- [ ] T020 Implement `POST /v1/applications/{app_id}/restore` with super_admin check
- [ ] T021 Register applications router in `src/api/v1/router.py`

---

## Phase 4: Tests

- [ ] T022 [P] Create `tests/unit/services/test_application_service.py`
- [ ] T023 [P] Create `tests/unit/api/test_applications.py`
- [ ] T024 [P] Create `tests/integration/test_applications_crud.py`

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

- [ ] List returns paginated applications
- [ ] Get by UUID works
- [ ] Get by app_key works
- [ ] Create succeeds for super_admin
- [ ] Create returns 409 for duplicate app_key
- [ ] Update succeeds for super_admin
- [ ] Delete soft-deletes for super_admin
- [ ] Delete returns 409 if subscriptions exist
- [ ] Restore recovers soft-deleted app
- [ ] Non-super_admin receives 403 for CUD
