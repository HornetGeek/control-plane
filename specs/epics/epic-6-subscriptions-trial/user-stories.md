# User Stories — EPIC 6: Subscriptions + 14-Day Trial

**Epic**: [epic.md](./epic.md)
**User Personas**: super_admin, org_admin, tenant_admin
**Total Stories**: 9
**Total Points**: 14

---

## US-6.1: List Subscriptions

**As an** org_admin or tenant_admin,
**I want** to view subscriptions,
**So that** I can track what applications are being used.

### Acceptance Criteria
- [ ] `GET /v1/subscriptions` returns paginated list
- [ ] super_admin sees all
- [ ] org_admin sees subscriptions in their org
- [ ] tenant_admin sees subscriptions for their tenant
- [ ] Filter by tenant_id, app_id, status
- [ ] `trial_expiring=true` filters trials expiring within 3 days
- [ ] Response includes tenant_name, app_name, days_remaining

### Files to Create
- `src/api/v1/subscriptions.py`
- `src/services/subscription_service.py`
- `src/schemas/subscription.py`

**Priority**: P1
**Points**: 2

---

## US-6.2: Get Subscription

**As an** org_admin or tenant_admin,
**I want** to view subscription details,
**So that** I can understand the subscription status.

### Acceptance Criteria
- [ ] `GET /v1/subscriptions/{subscription_id}` returns single subscription
- [ ] Returns 403 if not authorized
- [ ] Response includes all details including days_remaining

**Priority**: P1
**Points**: 1

---

## US-6.3: Create Subscription (Trial)

**As an** org_admin or tenant_admin,
**I want** to subscribe a tenant to an application,
**So that** the tenant can use the application.

### Acceptance Criteria
- [ ] `POST /v1/subscriptions` creates 14-day trial subscription
- [ ] super_admin can create for any tenant
- [ ] org_admin can create for tenants in their org
- [ ] tenant_admin can create for their own tenant
- [ ] status defaults to "trial"
- [ ] trial_ends_at auto-set to now + 14 days
- [ ] Returns 409 with `SUBSCRIPTION_EXISTS` if tenant+app already subscribed
- [ ] Returns 400 with `APP_DISABLED` or `TENANT_DISABLED` if disabled
- [ ] Returns 201 with created subscription

**Priority**: P1
**Points**: 3

---

## US-6.4: Activate Subscription

**As an** org_admin,
**I want** to activate a trial subscription,
**So that** the tenant continues using the application after trial.

### Acceptance Criteria
- [ ] `POST /v1/subscriptions/{subscription_id}/activate` converts trial to active
- [ ] super_admin can activate any subscription
- [ ] org_admin can activate subscriptions in their org
- [ ] Returns 400 with `TRIAL_EXPIRED` if trial already expired
- [ ] Returns 200 with activated subscription

**Priority**: P1
**Points**: 2

---

## US-6.5: Disable Subscription

**As an** org_admin,
**I want** to disable a subscription,
**So that** access can be suspended without deletion.

### Acceptance Criteria
- [ ] `POST /v1/subscriptions/{subscription_id}/disable` sets status to disabled
- [ ] super_admin can disable any subscription
- [ ] org_admin can disable subscriptions in their org
- [ ] Returns 200 with disabled subscription

**Priority**: P1
**Points**: 1

---

## US-6.6: Re-enable Subscription

**As an** org_admin,
**I want** to re-enable a disabled subscription,
**So that** access can be restored.

### Acceptance Criteria
- [ ] `POST /v1/subscriptions/{subscription_id}/enable` sets status to active
- [ ] Re-enabling expired trial requires activation
- [ ] Returns 200 with enabled subscription

**Priority**: P1
**Points**: 1

---

## US-6.7: Delete Subscription

**As an** org_admin,
**I want** to remove a subscription,
**So that** it no longer appears in listings.

### Acceptance Criteria
- [ ] `DELETE /v1/subscriptions/{subscription_id}` soft-deletes subscription
- [ ] super_admin can delete any subscription
- [ ] org_admin can delete subscriptions in their org
- [ ] Returns 204 on success

**Priority**: P1
**Points**: 1

---

## US-6.8: Restore Subscription

**As a** super_admin,
**I want** to restore deleted subscriptions,
**So that** I can recover from accidental deletions.

### Acceptance Criteria
- [ ] `POST /v1/subscriptions/{subscription_id}/restore` restores soft-deleted subscription
- [ ] Returns 200 with restored subscription

**Priority**: P2
**Points**: 1

---

## US-6.9: Trial Expiration Check

**As a** platform administrator,
**I want** expired trials to be automatically disabled,
**So that** access is revoked when trials end.

### Acceptance Criteria
- [ ] `POST /v1/admin/check-trials` triggers expiration check (super_admin only)
- [ ] Finds subscriptions where status=trial AND trial_ends_at < now
- [ ] Sets status to disabled for expired trials
- [ ] Logs all expirations
- [ ] Returns count of expired trials disabled

### Files to Create
- `src/api/v1/admin.py`
- `src/services/trial_service.py`

**Priority**: P1
**Points**: 2

---

## Story Dependencies

```
US-6.1 (List) ──► US-6.2 (Get)
        │
        └──► US-6.3 (Create)
                  │
                  ├──► US-6.4 (Activate)
                  │
                  ├──► US-6.5 (Disable) ──► US-6.6 (Enable)
                  │
                  └──► US-6.7 (Delete) ──► US-6.8 (Restore)

US-6.9 (Trial Check) ──► depends on US-6.3
```
