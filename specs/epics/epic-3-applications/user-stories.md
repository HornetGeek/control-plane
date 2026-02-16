# User Stories — EPIC 3: Applications Catalog

**Epic**: [epic.md](./epic.md)
**User Personas**: super_admin, org_admin, tenant_admin
**Total Stories**: 6
**Total Points**: 8

---

## US-3.1: List Applications

**As an** org_admin or tenant_admin,
**I want** to view the list of available applications,
**So that** I can see what applications are available for subscription.

### Acceptance Criteria
- [ ] `GET /v1/applications` returns paginated list
- [ ] Filter by status query parameter
- [ ] super_admin can use `include_deleted` parameter
- [ ] Response includes id, app_key, name, base_url, status

### Files to Create
- `src/api/v1/applications.py`
- `src/services/application_service.py`
- `src/schemas/application.py`

**Priority**: P1
**Points**: 2

---

## US-3.2: Get Application

**As an** org_admin or tenant_admin,
**I want** to view details of a specific application,
**So that** I can understand what the application does.

### Acceptance Criteria
- [ ] `GET /v1/applications/{app_id_or_key}` returns single application
- [ ] Supports lookup by UUID or app_key
- [ ] Returns 404 with `APP_NOT_FOUND` if not found

**Priority**: P1
**Points**: 1

---

## US-3.3: Create Application

**As a** super_admin,
**I want** to add new applications to the catalog,
**So that** new services can be offered to organizations.

### Acceptance Criteria
- [ ] `POST /v1/applications` creates new application (super_admin only)
- [ ] Validates app_key format: `^[a-z][a-z0-9_]*$`
- [ ] Validates base_url is valid HTTPS URL
- [ ] Returns 409 with `APP_KEY_EXISTS` if key already used
- [ ] Returns 201 with created application

**Priority**: P1
**Points**: 2

---

## US-3.4: Update Application

**As a** super_admin,
**I want** to update application details,
**So that** I can keep the catalog current.

### Acceptance Criteria
- [ ] `PATCH /v1/applications/{app_id}` updates application (super_admin only)
- [ ] Partial updates supported
- [ ] Returns 200 with updated application

**Priority**: P1
**Points**: 1

---

## US-3.5: Delete Application

**As a** super_admin,
**I want** to remove applications from the catalog,
**So that** discontinued services are no longer available.

### Acceptance Criteria
- [ ] `DELETE /v1/applications/{app_id}` soft-deletes application (super_admin only)
- [ ] Returns 409 with `APP_HAS_SUBSCRIPTIONS` if active subscriptions exist
- [ ] Returns 204 on success

**Priority**: P1
**Points**: 1

---

## US-3.6: Restore Application

**As a** super_admin,
**I want** to restore deleted applications,
**So that** I can recover from accidental deletions.

### Acceptance Criteria
- [ ] `POST /v1/applications/{app_id}/restore` restores soft-deleted application
- [ ] Returns 200 with restored application

**Priority**: P2
**Points**: 1

---

## Story Dependencies

```
US-3.1 (List) ──► US-3.2 (Get)
        │
        └──► US-3.3 (Create)
                  │
                  └──► US-3.4 (Update)
                           │
                           ├──► US-3.5 (Delete)
                           │         │
                           │         └──► US-3.6 (Restore)
```
