# User Stories — EPIC 7: Dashboard APIs

**Epic**: [epic.md](./epic.md)
**User Personas**: super_admin, org_admin, tenant_admin
**Total Stories**: 5
**Total Points**: 11

---

## US-7.1: Global Dashboard

**As a** super_admin,
**I want** to see system-wide metrics,
**So that** I can monitor platform health and usage.

### Acceptance Criteria
- [ ] `GET /v1/dashboard` returns global metrics (super_admin only)
- [ ] Includes: totals for orgs, tenants, subscriptions, apps
- [ ] Includes: subscriptions by status and by app
- [ ] Includes: trials expiring soon count
- [ ] Includes: recent activity (7 days)
- [ ] Includes: sync_status summary

### Files to Create
- `src/api/v1/dashboard.py`
- `src/services/dashboard_service.py`
- `src/schemas/dashboard.py`

**Priority**: P2
**Points**: 3

---

## US-7.2: Organization Dashboard

**As an** org_admin,
**I want** to see organization-level metrics,
**So that** I can monitor my organization's usage.

### Acceptance Criteria
- [ ] `GET /v1/dashboard/organizations/{org_id}` returns org metrics
- [ ] super_admin can view any org
- [ ] org_admin and tenant_admin can view their org only
- [ ] Includes: tenant and subscription counts
- [ ] Includes: subscriptions by status and app
- [ ] Includes: list of tenants with subscription counts

**Priority**: P2
**Points**: 2

---

## US-7.3: Tenant Dashboard

**As a** tenant_admin,
**I want** to see tenant-level metrics,
**So that** I can monitor my tenant's subscriptions.

### Acceptance Criteria
- [ ] `GET /v1/dashboard/tenants/{tenant_id}` returns tenant metrics
- [ ] super_admin can view any tenant
- [ ] org_admin can view tenants in their org
- [ ] tenant_admin can view their own tenant
- [ ] Includes: tenant details and subscription list
- [ ] Includes: active_app_keys array

**Priority**: P2
**Points**: 2

---

## US-7.4: Trial Report

**As an** org_admin,
**I want** to see trials expiring soon,
**So that** I can follow up on conversions.

### Acceptance Criteria
- [ ] `GET /v1/dashboard/trials` returns expiring trials
- [ ] Filter by days threshold (default 3, max 14)
- [ ] Filter by org_id
- [ ] Scoped by role (super_admin=all, org_admin=org, tenant_admin=tenant)
- [ ] Includes: tenant, org, app details, days_remaining

**Priority**: P2
**Points**: 2

---

## US-7.5: Sync Status Report

**As a** super_admin,
**I want** to see tenant sync status,
**So that** I can identify and resolve sync issues.

### Acceptance Criteria
- [ ] `GET /v1/dashboard/sync-status` returns sync status report (super_admin only)
- [ ] Includes: summary counts by sync_status
- [ ] Filter by status (pending, failed)
- [ ] Includes: list of pending and failed tenants

**Priority**: P2
**Points**: 2

---

## Story Dependencies

```
US-7.1 (Global Dashboard)
         │
         ├──► US-7.2 (Org Dashboard)
         │          │
         │          └──► US-7.3 (Tenant Dashboard)
         │
         ├──► US-7.4 (Trial Report)
         │
         └──► US-7.5 (Sync Report)
```
