# Implementation Plan: Control Plane MVP

**Branch**: `001-control-plane-mvp` | **Date**: 2026-02-09 | **Spec**: [spec.md](../specs/001-control-plane-mvp/spec.md)
**Input**: Feature specification from `/specs/001-control-plane-mvp/spec.md`

**Note**: This plan defines the technical architecture for a multi-tenant SaaS Control Plane microservice.

## Summary

Build a REST API microservice that provides multi-tenant organization management, OIDC authentication via Zitadel, subscription-based application access control, and launch routing to downstream applications. The service is API-only (no web UI), enforces strict tenancy boundaries, and uses coarse-grained role-based authorization.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (async), Pydantic v2, python-jose, httpx
**Storage**: PostgreSQL with SQLAlchemy 2.0 (async), Alembic for migrations
**Testing**: pytest with async support, pytest-asyncio
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
└── checklists/
    └── requirements.md  # Quality checklist (completed)

docs/                    # This directory
├── plan.md              # This file (implementation plan)
├── data-model.md        # Data model design (below)
├── api-design.md        # API endpoint contracts (below)
└── quickstart.md        # Developer setup guide (below)
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
│   └── migrations/      # Alembic migrations
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
    ├── test_v1_auth.yaml
    ├── test_v1_tenants.yaml
    ├── test_v1_memberships.yaml
    ├── test_v1_subscriptions.yaml
    └── test_v1_launch.yaml

alembic/                 # Alembic configuration
├── env.py
├── script.py.mako
└── versions/
```

**Structure Decision**: Single Python project with FastAPI. Source code follows domain-driven organization (models, schemas, services, API routes). All database operations are async using SQLAlchemy 2.0.

## Complexity Tracking

> No violations - specification aligns with constitution principles.

## Data Model

### Core Entities

```python
# Organization
{
    "id": UUID (primary key),
    "name": String,
    "created_at": DateTime,
    "updated_at": DateTime
}

# Tenant
{
    "id": UUID (primary key),
    "organization_id": UUID (foreign key -> organization.id),
    "name": String,
    "created_at": DateTime,
    "updated_at": DateTime
}

# User
{
    "id": UUID (primary key),
    "organization_id": UUID (foreign key -> organization.id),
    "idp_sub": String (unique, OIDC subject),
    "email": String,
    "name": String,
    "last_login_at": DateTime (nullable),
    "created_at": DateTime,
    "updated_at": DateTime,
    "status": Enum (active, inactive)
}

# Membership
{
    "id": UUID (primary key),
    "tenant_id": UUID (foreign key -> tenant.id),
    "user_id": UUID (foreign key -> user.id),
    "role": Enum (org_admin, tenant_admin, tenant_member),
    "created_at": DateTime,
    # Unique constraint on (tenant_id, user_id)
}

# Application
{
    "app_key": String (primary key),
    "name": String,
    "launch_base_url": String,
    "status": Enum (active, inactive),
    "created_at": DateTime,
    "updated_at": DateTime
}

