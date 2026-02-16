# User Stories — EPIC 5: Tenants Management + Sync

**Epic**: [epic.md](./epic.md)
**User Personas**: super_admin, org_admin, tenant_admin
**Total Stories**: 7
**Total Points**: 12

---

## US-5.1: List Tenants

**As an** org_admin,
**I want** to view tenants in my organization,
**So that** I can manage branches/locations.

### Acceptance Criteria
- [ ] `GET /v1/tenants` returns paginated list
- [ ] super_admin sees all (can filter by org_id)
- [ ] org_admin sees tenants in their org only
- [ ] tenant_admin sees only their tenant
- [ ] Filter by status, sync_status, search by name
- [ ] Response includes org_name, subscription_count

### Files to Create
- `src/api/v1/tenants.py`
- `src/services/tenant_service.py`
- `src/schemas/tenant.py`

**Priority**: P1
**Points**: 2

---

## US-5.2: Get Tenant

**As an** org_admin or tenant_admin,
**I want** to view tenant details,
**So that** I can understand the tenant context.

### Acceptance Criteria
- [ ] `GET /v1/tenants/{tenant_id}` returns single tenant
- [ ] Returns 403 with `TENANT_ACCESS_DENIED` if not authorized
- [ ] Response includes org_name, subscription_count, sync_status

**Priority**: P1
**Points**: 1

---

## US-5.3: Create Tenant

**As an** org_admin,
**I want** to create new tenants in my organization,
**So that** new branches/locations can be added.

### Acceptance Criteria
- [ ] `POST /v1/tenants` creates new tenant
- [ ] super_admin can create in any org
- [ ] org_admin can create only in their org
- [ ] Returns 409 with `TENANT_NAME_EXISTS` if name exists in org (case-insensitive)
- [ ] name_normalized auto-generated as lowercase
- [ ] sync_status set to "pending"
- [ ] Returns 201 with created tenant

**Priority**: P1
**Points**: 3

---

## US-5.4: Update Tenant

**As an** org_admin or tenant_admin,
**I want** to update tenant details,
**So that** I can keep information current.

### Acceptance Criteria
- [ ] `PATCH /v1/tenants/{tenant_id}` updates tenant
- [ ] super_admin can update any tenant
- [ ] org_admin can update tenants in their org
- [ ] tenant_admin can only update name (not status) of their own tenant
- [ ] Returns 200 with updated tenant

**Priority**: P1
**Points**: 2

---

## US-5.5: Delete Tenant

**As an** org_admin,
**I want** to remove tenants,
**So that** closed branches are cleaned up.

### Acceptance Criteria
- [ ] `DELETE /v1/tenants/{tenant_id}` soft-deletes tenant
- [ ] super_admin can delete any tenant
- [ ] org_admin can delete tenants in their org
- [ ] Returns 409 with `TENANT_HAS_SUBSCRIPTIONS` if active subscriptions exist
- [ ] Returns 204 on success

**Priority**: P1
**Points**: 1

---

## US-5.6: Restore Tenant

**As a** super_admin,
**I want** to restore deleted tenants,
**So that** I can recover from accidental deletions.

### Acceptance Criteria
- [ ] `POST /v1/tenants/{tenant_id}/restore` restores soft-deleted tenant (super_admin only)
- [ ] Returns 200 with restored tenant

**Priority**: P2
**Points**: 1

---

## US-5.7: Sync Tenant with Core

**As an** org_admin,
**I want** to manually trigger tenant sync with Core,
**So that** I can resolve sync issues.

### Acceptance Criteria
- [ ] `POST /v1/tenants/{tenant_id}/sync` triggers Core sync
- [ ] super_admin can sync any tenant
- [ ] org_admin can sync tenants in their org
- [ ] Returns 200 with updated sync_status and synced_at timestamp
- [ ] MVP: stub that sets status to "synced" and logs action

**Priority**: P2
**Points**: 2

---

## Story Dependencies

```
US-5.1 (List) ──► US-5.2 (Get)
        │
        └──► US-5.3 (Create)
                  │
                  └──► US-5.4 (Update)
                           │
                           ├──► US-5.5 (Delete)
                           │         │
                           │         └──► US-5.6 (Restore)
                           │
                           └──► US-5.7 (Sync)
```
