# Master Specification: Control Plane MVP (API-only)

**Feature Branch**: `001-control-plane-mvp`
**Created**: 2026-02-09
**Updated**: 2026-02-14
**Status**: Draft
**IdP**: Keycloak (realm: `control-plane`)

## Goal

Build the Control Plane microservice (FastAPI) for a multi-organization, multi-tenant, multi-application SaaS platform where a user selects an app BEFORE login, then authenticates via Keycloak (OIDC), and is provisioned into Org/Tenant with a tenant-level 14-day TRIAL subscription, then launched into the selected app via short-lived Control Plane Launch JWT.

## Actors

- **Anonymous visitor** (pre-login)
- **Authenticated user** (OIDC access token)
- **Roles** (MVP):
  - `org_admin`
  - `tenant_admin`
  - `tenant_member`

## Domain Model (MVP)

- Organization has multiple Tenants (branches)
- Tenant has subscriptions to Apps
- User belongs to exactly ONE Organization
- User can be a member of multiple tenants within that org
- Apps are shared SaaS apps (PACS, ERP) with fixed base URLs

## Key Decisions (Locked)

| Decision | Value |
|----------|-------|
| Pre-login flow | Creates ONLY onboarding session (A2) |
| Pre-login collection | `org_name` and `tenant_name` |
| Same IdP user (sub) in different org | ERROR (blocked) |
| Launch mechanism | Control Plane short-lived Launch JWT (C2) |
| Launch API | Accepts `tenant_id` explicitly |
| Subscription model | Tenant-level, status=trial only (MVP) |
| Trial duration | 14 days |
| OIDC provider | Keycloak |
| OIDC issuer | `http://localhost:18080/realms/control-plane` |
| Token validation | Access token validated; `aud` check enforced |
| Onboarding TTL | 60 minutes |
| Onboarding consumption | Single-use (status field) |
| Tenant uniqueness | `UNIQUE(org_id, tenant_name)` |
| User profile persistence | `{email, name}` from IdP |

## Clarifications

### Session 2026-02-14

| # | Question | Decision |
|---|----------|----------|
| Q1 | Should inactive apps be visible? | Only `status=active` apps |
| Q13 | Observability signals? | Structured logging (JSON) + `/health` endpoint |
| Q14 | Keycloak unreachable behavior? | Return 503 with "IdP unavailable" message |
| Q2 | Should app descriptions be included? | Minimal fields only (MVP) |
| Q3 | Name validation? | Alphanumeric + spaces/hyphens, 3-50 chars |
| Q4 | org_name uniqueness? | Globally unique |
| Q5 | Expired session handling? | Delete on access attempt |
| Q6 | Returning user response? | Access token + refresh hint |
| Q7 | First user role? | `org_admin` |
| Q8 | Orphaned users allowed? | Yes |
| Q9 | Expired trial handling? | Block launch, keep record |
| Q10 | Multiple trials same app? | No, idempotent |
| Q11 | JWT validation method? | Shared secret (HMAC-SHA256) |
| Q12 | Redirect URL format? | Query params format (`{base_url}/launch?token=JWT&tenant_id=ID`) |

## Features (Detailed Specs)

1. Public App Catalog — `specs/features/01-public-apps.md`
2. Pre-login Onboarding — `specs/features/02-onboarding-prelogin.md`
3. OIDC Auth (Keycloak) — `specs/features/03-oidc-auth-keycloak.md`
4. Orgs/Tenants/Memberships — `specs/features/04-tenants-memberships.md`
5. Trial Subscriptions — `specs/features/05-subscriptions-trial.md`
6. Launch Token + Redirect — `specs/features/06-launch-token.md`
7. Admin Seed + Config — `specs/features/09-admin-seed-config.md`

---

## User Stories & Acceptance Criteria

### User Story 1 — New User Onboarding (Priority: P0)

A new user selects an application and provides organization/tenant names, then authenticates via Keycloak and is automatically provisioned with a 14-day trial subscription.

**Why P0**: This is the core acquisition flow. Without it, no new users can access the platform.

**Acceptance Scenarios**:

1. **Given** no user exists, **When** user completes pre-login form (app + org_name + tenant_name) and OIDC authentication, **Then** org/tenant/user/membership are created with 14-day trial subscription
2. **Given** onboarding session exists, **When** user completes OIDC auth within 60 minutes, **Then** provisioning succeeds and onboarding session is consumed
3. **Given** onboarding session expired (TTL > 60min), **When** user attempts callback, **Then** error `ONBOARDING_SESSION_EXPIRED` is returned
4. **Given** onboarding session already consumed, **When** callback is replayed, **Then** error `ONBOARDING_SESSION_CONSUMED` is returned

---

### User Story 2 — Returning User Login (Priority: P0)

An existing user logs in without pre-selection and accesses their existing tenants and subscriptions.

