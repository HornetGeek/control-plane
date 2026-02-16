# Control Plane MVP — Master Specification

**Project**: Control Plane (Generic SaaS Management Service)
**Version**: 2.0.0
**Created**: 2026-02-15
**Status**: Active
**Constitution**: [constitution.md](../.specify/memory/constitution.md)

## Overview

Control Plane (CP) is the **public-facing Generic SaaS management service** for a multi-organization, multi-tenant, multi-application SaaS platform.

### Mission (per Constitution §I)

CP provides:
- Application catalog management (PACS/ERP and future apps)
- Organization and tenant (branch) registry
- Tenant subscription registry (tenant ↔ app)
- Administrative views for SaaS operations (dashboard, tenants, organizations, settings)

CP explicitly does **not** provide:
- Business-domain workflows (these belong to Data Plane apps)
- Role/permission data ownership (belongs to Core)
- Session issuance or launch JWT issuance

## Architecture Context

### 3-Plane Model (Constitution §II)

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (this service)            │
│  - App Catalog | Organizations | Tenants | Subscriptions    │
│  - Dashboard APIs | Admin Views                              │
│  - Local OIDC Token Validation                               │
│  - Authorization Delegation to Core (MOCK for MVP)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Authorization requests (mock)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CORE SERVICE (Mock for MVP)              │
│  - Identity/Membership/RBAC                                  │
│  - Authorization decisions                                   │
│  - Users (IdP-linked)                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ App redirects
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        DATA PLANE                            │
│  - PACS Service | ERP Service | Future Apps                  │
│  - Domain workflows (tenant-aware)                           │
└─────────────────────────────────────────────────────────────┘
```

### Source of Truth

| Entity | Owner |
|--------|-------|
| Applications, Organizations, Tenants, Subscriptions | **Control Plane** |
| Users, Memberships, Roles/Permissions, AuthZ Decisions | **Core** (mocked) |

## MVP Constraints

### In Scope
- ✅ Local OIDC token validation (Keycloak JWKS)
- ✅ Authorization delegation to **mock Core** client
- ✅ Redis caching for authorization decisions
- ✅ CP-owned entities: applications, organizations, tenants, subscriptions
- ✅ 14-day trial subscriptions
- ✅ Soft delete + status for all entities
- ✅ Dashboard APIs (scoped by role)
- ✅ Users listing (via mock Core)

### Out of Scope (Deferred)
- ❌ Pre-login onboarding flow
- ❌ Launch JWT issuance (apps handle their own OIDC)
- ❌ Real Core service integration (mock only)
- ❌ Billing/Stripe integration
- ❌ Web UI (API-only for MVP)

## Roles & Access (Constitution §IV)

| Role | Scope | CP Access |
|------|-------|-----------|
| `super_admin` | Global | Manage apps, orgs, view global dashboards |
| `org_admin` | Organization | Manage tenants/subscriptions in org |
| `tenant_admin` | Tenant | Manage own tenant and subscriptions |
| `tenant_member` | Tenant | No CP access (Data Plane only) |

## Epics & User Stories

| Epic | Goal | Epic | User Stories |
|------|------|------|--------------|
| **EPIC 0** | Setup & Engineering Baseline | [epic.md](epics/epic-0-setup/epic.md) | [user-stories.md](epics/epic-0-setup/user-stories.md) |
| **EPIC 1** | Security & Authorization | [epic.md](epics/epic-1-security-authz/epic.md) | [user-stories.md](epics/epic-1-security-authz/user-stories.md) |
| **EPIC 2** | Data Model | [epic.md](epics/epic-2-data-model/epic.md) | [user-stories.md](epics/epic-2-data-model/user-stories.md) |
| **EPIC 3** | Applications Catalog | [epic.md](epics/epic-3-applications/epic.md) | [user-stories.md](epics/epic-3-applications/user-stories.md) |
| **EPIC 4** | Organizations | [epic.md](epics/epic-4-organizations/epic.md) | [user-stories.md](epics/epic-4-organizations/user-stories.md) |
| **EPIC 5** | Tenants + Sync | [epic.md](epics/epic-5-tenants-sync/epic.md) | [user-stories.md](epics/epic-5-tenants-sync/user-stories.md) |
| **EPIC 6** | Subscriptions + Trial | [epic.md](epics/epic-6-subscriptions-trial/epic.md) | [user-stories.md](epics/epic-6-subscriptions-trial/user-stories.md) |
| **EPIC 7** | Dashboard APIs | [epic.md](epics/epic-7-dashboard/epic.md) | [user-stories.md](epics/epic-7-dashboard/user-stories.md) |
| **EPIC 8** | Users Listing | [epic.md](epics/epic-8-users-listing/epic.md) | [user-stories.md](epics/epic-8-users-listing/user-stories.md) |

## Epic Dependencies

```
EPIC 0 (Setup)
    │
    ▼
EPIC 2 (Data Model) ─────► EPIC 1 (Security)
    │                           │
    ▼                           ▼
EPIC 3 (Apps) ◄──────────► EPIC 4 (Orgs)
    │                           │
    └───────────┬───────────────┘
                ▼
         EPIC 5 (Tenants)
                │
                ▼
         EPIC 6 (Subscriptions)
                │
    ┌───────────┴───────────┐
    ▼                       ▼
EPIC 7 (Dashboard)    EPIC 8 (Users)
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI (async) |
| Validation | Pydantic v2 |
| Database | PostgreSQL + SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Cache | Redis |
| JWT | python-jose[cryptography] |
| HTTP Client | httpx |
| Testing | pytest (async) |

## Error Contract (Constitution §IX.2)

All endpoints return consistent error envelope:

```json
{
  "error_code": "STRING",
  "message": "STRING",
  "details": {}
}
```

## Key Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `KEYCLOAK_ISSUER_URL` | Keycloak issuer URL | Required |
| `KEYCLOAK_CLIENT_ID` | CP client ID in Keycloak | Required |
| `KEYCLOAK_CLIENT_SECRET` | CP client secret | Required |
| `AUTHZ_CACHE_TTL` | AuthZ decision cache TTL (seconds) | 60 |
| `TRIAL_DURATION_DAYS` | Trial subscription duration | 14 |

## Success Criteria

| ID | Criteria |
|----|----------|
| SC-001 | All protected endpoints enforce mock Core authorization |
| SC-002 | Redis caching reduces mock Core calls by >80% |
| SC-003 | 14-day trial subscriptions created correctly |
| SC-004 | Soft delete works for all entities |
| SC-005 | Dashboard returns correct scoped metrics |
| SC-006 | Users listing returns scoped results via mock Core |
| SC-007 | 95% of API requests complete within 500ms |
| SC-008 | All error responses follow standard envelope |

## Related Documents

- [Constitution](../.specify/memory/constitution.md) - Core principles and governance
- [README](../README.md) - Architecture diagram and overview
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
