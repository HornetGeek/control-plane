# Tasks — EPIC 6: Subscriptions + 14-Day Trial

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 30
**Estimated Time**: 3-4 days

---

## Format: `[ID] [P?] [US] Description`

---

## Phase 1: Schemas

- [ ] T001 [P] Create `src/schemas/subscription.py` with SubscriptionCreate schema
- [ ] T002 [P] Create `src/schemas/subscription.py` with SubscriptionUpdate schema
- [ ] T003 [P] Create `src/schemas/subscription.py` with SubscriptionResponse schema (includes tenant_name, app_name, days_remaining)
- [ ] T004 [P] Create `src/schemas/subscription.py` with SubscriptionListResponse schema

---

## Phase 2: Service Layer

- [ ] T005 Create `src/services/subscription_service.py` with SubscriptionService class
- [ ] T006 Implement `list_subscriptions()` with role-based scoping
- [ ] T007 Add `trial_expiring` filter logic (within 3 days)
- [ ] T008 Implement `get_subscription()` with authorization check
- [ ] T009 Implement `create_subscription()` with 14-day trial logic
- [ ] T010 Auto-set `status` to "trial"
- [ ] T011 Auto-calculate `trial_ends_at` = now + TRIAL_DURATION_DAYS
- [ ] T012 Add tenant+app uniqueness check
- [ ] T013 Add app/tenant enabled validation
- [ ] T014 Implement `activate_subscription()` (trial → active)
- [ ] T015 Implement `disable_subscription()` (any → disabled)
- [ ] T016 Implement `enable_subscription()` (disabled → active, check expired trial)
- [ ] T017 Implement `delete_subscription()` with soft delete
- [ ] T018 Implement `restore_subscription()` (super_admin only)
- [ ] T019 Add `calculate_days_remaining()` helper
- [ ] T020 Implement status transition validation

---

## Phase 3: Trial Expiration (US-6.9)

- [ ] T021 Create `src/services/trial_service.py` with TrialService class
- [ ] T022 Implement `check_expired_trials()` method
- [ ] T023 Create `src/api/v1/admin.py` router
- [ ] T024 Implement `POST /v1/admin/check-trials` endpoint (super_admin only)
- [ ] T025 Register admin router in `src/api/v1/router.py`

---

## Phase 4: API Endpoints

- [ ] T026 Create `src/api/v1/subscriptions.py` router
- [ ] T027 Implement `GET /v1/subscriptions` with scoping and filters
- [ ] T028 Implement `GET /v1/subscriptions/{subscription_id}` with auth check
- [ ] T029 Implement `POST /v1/subscriptions` with role check
- [ ] T030 Implement `POST /v1/subscriptions/{subscription_id}/activate`
- [ ] T031 Implement `POST /v1/subscriptions/{subscription_id}/disable`
- [ ] T032 Implement `POST /v1/subscriptions/{subscription_id}/enable`
- [ ] T033 Implement `DELETE /v1/subscriptions/{subscription_id}`
- [ ] T034 Implement `POST /v1/subscriptions/{subscription_id}/restore` (super_admin only)
- [ ] T035 Register subscriptions router in `src/api/v1/router.py`

---

## Phase 5: Tests

- [ ] T036 [P] Create `tests/unit/services/test_subscription_service.py`
- [ ] T037 [P] Create `tests/unit/services/test_trial_service.py`
- [ ] T038 [P] Create `tests/unit/api/test_subscriptions.py`
- [ ] T039 [P] Create `tests/integration/test_subscriptions_crud.py`

---

## Dependencies

```
T001-T004 (parallel) ──► Schemas
        │
        ▼
    T005-T020 ──► Service layer
        │
        ├──► T021-T025 ──► Trial service + admin endpoint
        │
        └──► T026-T035 ──► API endpoints
                  │
                  ▼
           T036-T039 (parallel) ──► Tests
```

---

## Acceptance Checklist

- [ ] List scoped by role
- [ ] Get returns single subscription if authorized
- [ ] Create starts 14-day trial
- [ ] Create fails for duplicate tenant+app
- [ ] Create fails for disabled app or tenant
- [ ] Activate converts trial to active
- [ ] Activate fails for expired trial
- [ ] Disable sets status to disabled
- [ ] Enable restores to active (unless expired trial)
- [ ] Delete soft-deletes
- [ ] Restore recovers soft-deleted (super_admin)
- [ ] days_remaining calculated correctly
- [ ] Trial check disables expired trials