**Why P0**: Existing users need to access the platform. Must work seamlessly.

**Acceptance Scenarios**:

1. **Given** user exists, **When** user calls `GET /v1/auth/login` (no onboarding_token), **Then** redirects to Keycloak
2. **Given** authenticated returning user, **When** callback completes, **Then** user's `last_login_at` is updated
3. **Given** user exists in org A, **When** same `idp_sub` attempts to onboard into org B, **Then** error `USER_ORG_CONFLICT` is returned

---

### User Story 3 — Tenant Management (Priority: P1)

Users manage tenants within their organization and membership across tenants.

**Why P1**: Required for multi-branch organizations. Depends on auth (P0).

**Acceptance Scenarios**:

1. **Given** user is `org_admin`, **When** they create tenant with name, **Then** tenant is created with `UNIQUE(org_id, tenant_name)`
2. **Given** duplicate tenant name in same org, **When** creation attempted, **Then** error `TENANT_NAME_EXISTS` is returned
3. **Given** user is `org_admin` or `tenant_admin`, **When** they add user to tenant, **Then** membership is created with specified role
4. **Given** user is `tenant_member`, **When** they attempt to add members, **Then** access is denied

---

### User Story 4 — Trial Subscriptions (Priority: P1)

Tenants have 14-day trial subscriptions to applications, created automatically during onboarding or manually post-login.

**Why P1**: Core business model. Enables app access.

**Acceptance Scenarios**:

1. **Given** new user onboarding, **When** provisioning completes, **Then** subscription with `status=trial` and `trial_ends_at = now + 14 days` is created
2. **Given** authenticated user with `tenant_admin` role, **When** they request `POST /v1/subscriptions` for additional app, **Then** new trial subscription is created
3. **Given** trial subscription expired, **When** user attempts launch, **Then** error `TRIAL_EXPIRED` is returned

---

### User Story 5 — Application Launch (Priority: P2)

A tenant member launches a subscribed application and receives a short-lived Launch JWT.

**Why P2**: Delivers value to users. Depends on all prior features.

**Acceptance Scenarios**:

1. **Given** user is tenant member, **When** they request `GET /v1/launch?tenant_id=X&app_id=Y`, **Then** Launch JWT is issued and 302 redirect to `{app.base_url}/launch?token=...&tenant_id=...`
2. **Given** user is NOT tenant member, **When** they request launch, **Then** error `NOT_TENANT_MEMBER` is returned
3. **Given** tenant has no subscription to app, **When** launch requested, **Then** error `NO_SUBSCRIPTION` is returned
4. **Given** invalid/expired Launch JWT presented to app, **When** app validates, **Then** standard error response (per app contract)

---

## End-to-End Flow (MVP)

### New User Flow

```
1. Anonymous selects app (pacs/erp) + org_name + tenant_name
2. POST /v1/onboarding → creates session, returns onboarding_token + login_url
3. GET /v1/auth/login?onboarding_token=... → 302 to Keycloak
4. Keycloak authenticates → 302 to /v1/auth/callback?code=...&state=...
5. POST /v1/auth/callback → validates tokens, resolves onboarding session
6. CP provisions: org/tenant/user/membership + 14-day trial subscription
7. CP issues short-lived Launch JWT
8. 302 redirect to app: {base_url}/launch?token=...&tenant_id=...
```

### Returning User Flow

```
1. GET /v1/auth/login (no token) → 302 to Keycloak
2. Keycloak authenticates → 302 to /v1/auth/callback
3. POST /v1/auth/callback → validates tokens, looks up existing user
4. Return authenticated session / tokens
5. GET /v1/tenants → user selects tenant
6. GET /v1/launch?tenant_id=X&app_id=Y → Launch JWT + redirect
```

### Add Subscription (Post-login)

```
POST /v1/subscriptions
  { tenant_id, app_id }
  → creates 14-day trial subscription
```

---

## Requirements

### Functional Requirements

**Onboarding**
- **FR-001**: System MUST accept pre-login form with `app_id`, `org_name`, `tenant_name`
- **FR-002**: System MUST create onboarding session with 60-minute TTL
- **FR-003**: System MUST enforce single-consume on onboarding sessions via status field
- **FR-004**: System MUST bind OIDC `state` parameter to `onboarding_token` for CSRF protection

**Authentication**
- **FR-005**: System MUST authenticate users via OIDC authorization code flow with Keycloak
- **FR-006**: System MUST validate bearer tokens using issuer URL and JWKS endpoint
- **FR-007**: System MUST enforce `aud` claim validation
- **FR-008**: System MUST extract user identity (`sub` claim) and profile (`email`, `name`) from validated tokens
- **FR-009**: System MUST support `GET /v1/auth/login` with optional `onboarding_token` parameter
- **FR-010**: System MUST reject same `idp_sub` attempting to onboard into different org

