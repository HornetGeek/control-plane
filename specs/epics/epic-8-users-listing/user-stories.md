# User Stories — EPIC 8: Users Listing (via Mock Core)

**Epic**: [epic.md](./epic.md)
**User Personas**: super_admin, org_admin, tenant_admin, authenticated user
**Total Stories**: 4
**Total Points**: 8

---

## US-8.1: List Users (Global)

**As a** super_admin,
**I want** to list all users in the platform,
**So that** I can manage user accounts.

### Acceptance Criteria
- [ ] `GET /v1/users` returns paginated user list (super_admin only)
- [ ] Filter by role, org_id, tenant_id
- [ ] Search by email or name (case-insensitive)
- [ ] Data from mock Core client
- [ ] Includes: id, email, name, effective_role, org_id, tenant_ids

### Files to Create
- `src/api/v1/users.py`
- `src/services/user_service.py`
- `src/schemas/user.py`

**Priority**: P2
**Points**: 2

---

## US-8.2: List Users by Organization

**As an** org_admin,
**I want** to list users in my organization,
**So that** I can manage organizational members.

### Acceptance Criteria
- [ ] `GET /v1/organizations/{org_id}/users` returns org users
- [ ] super_admin can list any org
- [ ] org_admin can list their org only
- [ ] tenant_admin can list their org (but only their tenants)
- [ ] Filter by role, tenant_id, search

**Priority**: P2
**Points**: 2

---

## US-8.3: List Users by Tenant

**As a** tenant_admin,
**I want** to list users in my tenant,
**So that** I can see tenant members.

### Acceptance Criteria
- [ ] `GET /v1/tenants/{tenant_id}/users` returns tenant users
- [ ] super_admin can list any tenant
- [ ] org_admin can list tenants in their org
- [ ] tenant_admin can list their own tenant only
- [ ] Filter by search

**Priority**: P2
**Points**: 2

---

## US-8.4: Get Current User

**As an** authenticated user,
**I want** to view my profile,
**So that** I can see my roles and permissions.

### Acceptance Criteria
- [ ] `GET /v1/users/me` returns current user profile
- [ ] Available to all authenticated users
- [ ] Includes: id, email, name, effective_role, org_id
- [ ] Includes: tenant_ids with tenant names
- [ ] Includes: permissions array

**Priority**: P1
**Points**: 2

---

## Story Dependencies

```
US-8.1 (Global Users)
         │
         ├──► US-8.2 (Org Users)
         │          │
         │          └──► US-8.3 (Tenant Users)
         │
         └──► US-8.4 (Current User) [independent]
```
