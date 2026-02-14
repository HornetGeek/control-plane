# Implementation Plan: Control Plane MVP

**Branch**: `001-control-plane-mvp` | **Date**: 2026-02-09 | **Updated**: 2026-02-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-control-plane-mvp/spec.md`

**Note**: This plan defines the technical architecture for a multi-tenant SaaS Control Plane microservice with pre-login onboarding.

## Summary

Build a REST API microservice that provides:
- **Pre-login onboarding** — User selects app + org_name + tenant_name BEFORE authentication
- **OIDC authentication** via Keycloak (realm: `control-plane`)
- **Auto-provisioning** — Org/tenant/user/membership + 14-day trial subscription created on first login
- **Launch routing** — Short-lived Launch JWT redirects user to subscribed application

The service is API-only (no web UI), enforces strict tenancy boundaries (one user = one org), and uses coarse-grained role-based authorization.

## Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Version** | Python 3.11+ |
| **Primary Dependencies** | FastAPI (async), Pydantic v2, python-jose[cryptography], httpx |
| **Storage** | PostgreSQL with SQLAlchemy 2.0 (async), Alembic for migrations |
| **Testing** | pytest with async support, pytest-asyncio, httpx for test client |
| **Target Platform** | Linux server (containerized) |
| **Project Type** | web (REST API microservice) |
| **Performance Goals** | 1000 concurrent auth requests, 95% of API requests under 500ms |
| **Constraints** | <200ms p95 latency, <500MB memory footprint |
| **Scale/Scope** | 10k+ users, 1k+ organizations, 10k+ tenants |
| **IdP** | Keycloak (realm: `control-plane`) |
| **Issuer URL** | `http://localhost:18080/realms/control-plane` |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| API-First Architecture | PASS | REST API only, no web UI planned |
| Strict Tenancy Boundaries | PASS | Org/tenant isolation enforced at all layers |
| One User = One Org | PASS | `idp_sub` unique constraint prevents multi-org |
| Subscription-Based Access Control | PASS | Dual-check: tenant subscription + user membership |
| OIDC-First Authentication | PASS | Keycloak integration via authorization code flow |
| Coarse-Grained Authorization | PASS | Three roles: org_admin, tenant_admin, tenant_member |
| Idempotent Operations | PASS | Membership and subscription creation are idempotent |
| Trial-Only Subscriptions (MVP) | PASS | 14-day trial, no billing integration |
| Audit Stubs Only | PASS | Internal interfaces with minimal persistence |

## Project Structure

### Documentation (this feature)

```text
specs/001-control-plane-mvp/
├── spec.md              # Feature specification (updated 2026-02-14)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── onboarding.yaml
│   ├── auth.yaml
│   ├── tenants.yaml
│   ├── memberships.yaml
│   ├── applications.yaml
│   ├── subscriptions.yaml
│   └── launch.yaml
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py              # FastAPI application entry point
├── config.py            # Environment-based configuration (pydantic-settings)
├── models/
│   ├── __init__.py
│   ├── base.py          # Base declarative model
│   ├── organization.py  # Organization model
│   ├── tenant.py        # Tenant model
│   ├── user.py          # User model
│   ├── membership.py    # Membership model (user <-> tenant)
│   ├── application.py   # Application catalog model
│   ├── subscription.py  # Subscription model (trial-only)
│   └── onboarding.py    # OnboardingSession model
├── schemas/
│   ├── __init__.py
│   ├── onboarding.py    # Onboarding request/response schemas
│   ├── auth.py          # OIDC token, user response schemas
│   ├── organization.py  # Organization request/response schemas
│   ├── tenant.py        # Tenant request/response schemas
│   ├── membership.py    # Membership request/response schemas
│   ├── application.py   # Application catalog schemas
│   ├── subscription.py  # Subscription request/response schemas
│   ├── launch.py        # Launch JWT schemas
│   └── common.py        # Common schemas (pagination, error response)
├── services/
│   ├── __init__.py
│   ├── onboarding.py    # Onboarding session management (create, consume, validate)
│   ├── provisioning.py  # Auto-provisioning (org, tenant, user, membership, subscription)
│   ├── auth.py          # OIDC token validation, user lookup/creation
│   ├── tenant.py        # Tenant CRUD operations
│   ├── membership.py    # Membership management
│   ├── subscription.py  # Subscription management (trial-only)
│   ├── application.py   # Application catalog lookup
│   └── launch.py        # Launch JWT generation and validation
├── api/
│   ├── __init__.py
│   ├── dependencies.py  # FastAPI dependencies (auth, tenant lookup)
│   ├── middleware.py    # Correlation ID, error handling
│   └── v1/
│       ├── __init__.py
│       ├── onboarding.py # Onboarding endpoints (POST /v1/onboarding)
│       ├── auth.py      # Auth endpoints (login, callback, me)
│       ├── tenants.py   # Tenant endpoints
│       ├── memberships.py  # Membership endpoints
│       ├── applications.py # Application catalog
│       ├── subscriptions.py # Subscription endpoints
│       └── launch.py    # Launch endpoint
├── db/
│   ├── __init__.py
│   ├── session.py       # Async session factory
│   └── seed.py          # Database seeding scripts
└── security/
    ├── __init__.py
    ├── oidc.py          # Keycloak OIDC token validation, JWKS caching
    ├── launch_jwt.py    # Launch JWT generation and validation
    ├── authorization.py # Role-based access control helpers
    └── audit.py         # Audit event stubs

tests/
├── conftest.py          # Pytest fixtures (test DB, test client, mock Keycloak)
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_onboarding.py
│   ├── test_launch_jwt.py
│   └── test_security.py
├── integration/
│   ├── test_onboarding_flow.py
│   ├── test_auth_flow.py
│   ├── test_returning_user_flow.py
│   ├── test_tenants.py
│   ├── test_memberships.py
│   ├── test_subscriptions.py
│   └── test_launch.py
└── contract/
    ├── test_v1_onboarding.py
    ├── test_v1_auth.py
    ├── test_v1_tenants.py
    ├── test_v1_memberships.py
    ├── test_v1_subscriptions.py
    └── test_v1_launch.py

alembic/                 # Alembic configuration
├── env.py
├── script.py.mako
└── versions/
```