# Subscription
{
    "id": UUID (primary key),
    "tenant_id": UUID (foreign key -> tenant.id),
    "app_key": String (foreign key -> application.app_key),
    "status": Enum (active, suspended, canceled),
    "started_at": DateTime,
    "updated_at": DateTime,
    # Unique constraint on (tenant_id, app_key)
}
```

### Relationships

- Organization 1:N User (each user belongs to exactly one org)
- Organization 1:N Tenant (each tenant belongs to exactly one org)
- User M:N Tenant (via Membership, with role)
- Tenant 1:N Subscription (each tenant has many subscriptions)
- Application 1:N Subscription (each app has many subscriptions)

### Indexes

- `users.organization_id` (for org-wide queries)
- `users.idp_sub` (unique, for OIDC lookup)
- `tenants.organization_id` (for org-wide queries)
- `memberships.tenant_id` (for tenant member listing)
- `memberships.user_id` (for user's tenant listing)
- `subscriptions.tenant_id` (for tenant subscription listing)
- `subscriptions (tenant_id, app_key)` (unique, for idempotent subscription)

## API Design

### Authentication Pattern

All endpoints except `/v1/auth/login` and `/v1/auth/callback` require a valid bearer token:

```
Authorization: Bearer <jwt_token>
```

Token validation flow:
1. Extract JWT from Authorization header
2. Verify signature using JWKS from Zitadel issuer
3. Validate claims: `iss`, `aud`, `exp`, `sub`
4. Extract `sub` (user ID) and `org_id` (organization ID)
5. Look up/create user record
6. Attach user to request state for authorization

### Endpoint Summary

| Method | Path | Description | Auth Required | Role Required |
|--------|------|-------------|---------------|---------------|
| GET | `/v1/auth/login` | Redirect to Zitadel | No | - |
| GET | `/v1/auth/callback` | OIDC callback | No | - |
| GET | `/v1/auth/me` | Current user info | Yes | Any |
| POST | `/v1/tenants` | Create tenant | Yes | org_admin |
| GET | `/v1/tenants` | List tenants | Yes | Any |
| GET | `/v1/tenants/{id}` | Get tenant | Yes | Member or org_admin |
| POST | `/v1/tenants/{tenant_id}/members` | Add member | Yes | org_admin or tenant_admin |
| GET | `/v1/tenants/{tenant_id}/members` | List members | Yes | org_admin or tenant_admin |
| DELETE | `/v1/tenants/{tenant_id}/members/{user_id}` | Remove member | Yes | org_admin or tenant_admin |
| GET | `/v1/applications` | List applications | Yes | Any |
| POST | `/v1/tenants/{tenant_id}/subscriptions` | Subscribe | Yes | org_admin or tenant_admin |
| GET | `/v1/tenants/{tenant_id}/subscriptions` | List subscriptions | Yes | org_admin or tenant_admin |
| PATCH | `/v1/tenants/{tenant_id}/subscriptions/{sub_id}` | Update status | Yes | org_admin or tenant_admin |
| POST | `/v1/launch` | Launch application | Yes | tenant_member or above |

### Request/Response Examples

**Create Tenant**
```json
// POST /v1/tenants
{
  "name": "Branch Office A"
}

// 201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Branch Office A",
  "created_at": "2026-02-09T12:00:00Z"
}
```

**Add Member**
```json
// POST /v1/tenants/{tenant_id}/members
{
  "user_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "tenant_member"
}

// 201 Created
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "user_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "tenant_member",
  "created_at": "2026-02-09T12:00:00Z"
}
```

**Subscribe to Application**
```json
// POST /v1/tenants/{tenant_id}/subscriptions
{
  "app_key": "pacs"
}

// 201 Created (idempotent - returns existing if already subscribed)
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "app_key": "pacs",
  "status": "active",
  "started_at": "2026-02-09T12:00:00Z"
}
```

**Launch Application**
```json
// POST /v1/launch
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "app_key": "pacs",
  "return_to": "https://app.example.com/dashboard"
}

