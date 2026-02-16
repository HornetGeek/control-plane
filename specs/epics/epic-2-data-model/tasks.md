# Tasks — EPIC 2: CP Registry Data Model

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 18
**Estimated Time**: 2 days
**Status**: ✅ Complete

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Base Models Setup (US-2.2)

- [X] T001 Create `src/models/__init__.py`
- [X] T002 Create `src/models/base.py` with TimestampMixin
- [X] T003 Create `src/models/base.py` with SoftDeleteMixin
- [X] T004 Add `with_deleted()` query method to SoftDeleteMixin
- [X] T005 Update `src/db/base.py` to use custom base class

---

## Phase 2: Entity Models (US-2.1)

- [X] T006 [P] Create `src/models/application.py` with Application model
- [X] T007 [P] Create `src/models/organization.py` with Organization model
- [X] T008 [P] Create `src/models/tenant.py` with Tenant model
- [X] T009 [P] Create `src/models/subscription.py` with Subscription model

---

## Phase 3: Model Details

- [X] T010 Add relationships: Tenant.org → Organization, Subscription.tenant → Tenant
- [X] T011 Add relationships: Subscription.app → Application
- [X] T012 Add `name_normalized` auto-generation in Tenant model
- [X] T013 Add UNIQUE constraint on Tenant(org_id, name_normalized)
- [X] T014 Add UNIQUE constraint on Subscription(tenant_id, app_id)
- [X] T015 Add indexes for foreign keys

---

## Phase 4: Sync Status (US-2.3)

- [X] T016 Add `sync_status` field to Tenant with default "pending"
- [X] T017 Add `synced_at` timestamp field to Tenant

---

## Phase 5: Migration & Tests

- [X] T018 Create Alembic migration: `alembic/versions/001_initial_schema.py`
- [X] T019 Run migration: `docker compose --profile migrate up migrate`
- [X] T020 [P] Create `tests/unit/models/test_entities.py`
- [X] T021 [P] Create `tests/unit/models/test_soft_delete.py`

---

## Dependencies

```
T001 ──► T002-T005
              │
              ▼
    T006-T009 (parallel)
              │
              ▼
        T010-T015
              │
              ▼
        T016-T017
              │
              ▼
        T018-T021
```

---

## Acceptance Checklist

- [X] All migrations run successfully
- [X] UUID PKs generated automatically
- [X] Soft delete works (deleted_at set, excluded from queries)
- [X] `with_deleted()` includes soft-deleted records
- [X] Status field accepts "active" | "disabled"
- [X] Tenant UNIQUE(org_id, name_normalized) enforced
- [X] Subscription UNIQUE(tenant_id, app_id) enforced
- [X] sync_status defaults to "pending"
- [X] Timestamps auto-managed
