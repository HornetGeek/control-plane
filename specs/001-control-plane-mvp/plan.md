# Implementation Plan: Control Plane MVP

**Branch**: `001-control-plane-mvp` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-control-plane-mvp/spec.md`

**Note**: This plan defines the technical architecture for a multi-tenant SaaS Control Plane microservice.

## Summary

Build a REST API microservice that provides multi-tenant organization management, OIDC authentication via Zitadel, subscription-based application access control, and launch routing to downstream applications. The service is API-only (no web UI), enforces strict tenancy boundaries, and uses coarse-grained role-based authorization.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (async), Pydantic v2, python-jose[cryptography], httpx
**Storage**: PostgreSQL with SQLAlchemy 2.0 (async), Alembic for migrations
**Testing**: pytest with async support, pytest-asyncio, httpx for test client
**Target Platform**: Linux server (containerized)
**Project Type**: web (REST API microservice)
**Performance Goals**: 1000 concurrent auth requests, 95% of API requests under 500ms
**Constraints**: <200ms p95 latency, <500MB memory footprint
**Scale/Scope**: 10k+ users, 1k+ organizations, 10k+ tenants

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| API-First Architecture | PASS | REST API only, no web UI planned |
| Strict Tenancy Boundaries | PASS | Org/tenant isolation enforced at all layers |
| Subscription-Based Access Control | PASS | Dual-check: tenant subscription + user membership |
| OIDC-First Authentication | PASS | Zitadel integration via authorization code flow |
| Coarse-Grained Authorization | PASS | Three roles: org_admin, tenant_admin, tenant_member |
| Idempotent Operations | PASS | Membership and subscription creation are idempotent |
| No External Billing Integration | PASS | Manual subscription status management |
| Audit Stubs Only | PASS | Internal interfaces with minimal persistence |

## Project Structure

### Documentation (this feature)

```text
specs/001-control-plane-mvp/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output (below)
├── data-model.md        # Phase 1 output (below)
├── quickstart.md        # Phase 1 output (below)
├── contracts/           # Phase 1 output (below)
│   ├── auth.yaml
│   ├── tenants.yaml
│   ├── memberships.yaml
│   ├── applications.yaml
│   ├── subscriptions.yaml
│   └── launch.yaml
└── checklists/
    └── requirements.md  # Quality checklist (completed)
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
│   └── subscription.py  # Subscription model
├── schemas/
│   ├── __init__.py
│   ├── auth.py          # OIDC token, user response schemas
│   ├── organization.py  # Organization request/response schemas
│   ├── tenant.py        # Tenant request/response schemas
│   ├── membership.py    # Membership request/response schemas
│   ├── application.py   # Application catalog schemas
│   ├── subscription.py  # Subscription request/response schemas
│   └── common.py        # Common schemas (pagination, error response)
├── services/
│   ├── __init__.py
│   ├── auth.py          # OIDC token validation, user lookup/creation
│   ├── tenant.py        # Tenant CRUD operations
│   ├── membership.py    # Membership management
│   ├── subscription.py  # Subscription management
│   ├── application.py   # Application catalog lookup
│   └── launch.py        # Launch request validation and URL generation
├── api/
│   ├── __init__.py
│   ├── dependencies.py  # FastAPI dependencies (auth, tenant lookup)
│   ├── middleware.py    # Correlation ID, error handling
│   └── v1/
│       ├── __init__.py
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
    ├── oidc.py          # OIDC token validation, JWKS caching
    ├── authorization.py # Role-based access control helpers
    └── audit.py         # Audit event stubs

tests/
├── conftest.py          # Pytest fixtures (test DB, test client)
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   └── test_security.py
├── integration/
│   ├── test_auth_flow.py
│   ├── test_tenants.py
│   ├── test_memberships.py
│   ├── test_subscriptions.py
│   └── test_launch.py
└── contract/
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

## Complexity Tracking

> No violations - specification aligns with constitution principles. All technical decisions are specified in the constitution and require no additional research.

---

## Phase 0: Research & Technology Decisions

**Status**: COMPLETE

All technical decisions are specified in the Control Plane Constitution (version 1.0.0). No additional research is required as the constitution provides:

- Language and framework selection (Python 3.11+, FastAPI, Pydantic v2)
- Database choice (PostgreSQL with SQLAlchemy 2.0 async)
- Testing framework (pytest with async support)
- Authentication strategy (OIDC with Zitadel)
- Authorization model (coarse-grained roles)
- API standards (OpenAPI 3.0, REST conventions)

See `/media/hornet/84ACF2FAACF2E5981/control_plan/.specify/memory/constitution.md` for complete technical specifications.

---

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions, relationships, and database schema.

### API Contracts

See [contracts/](./contracts/) directory for OpenAPI specifications for each endpoint group.

### Quickstart Guide

See [quickstart.md](./quickstart.md) for local development setup and testing instructions.

---

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion*

| Principle | Status | Notes |
|-----------|--------|-------|
| API-First Architecture | PASS | All functionality exposed via REST API |
| Strict Tenancy Boundaries | PASS | Data model enforces org_id on all entities |
| Subscription-Based Access Control | PASS | Subscription entity with tenant-level scoping |
| OIDC-First Authentication | PASS | User.idp_sub for OIDC subject mapping |
| Coarse-Grained Authorization | PASS | Membership.role enum with three values |
| Idempotent Operations | PASS | Unique constraints on (tenant_id, user_id) and (tenant_id, app_key) |
| No External Billing Integration | PASS | Subscription.status as database field only |
| Audit Stubs Only | PASS | Audit interface defined without external dispatch |

**All gates passed - implementation can proceed.**
