# Data Model: Control Plane MVP

**Feature**: Control Plane MVP
**Date**: 2026-02-09
**Status**: COMPLETE

## Overview

This document defines the complete data model for the Control Plane MVP, including all entities, relationships, and database schema.

---

## Entity Relationship Diagram

```
┌─────────────┐
│Organization │
└──────┬──────┘
       │1
       │
       │N
┌──────▼──────┐     1      ┌─────────┐     N     ┌──────────────┐
│   Tenant    │◄──────────┤Membership│─────────►│     User      │
└──────┬──────┘            └─────────┘             └──────┬───────┘
       │1                                                  │1
       │                                                   │
       │N                                                 N│
┌──────▼──────┐                                    ┌──────▼───────┐
│Subscription │                                    │ Organization │
└──────┬──────┘                                    └──────────────┘
       │
       │N
       │
┌──────▼──────┐
│Application  │
└─────────────┘
```

---

## Entity Definitions

### Organization

The top-level customer entity containing tenants and users.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-gen | Unique identifier |
| `name` | String(255) | NOT NULL | Organization name |
| `created_at` | DateTime | NOT NULL, default=now | Creation timestamp |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | Last update timestamp |

**Relationships**:
- Has many Tenants (Tenant.organization_id → Organization.id)
- Has many Users (User.organization_id → Organization.id)

**Indexes**:
- `id` (primary key)

---

### Tenant

A branch or business unit within an organization. Subscriptions are scoped at the tenant level.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-gen | Unique identifier |
| `organization_id` | UUID | FK, NOT NULL, INDEX | Reference to Organization |
| `name` | String(255) | NOT NULL | Tenant name |
| `created_at` | DateTime | NOT NULL, default=now | Creation timestamp |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | Last update timestamp |

**Relationships**:
- Belongs to Organization (Tenant.organization_id → Organization.id)
- Has many Memberships (Membership.tenant_id → Tenant.id)
- Has many Subscriptions (Subscription.tenant_id → Tenant.id)

**Indexes**:
- `id` (primary key)
- `organization_id` (foreign key, for org-wide queries)

**Constraints**:
- FK: `organization_id` REFERENCES `organization(id)` ON DELETE CASCADE

---

### User

A person authenticated via OIDC. Each user belongs to exactly one organization.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-gen | Unique identifier |
| `organization_id` | UUID | FK, NOT NULL, INDEX | Reference to Organization |
| `idp_sub` | String(255) | NOT NULL, UNIQUE, INDEX | Identity provider subject (OIDC) |
| `email` | String(255) | NOT NULL, INDEX | User email |
| `name` | String(255) | NOT NULL | User display name |
| `last_login_at` | DateTime | NULLABLE | Last successful login timestamp |
| `status` | Enum | NOT NULL, default='active' | User status (active, inactive) |
| `created_at` | DateTime | NOT NULL, default=now | Creation timestamp |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | Last update timestamp |

**Relationships**:
- Belongs to Organization (User.organization_id → Organization.id)
- Has many Memberships (Membership.user_id → User.id)

**Indexes**:
- `id` (primary key)
- `organization_id` (foreign key, for org-wide queries)
- `idp_sub` (unique, for OIDC lookup)
- `email` (for user lookup by email)

**Constraints**:
- FK: `organization_id` REFERENCES `organization(id)` ON DELETE CASCADE
- UNIQUE: `idp_sub`

**Status Values**:
- `active`: User can authenticate and access resources
- `inactive`: User cannot authenticate (soft delete)

---

### Membership

An association between a user and a tenant with a specific role.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-gen | Unique identifier |
| `tenant_id` | UUID | FK, NOT NULL, INDEX | Reference to Tenant |
| `user_id` | UUID | FK, NOT NULL, INDEX | Reference to User |
| `role` | Enum | NOT NULL | User role in tenant |
| `created_at` | DateTime | NOT NULL, default=now | Creation timestamp |

**Relationships**:
- Belongs to Tenant (Membership.tenant_id → Tenant.id)
- Belongs to User (Membership.user_id → User.id)

