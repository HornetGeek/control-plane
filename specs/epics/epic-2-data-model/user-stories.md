# User Stories — EPIC 2: CP Registry Data Model

**Epic**: [epic.md](./epic.md)
**User Persona**: Developer
**Total Stories**: 3
**Total Points**: 8

---

## US-2.1: Entities + Migrations

**As a** developer,
**I want** SQLAlchemy models for all CP entities with Alembic migrations,
**So that** I can persist and query application, organization, tenant, and subscription data.

### Acceptance Criteria
- [ ] Application model with UUID PK, app_key, name, base_url, status
- [ ] Organization model with UUID PK, name, status
- [ ] Tenant model with UUID PK, org_id FK, name, name_normalized, status, sync_status
- [ ] Subscription model with UUID PK, tenant_id FK, app_id FK, status, trial_ends_at
- [ ] All entities have created_at, updated_at timestamps
- [ ] Migration creates all tables with correct constraints and indexes

### Files to Create
- `src/models/__init__.py`
- `src/models/application.py`
- `src/models/organization.py`
- `src/models/tenant.py`
- `src/models/subscription.py`
- `alembic/versions/xxx_initial_schema.py`

**Priority**: P0
**Points**: 5

---

## US-2.2: Soft Delete + Status

**As a** platform administrator,
**I want** entities to support soft deletion and status management,
**So that** data can be recovered and temporarily suspended.

### Acceptance Criteria
- [ ] All entities have `deleted_at` timestamp field (NULL = not deleted)
- [ ] All entities have `status` field ("active" | "disabled")
- [ ] Default queries exclude soft-deleted records
- [ ] `with_deleted()` query method available for admin use
- [ ] Soft delete preserves record for audit/recovery

### Files to Create/Modify
- `src/models/base.py` (mixins for soft delete, timestamps)
- `src/models/` (add soft delete methods to each model)

**Priority**: P0
**Points**: 2

---

## US-2.3: Sync Status Field

**As a** developer,
**I want** a sync_status field on tenants,
**So that** I can track Core synchronization state.

### Acceptance Criteria
- [ ] `sync_status` field: "synced" | "pending" | "failed"
- [ ] Default value is "pending" on creation
- [ ] Field updated on sync success/failure

### Files to Modify
- `src/models/tenant.py`

**Priority**: P1
**Points**: 1

---

## Story Dependencies

```
US-2.1 (Entities)
     │
     ▼
US-2.2 (Soft Delete)
     │
     ▼
US-2.3 (Sync Status)
```
