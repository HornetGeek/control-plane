# User Stories — EPIC 4: Organizations Management

**Epic**: [epic.md](./epic.md)
**User Personas**: super_admin, org_admin, tenant_admin
**Total Stories**: 6
**Total Points**: 9

---

## US-4.1: List Organizations

**As an** org_admin or tenant_admin,
**I want** to view organizations I have access to,
**So that** I can navigate my organizational context.

### Acceptance Criteria
- [ ] `GET /v1/organizations` returns paginated list
- [ ] super_admin sees all organizations
- [ ] org_admin/tenant_admin sees only their organization
- [ ] Filter by status, search by name
- [ ] Response includes tenant_count

### Files to Create
- `src/api/v1/organizations.py`
- `src/services/organization_service.py`
- `src/schemas/organization.py`

**Priority**: P1
**Points**: 2

---

## US-4.2: Get Organization

**As an** org_admin or tenant_admin,
**I want** to view details of an organization,
**So that** I can understand the organizational context.

### Acceptance Criteria
- [ ] `GET /v1/organizations/{org_id}` returns single organization
- [ ] Returns 403 with `ORG_ACCESS_DENIED` if not authorized for org
- [ ] Response includes tenant_count

**Priority**: P1
**Points**: 1

---

## US-4.3: Create Organization

**As a** super_admin,
**I want** to create new organizations,
**So that** new customers can be onboarded.

### Acceptance Criteria
- [ ] `POST /v1/organizations` creates new organization (super_admin only)
- [ ] Returns 409 with `ORG_NAME_EXISTS` if name already used
- [ ] Triggers Core sync (stubbed for MVP)
- [ ] Returns 201 with created organization

**Priority**: P1
**Points**: 2

---

## US-4.4: Update Organization

**As an** org_admin,
**I want** to update my organization details,
**So that** I can keep information current.

### Acceptance Criteria
- [ ] `PATCH /v1/organizations/{org_id}` updates organization
- [ ] super_admin can update any org
- [ ] org_admin can only update their own org
- [ ] tenant_admin receives 403
- [ ] Returns 200 with updated organization

**Priority**: P1
**Points**: 2

---

## US-4.5: Delete Organization

**As a** super_admin,
**I want** to remove organizations,
**So that** offboarded customers are cleaned up.

### Acceptance Criteria
- [ ] `DELETE /v1/organizations/{org_id}` soft-deletes organization (super_admin only)
- [ ] Returns 409 with `ORG_HAS_TENANTS` if active tenants exist
- [ ] Returns 204 on success

**Priority**: P1
**Points**: 1

---

## US-4.6: Restore Organization

**As a** super_admin,
**I want** to restore deleted organizations,
**So that** I can recover from accidental deletions.

### Acceptance Criteria
- [ ] `POST /v1/organizations/{org_id}/restore` restores soft-deleted organization
- [ ] Returns 200 with restored organization

**Priority**: P2
**Points**: 1

---

## Story Dependencies

```
US-4.1 (List) ──► US-4.2 (Get)
        │
        └──► US-4.3 (Create)
                  │
                  └──► US-4.4 (Update)
                           │
                           ├──► US-4.5 (Delete)
                           │         │
                           │         └──► US-4.6 (Restore)
```
