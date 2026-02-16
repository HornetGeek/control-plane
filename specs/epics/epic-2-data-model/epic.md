# EPIC 2 — CP Registry Data Model

**Epic ID**: `epic-2-data-model`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-15
**Priority**: P0 (Foundation)
**Depends On**: EPIC 0 (Alembic bootstrap)

## Goal

Implement CP as system-of-record for SaaS registry entities with proper lifecycle management.

## Features

### F2.1 Entities + Migrations (UUID PKs)

All entities use UUID primary keys.

#### Applications

```python
class Application:
    id: UUID
    app_key: str          # Unique key: "pacs", "erp"
    name: str             # Display name
    base_url: str         # App URL for redirects
    status: str           # "active" | "disabled"
    deleted_at: datetime  # Soft delete
    created_at: datetime
    updated_at: datetime
```

#### Organizations

```python
class Organization:
    id: UUID
    name: str             # Unique organization name
    status: str           # "active" | "disabled"
    deleted_at: datetime  # Soft delete
    created_at: datetime
    updated_at: datetime
```

#### Tenants

```python
class Tenant:
    id: UUID
    org_id: UUID          # FK to Organization
    name: str             # Tenant/branch name
    name_normalized: str  # Lowercase, for uniqueness check
    status: str           # "active" | "disabled"
    sync_status: str      # "synced" | "pending" | "failed"
    deleted_at: datetime  # Soft delete
    created_at: datetime
    updated_at: datetime

    # Constraints
    UNIQUE(org_id, name_normalized)
```

#### Subscriptions

```python
class Subscription:
    id: UUID
    tenant_id: UUID       # FK to Tenant
    app_id: UUID          # FK to Application
    status: str           # "trial" | "active" | "disabled"
    trial_ends_at: datetime
    deleted_at: datetime  # Soft delete
    created_at: datetime
    updated_at: datetime

    # Constraints
    UNIQUE(tenant_id, app_id)
```

### F2.2 Soft Delete + Status

**Status Field**:
- `active` - Normal operational state
- `disabled` - Temporarily suspended (can be re-enabled)

**Soft Delete**:
- `deleted_at` timestamp (NULL = not deleted)
- Default queries exclude deleted records
- Deleted records preserved for audit/recovery

**Query Pattern**:
```python
# Default scope excludes deleted
session.scalars(
    select(Organization)
    .where(Organization.deleted_at.is_(None))
)

# Include deleted (admin use)
session.scalars(
    select(Organization)
    .with_deleted()  # Custom query method
)
```

### F2.3 sync_status Field

For entities that depend on Core synchronization:

| Status | Meaning |
|--------|---------|
| `synced` | Successfully synced with Core |
| `pending` | Sync pending (initial state or retry needed) |
| `failed` | Sync failed after retries |

**MVP Note**: For MVP, sync calls are stubbed. The `sync_status` field is set but the actual sync is logged only.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-2.1 | All entities MUST use UUID primary keys |
| FR-2.2 | All entities MUST have `status` field |
| FR-2.3 | All entities MUST have `deleted_at` for soft delete |
| FR-2.4 | Default list queries MUST exclude soft-deleted records |
| FR-2.5 | Tenant uniqueness MUST be enforced per org |
| FR-2.6 | Subscription uniqueness MUST be enforced per tenant+app |
| FR-2.7 | sync_status MUST track Core sync state |

## Migrations

```bash
# Initial migration
alembic revision --autogenerate -m "Initial schema: apps, orgs, tenants, subscriptions"

# Apply
alembic upgrade head
```

## Database Schema

```sql
-- Applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    name_normalized VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    sync_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, name_normalized)
);
CREATE INDEX idx_tenants_org_id ON tenants(org_id);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    app_id UUID NOT NULL REFERENCES applications(id),
    status VARCHAR(20) NOT NULL DEFAULT 'trial',
    trial_ends_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, app_id)
);
CREATE INDEX idx_subscriptions_tenant_id ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_app_id ON subscriptions(app_id);
```

## Acceptance Criteria

- [ ] All migrations run successfully
- [ ] UUID PKs generated automatically
- [ ] Soft delete works (deleted_at set, excluded from queries)
- [ ] Status field accepts valid values only
- [ ] UNIQUE constraints enforced
- [ ] sync_status defaults to "pending"
- [ ] Timestamps auto-managed

## Dependencies

- EPIC 0 (Alembic bootstrap)

## Deliverables

- [ ] Migrations + seed framework operational
- [ ] All entities creatable via tests