**Provisioning**
- **FR-011**: System MUST auto-provision organization if not exists (from onboarding `org_name`)
- **FR-012**: System MUST auto-provision tenant if not exists (from onboarding `tenant_name`)
- **FR-013**: System MUST create user with `idp_sub`, `email`, `name` on first authentication
- **FR-014**: System MUST create membership linking user to tenant with default role
- **FR-015**: System MUST create trial subscription with `status=trial`, `trial_ends_at = now + 14 days`

**Tenant Management**
- **FR-016**: System MUST enforce `UNIQUE(org_id, tenant_name)` constraint
- **FR-017**: System MUST allow `org_admin` to create tenants within their organization
- **FR-018**: System MUST allow users to list tenants they are members of

**Membership**
- **FR-019**: System MUST allow `org_admin` and `tenant_admin` to add users to tenants
- **FR-020**: System MUST assign role (`org_admin`, `tenant_admin`, `tenant_member`) to memberships
- **FR-021**: System MUST reject membership modifications by `tenant_member`

**Subscriptions**
- **FR-022**: System MUST allow `org_admin` and `tenant_admin` to create trial subscriptions
- **FR-023**: System MUST make subscription creation idempotent per `(tenant_id, app_id)`
- **FR-024**: System MUST allow listing subscriptions for a tenant

**Launch**
- **FR-025**: System MUST validate user is member of tenant before issuing Launch JWT
- **FR-026**: System MUST validate tenant has active/trial subscription to requested app
- **FR-027**: System MUST issue short-lived Launch JWT with fixed claims
- **FR-028**: System MUST return 302 redirect to `{app.base_url}/launch?token=...&tenant_id=...`

**Application Catalog**
- **FR-029**: System MUST provide read-only catalog of available applications
- **FR-030**: System MUST seed initial applications (PACS, ERP) on startup

### Non-Functional Requirements

- **NFR-001**: All protected endpoints require valid bearer token
- **NFR-002**: Cross-organization access is blocked at data layer
- **NFR-003**: 95% of API requests complete within 500ms
- **NFR-004**: System supports 1000 concurrent authentication requests
- **NFR-005**: OpenAPI schema provided for all endpoints
- **NFR-006**: All services emit structured JSON logs to stdout
- **NFR-007**: `/health` endpoint returns 200 when database connected, 503 otherwise

---

## Key Entities

**Organization**: Top-level customer entity. Key attributes: `id`, `name`, `created_at`. Constraint: unique name.

**Tenant**: Branch within organization. Key attributes: `id`, `org_id`, `name`, `created_at`. Constraint: `UNIQUE(org_id, name)`.

**User**: Authenticated person. Key attributes: `id`, `org_id`, `idp_sub`, `email`, `name`, `last_login_at`, `created_at`. Constraint: unique `idp_sub`.

**Membership**: User ↔ Tenant association. Key attributes: `id`, `tenant_id`, `user_id`, `role`, `created_at`.

**Application**: SaaS product. Key attributes: `id`, `app_key`, `name`, `base_url`, `status`.

**Subscription**: Tenant → App entitlement. Key attributes: `id`, `tenant_id`, `app_id`, `status` (trial), `trial_ends_at`, `created_at`.

**OnboardingSession**: Pre-login session. Key attributes: `id`, `token`, `org_name`, `tenant_name`, `app_id`, `status` (pending/consumed/expired), `expires_at`, `created_at`.

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `ONBOARDING_SESSION_EXPIRED` | 400 | Session TTL exceeded |
| `ONBOARDING_SESSION_CONSUMED` | 400 | Session already used |
| `USER_ORG_CONFLICT` | 409 | User exists in different org |
| `TENANT_NAME_EXISTS` | 409 | Tenant name already in org |
| `NOT_TENANT_MEMBER` | 403 | User not member of tenant |
| `NO_SUBSCRIPTION` | 403 | No subscription to app |
| `TRIAL_EXPIRED` | 403 | Trial period ended |
| `INVALID_TOKEN` | 401 | Invalid/expired token |
| `IDP_UNAVAILABLE` | 503 | Identity provider unreachable |

---

## Non-Goals (MVP)

- Billing/Stripe integration
- Core services split (RBAC engine, audit service, notification service)
- Multi-org per user
- SAML (OIDC only)
- Web UI (API-only)

---

## Success Criteria

| ID | Criteria |
|----|----------|
| SC-001 | New user completes onboarding + auth + redirect in under 60 seconds |
| SC-002 | Returning user logs in and sees tenant list within 10 seconds |
| SC-003 | Trial subscription auto-created with correct 14-day expiry |
| SC-004 | `/v1/launch` enforces membership + subscription |
| SC-005 | Same user (sub) blocked from onboarding to different org |
| SC-006 | 100% of protected endpoints reject invalid tokens |
| SC-007 | 95% of API requests complete within 500ms |