// 200 OK
{
  "redirect_url": "https://pacs.example.com/launch?tenant_id=...&token=...&return_to=..."
}
```

### Error Response Format

```json
{
  "code": "TENANT_NOT_FOUND",
  "message": "Tenant not found or access denied",
  "details": {
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "request_id": "req_abc123"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing/invalid bearer token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `ORGANIZATION_NOT_FOUND` | 404 | Organization not found |
| `TENANT_NOT_FOUND` | 404 | Tenant not found or access denied |
| `USER_NOT_FOUND` | 404 | User not found |
| `APPLICATION_NOT_FOUND` | 404 | Application not available |
| `SUBSCRIPTION_NOT_FOUND` | 404 | Subscription not found |
| `ALREADY_MEMBER` | 409 | User already member of tenant |
| `INVALID_ROLE` | 400 | Invalid role specified |
| `MISSING_ORG_CLAIM` | 401 | OIDC token missing required org_id claim |

## Security Architecture

### Authentication Flow

```
┌─────────┐                    ┌─────────┐                  ┌─────────┐
│  Client │                    │Control  │                  │ Zitadel │
│ (App)   │                    │ Plane   │                  │ (OIDC)  │
└────┬────┘                    └────┬────┘                  └────┬────┘
     │                              │                            │
     │  GET /v1/auth/login          │                            │
     ├─────────────────────────────>│                            │
     │                              │                            │
     │  302 Redirect to Zitadel     │                            │
     │<─────────────────────────────┼────────────────────────────>│
     │                              │                            │
     │  User authenticates          │                            │
     ├─────────────────────────────┼────────────────────────────>│
     │                              │                            │
     │  302 Redirect with code      │                            │
     │<─────────────────────────────┼────────────────────────────>│
     │                              │                            │
     │  GET /v1/auth/callback?code= │                            │
     ├─────────────────────────────>│                            │
     │                              │  Exchange code for token   │
     │                              ├────────────────────────────>│
     │                              │                            │
     │                              │  JWT + id_token            │
     │                              │<────────────────────────────┤
     │                              │                            │
     │                              │  Validate JWT, extract sub │
     │                              │  and org_id, create user   │
     │                              │                            │
     │  200 OK with user info       │                            │
     │<─────────────────────────────┤                            │
```

### Authorization Flow

For each protected request:

1. **Token Validation**: Verify JWT signature and claims
2. **User Lookup**: Find user by `sub` claim, extract organization
3. **Tenant Access**: Verify user is member of requested tenant (or is org_admin)
4. **Role Check**: Enforce role-based permissions for the operation
5. **Subscription Check** (launch only): Verify active subscription

### Correlation ID Flow

```
Client Request        Middleware         Services
     │                   │                  │
     │ X-Request-ID:     │                  │
     ├──────────────────>│                  │
     │                   │ X-Request-ID:    │
     │                   ├─────────────────>│
     │                   │                  │
     │                   │ (all logs include)
     │                   │                  │
     │ X-Request-ID:     │                  │
     │<──────────────────┤                  │
```

## Configuration

### Environment Variables

```bash
# Application
CONTROL_PLANE_ENV=development
CONTROL_PLANE_HOST=0.0.0.0
CONTROL_PLANE_PORT=8000
CONTROL_PLANE_LOG_LEVEL=info

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/control_plane

# OIDC / Zitadel
OIDC_ISSUER=https://auth.craft-crew.com
OIDC_CLIENT_ID=control-plane-client
OIDC_CLIENT_SECRET=secret
OIDC_REDIRECT_URI=https://control-plane.example.com/v1/auth/callback
OIDC_SCOPES=openid profile email

# Application Catalog (seed data)
APPLICATIONS__PACS__NAME="PACS"
APPLICATIONS__PACS__URL="https://pacs.example.com/launch"
APPLICATIONS__PACS__STATUS="active"
APPLICATIONS__ERP__NAME="ERP"
APPLICATIONS__ERP__URL="https://erp.example.com/launch"
APPLICATIONS__ERP__STATUS="active"
```

## Quickstart

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Zitadel instance with OIDC configured

### Local Development Setup

```bash
# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e .

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Run database migrations
alembic upgrade head

# 5. Seed application catalog
python -m src.db.seed_applications

# 6. Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 7. Access API docs
open http://localhost:8000/docs
```

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires test database)
pytest tests/integration/

# Contract tests (validates OpenAPI spec)
pytest tests/contract/

# All tests with coverage
pytest --cov=src tests/
```

## Performance Considerations

### Database

- Connection pooling via SQLAlchemy (async)
- Indexes on frequently queried columns
- Unique constraints for idempotency

### Caching

- JWKS keys cached for OIDC validation (TTL: 5 minutes)
- Application catalog cached in memory (rarely changes)

### Async

- All database operations async (SQLAlchemy 2.0)
- All HTTP requests async (httpx)
- FastAPI async route handlers

## Deployment Considerations

### Container Image

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY alembic/ ./alembic/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks

- `/health` - Liveness probe (no auth required)
- `/ready` - Readiness probe (checks database connectivity)

### Observability

- Structured JSON logging
- Correlation ID on all requests
- Metrics endpoint (Prometheus format) at `/metrics`
