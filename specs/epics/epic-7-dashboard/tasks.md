# Tasks — EPIC 7: Dashboard APIs

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 20
**Estimated Time**: 2 days

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Schemas

- [ ] T001 [P] Create `src/schemas/dashboard.py` with GlobalDashboardResponse schema
- [ ] T002 [P] Create `src/schemas/dashboard.py` with OrgDashboardResponse schema
- [ ] T003 [P] Create `src/schemas/dashboard.py` with TenantDashboardResponse schema
- [ ] T004 [P] Create `src/schemas/dashboard.py` with TrialReportResponse schema
- [ ] T005 [P] Create `src/schemas/dashboard.py` with SyncStatusResponse schema

---

## Phase 2: Service Layer

- [ ] T006 Create `src/services/dashboard_service.py` with DashboardService class
- [ ] T007 Implement `get_global_dashboard()` with all aggregations
- [ ] T008 Implement `get_org_dashboard()` with org-scoped aggregations
- [ ] T009 Implement `get_tenant_dashboard()` with tenant-scoped data
- [ ] T010 Implement `get_trial_report()` with days_remaining calculation
- [ ] T011 Implement `get_sync_status_report()` for pending/failed tenants
- [ ] T012 Add aggregation helper: `count_by_status()`
- [ ] T013 Add aggregation helper: `count_by_app()`
- [ ] T014 Add aggregation helper: `count_recent_created()` (7 days)

---

## Phase 3: API Endpoints

- [ ] T015 Create `src/api/v1/dashboard.py` router
- [ ] T016 Implement `GET /v1/dashboard` (super_admin only)
- [ ] T017 Implement `GET /v1/dashboard/organizations/{org_id}` with role scoping
- [ ] T018 Implement `GET /v1/dashboard/tenants/{tenant_id}` with role scoping
- [ ] T019 Implement `GET /v1/dashboard/trials` with role scoping and filters
- [ ] T020 Implement `GET /v1/dashboard/sync-status` (super_admin only)
- [ ] T021 Register dashboard router in `src/api/v1/router.py`

---

## Phase 4: Tests

- [ ] T022 [P] Create `tests/unit/services/test_dashboard_service.py`
- [ ] T023 [P] Create `tests/unit/api/test_dashboard.py`
- [ ] T024 [P] Create `tests/integration/test_dashboard.py`

---

## Dependencies

```
T001-T005 (parallel) ──► Schemas
        │
        ▼
    T006-T014 ──► Service layer
        │
        ▼
    T015-T021 ──► API endpoints
        │
        ▼
    T022-T024 (parallel) ──► Tests
```

---

## Acceptance Checklist

- [ ] Global dashboard returns all metrics (super_admin)
- [ ] Org dashboard returns org-scoped metrics
- [ ] Org dashboard accessible to org members
- [ ] Tenant dashboard returns tenant-scoped metrics
- [ ] Tenant dashboard accessible to tenant members
- [ ] Trial report lists expiring trials with days_remaining
- [ ] Trial report scoped by role
- [ ] Sync status report shows pending/failed tenants (super_admin)
- [ ] Soft-deleted entities excluded from counts
- [ ] Response time < 500ms