**Indexes**:
- `id` (primary key)
- `tenant_id` (foreign key, for tenant member listing)
- `user_id` (foreign key, for user's tenant listing)
- `(tenant_id, user_id)` (unique, for idempotency)

**Constraints**:
- FK: `tenant_id` REFERENCES `tenant(id)` ON DELETE CASCADE
- FK: `user_id` REFERENCES `user(id)` ON DELETE CASCADE
- UNIQUE: `(tenant_id, user_id)`

**Role Values**:
- `org_admin`: Can manage all tenants within the organization
- `tenant_admin`: Can manage this specific tenant
- `tenant_member`: Read/launch access for this tenant

---

### Application

A product that tenants can subscribe to (e.g., PACS, ERP).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `app_key` | String(50) | PK, NOT NULL | Unique application key |
| `name` | String(255) | NOT NULL | Application display name |
| `launch_base_url` | String(500) | NOT NULL | Base URL for launch redirects |
| `status` | Enum | NOT NULL, default='active' | Application status |
| `created_at` | DateTime | NOT NULL, default=now | Creation timestamp |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | Last update timestamp |

**Relationships**:
- Has many Subscriptions (Subscription.app_key → Application.app_key)

**Indexes**:
- `app_key` (primary key)

**Status Values**:
- `active`: Available for subscription and launch
- `inactive`: Not available (existing subscriptions may remain active)

**Seed Data (MVP)**:
| app_key | name | launch_base_url | status |
|---------|------|-----------------|--------|
| `pacs` | PACS | `https://pacs.example.com/launch` | active |
| `erp` | ERP | `https://erp.example.com/launch` | active |

---

### Subscription

An entitlement that allows a tenant to access an application.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-gen | Unique identifier |
| `tenant_id` | UUID | FK, NOT NULL, INDEX | Reference to Tenant |
| `app_key` | String(50) | FK, NOT NULL, INDEX | Reference to Application |
| `status` | Enum | NOT NULL, default='active' | Subscription status |
| `started_at` | DateTime | NOT NULL, default=now | Subscription start timestamp |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | Last update timestamp |

**Relationships**:
- Belongs to Tenant (Subscription.tenant_id → Tenant.id)
- References Application (Subscription.app_key → Application.app_key)

**Indexes**:
- `id` (primary key)
- `tenant_id` (foreign key, for tenant subscription listing)
- `app_key` (for application lookup)
- `(tenant_id, app_key)` (unique, for idempotency)

**Constraints**:
- FK: `tenant_id` REFERENCES `tenant(id)` ON DELETE CASCADE
- FK: `app_key` REFERENCES `application(app_key)` ON DELETE CASCADE
- UNIQUE: `(tenant_id, app_key)`

**Status Values**:
- `active`: Tenant can launch the application
- `suspended`: Tenant cannot launch (admin action)
- `canceled`: Tenant cannot launch (permanent)

**Status Transitions**:
```
active ──→ suspended ──→ active
active ──→ canceled
suspended ──→ canceled
canceled (terminal state)
```

---

## Database Schema (DDL Reference)

### PostgreSQL Schema

```sql
-- Organizations
CREATE TABLE organization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tenants
CREATE TABLE tenant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tenant_organization ON tenant(organization_id);

-- Users
CREATE TABLE user_account (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    idp_sub VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    last_login_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_user_organization ON user_account(organization_id);
CREATE INDEX idx_user_idp_sub ON user_account(idp_sub);
CREATE INDEX idx_user_email ON user_account(email);

-- Memberships
CREATE TABLE membership (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);
CREATE INDEX idx_membership_tenant ON membership(tenant_id);
CREATE INDEX idx_membership_user ON membership(user_id);

-- Applications
CREATE TABLE application (
    app_key VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    launch_base_url VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscription (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    app_key VARCHAR(50) NOT NULL REFERENCES application(app_key) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, app_key)
);
CREATE INDEX idx_subscription_tenant ON subscription(tenant_id);
```

---

## SQLAlchemy Model Definitions

### Base Model

```python
# src/models/base.py
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

### Organization Model

```python
# src/models/organization.py
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class Organization(Base, TimestampMixin):
    __tablename__ = "organization"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid4()
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
```

---

## Cascade Delete Rules

| Entity | On Delete of Related | Action |
|--------|---------------------|--------|
| Tenant | Organization | CASCADE - Delete all tenants |
| User | Organization | CASCADE - Delete all users |
| Membership | Tenant | CASCADE - Delete all memberships |
| Membership | User | CASCADE - Delete all memberships |
| Subscription | Tenant | CASCADE - Delete all subscriptions |
| Subscription | Application | CASCADE - Delete all subscriptions |

**Note**: Organization deletion is a destructive action. In production, consider soft delete or preventing deletion of organizations with active data.

---

## Data Consistency Rules

### Organization Boundary Enforcement

- All queries for tenant/user data MUST filter by `organization_id`
- Client-supplied `organization_id` MUST NEVER be trusted
- Always derive `organization_id` from authenticated user

### Idempotency

- Membership creation: Check existing (tenant_id, user_id) before insert
- Subscription creation: Check existing (tenant_id, app_key) before insert
- Return existing record if found (no error)

### Role Validation

- `org_admin` role can only be assigned by system admins (not in MVP scope)
- `tenant_admin` and `tenant_member` can be assigned by org_admin or tenant_admin
- Users cannot have multiple roles for the same tenant

---

## Migration Strategy

Use Alembic for all schema changes:

1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review generated SQL
3. Apply migration: `alembic upgrade head`
4. Rollback if needed: `alembic downgrade -1`

**Order of Operations** (initial schema):
1. Create `organization` table
2. Create `tenant` table (depends on organization)
3. Create `user_account` table (depends on organization)
4. Create `application` table (independent)
5. Create `membership` table (depends on tenant, user_account)
6. Create `subscription` table (depends on tenant, application)
7. Create indexes
8. Seed application data (PACS, ERP)