**Structure Decision**: Single Python project with FastAPI. Source code follows domain-driven organization (models, schemas, services, API routes). All database operations are async using SQLAlchemy 2.0.

---

## Phase 0: Research & Technology Decisions

**Status**: COMPLETE

### Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| IdP | Keycloak | Open-source, self-hosted, realm-based multi-tenancy |
| Onboarding Token | Opaque UUID + server-side session | Simpler than JWT, easier revocation |
| Launch Token | Short-lived JWT (5 min) | Stateless validation by apps |
| Trial Duration | 14 days | Configured in subscription entity |

### Keycloak Configuration

```yaml
realm: control-plane
issuer: http://localhost:18080/realms/control-plane
client_id: control-plane-api
scopes: openid profile email
```

---

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:

| Entity | Key Attributes | Constraints |
|--------|---------------|-------------|
| Organization | `id`, `name`, `created_at` | `name` unique |
| Tenant | `id`, `org_id`, `name`, `created_at` | `UNIQUE(org_id, name)` |
| User | `id`, `org_id`, `idp_sub`, `email`, `name`, `last_login_at` | `idp_sub` unique |
| Membership | `id`, `tenant_id`, `user_id`, `role` | `UNIQUE(tenant_id, user_id)` |
| Application | `id`, `app_key`, `name`, `base_url`, `status` | `app_key` unique |
| Subscription | `id`, `tenant_id`, `app_id`, `status`, `trial_ends_at` | `UNIQUE(tenant_id, app_id)` |
| OnboardingSession | `id`, `token`, `org_name`, `tenant_name`, `app_id`, `status`, `expires_at` | `token` unique |

### API Contracts

See [contracts/](./contracts/) directory for OpenAPI specifications.

**Endpoint Summary**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/onboarding` | POST | Create onboarding session |
| `/v1/auth/login` | GET | Initiate OIDC flow (optional `onboarding_token`) |
| `/v1/auth/callback` | GET | OIDC callback handler |
| `/v1/auth/me` | GET | Current user info |
| `/v1/tenants` | GET | List user's tenants |
| `/v1/tenants` | POST | Create tenant (org_admin) |
| `/v1/tenants/{id}` | GET | Get tenant details |
| `/v1/tenants/{id}/members` | GET/POST | List/add members |
| `/v1/applications` | GET | List available apps |
| `/v1/subscriptions` | GET/POST | List/create subscriptions |
| `/v1/launch` | GET | Issue Launch JWT and redirect |

### Quickstart Guide

See [quickstart.md](./quickstart.md) for local development setup and testing instructions.

---

## Phase 2: Implementation Phases

### Phase 2.1: Foundation (P0)

- Database models + Alembic migrations
- Keycloak OIDC integration
- Application catalog seeding

### Phase 2.2: Onboarding Flow (P0)

- Onboarding session model + service
- `POST /v1/onboarding` endpoint
- `GET /v1/auth/login` with onboarding_token binding
- `GET /v1/auth/callback` with provisioning logic
- Auto-provisioning service (org, tenant, user, membership, trial subscription)

### Phase 2.3: Returning User Flow (P0)

- `GET /v1/auth/login` without onboarding_token
- `GET /v1/auth/callback` for existing users
- `GET /v1/tenants` endpoint

### Phase 2.4: Tenant Management (P1)

- `POST /v1/tenants` (org_admin)
- `GET /v1/tenants/{id}`
- Membership endpoints

### Phase 2.5: Subscriptions & Launch (P1-P2)

- `GET/POST /v1/subscriptions`
- Launch JWT service
- `GET /v1/launch` endpoint

---

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion*

| Principle | Status | Notes |
|-----------|--------|-------|
| API-First Architecture | PASS | All functionality exposed via REST API |
| Strict Tenancy Boundaries | PASS | Data model enforces org_id on all entities |
| One User = One Org | PASS | `idp_sub` unique constraint enforced |
| Subscription-Based Access Control | PASS | Subscription entity with tenant-level scoping |
| OIDC-First Authentication | PASS | Keycloak OIDC with `aud` validation |
| Coarse-Grained Authorization | PASS | Membership.role enum with three values |
| Idempotent Operations | PASS | Unique constraints on key relationships |
| Trial-Only Subscriptions | PASS | `trial_ends_at` field, no billing |
| Audit Stubs Only | PASS | Audit interface defined without external dispatch |

**All gates passed - implementation can proceed.**
