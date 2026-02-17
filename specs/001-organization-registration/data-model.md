# Data Model: Organization Registration

**Feature**: 001-organization-registration
**Date**: 2026-02-17

## Entity Relationship Diagram

```
┌─────────────────────┐
│    Registration     │
│─────────────────────│
│ id (PK)             │
│ organization_id(FK) │───┐
│ admin_email         │   │
│ admin_first_name    │   │
│ admin_last_name     │   │
│ admin_phone         │   │
│ status              │   │
│ invite_status       │   │
│ invite_error        │   │
│ idempotency_key     │   │
│ ip_address          │   │
│ correlation_id      │   │
│ created_at          │   │
│ updated_at          │   │
│ deleted_at          │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│    Organization     │◄──┘
│─────────────────────│
│ id (PK)             │
│ name                │
│ slug (UNIQUE)       │
│ status              │
│ trial_plan          │
│ trial_assigned_at   │
│ trial_starts_at     │
│ trial_ends_at       │
│ terms_version       │
│ privacy_version     │
│ accepted_at         │
│ accepted_locale     │
│ country_code        │
│ created_at          │
│ updated_at          │
│ deleted_at          │
└─────────────────────┘
```

## Entities

### Organization (Extended)

**Purpose**: Represents a customer's business entity. Extended to support registration flow.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Primary key |
| name | VARCHAR(100) | NOT NULL | Display name |
| slug | VARCHAR(120) | UNIQUE, NOT NULL, INDEX | URL-safe identifier |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending_invite' | Organization status |
| trial_plan | VARCHAR(20) | NULL | Trial plan type (e.g., 'trial') |
| trial_assigned_at | TIMESTAMP | NULL | When trial was assigned |
| trial_starts_at | TIMESTAMP | NULL | When trial clock starts (set at activation) |
| trial_ends_at | TIMESTAMP | NULL | When trial expires (set at activation) |
| terms_version | VARCHAR(20) | NULL | ToS version accepted |
| privacy_version | VARCHAR(20) | NULL | Privacy policy version accepted |
| accepted_at | TIMESTAMP | NULL | When legal terms accepted |
| accepted_locale | VARCHAR(10) | NULL | BCP 47 locale at acceptance |
| country_code | VARCHAR(2) | NOT NULL | ISO 3166-1 alpha-2 country code |
| created_at | TIMESTAMP | NOT NULL, auto | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, auto | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Status Values**:
| Status | Description |
|--------|-------------|
| pending_invite | Registration complete, awaiting IdP verification |
| active | Organization activated (US-CP-002) |
| suspended | Admin-suspended (separate feature) |

**Indexes**:
- `ix_organizations_slug` on `slug`
- `ix_organizations_status` on `status`
- `ix_organizations_created_at` on `created_at` (for cleanup queries)

**Constraints**:
- `uq_organizations_slug` UNIQUE on `slug`

### Registration (New)

**Purpose**: Tracks the registration process and stores admin details before IdP user creation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Registration ID (returned to client) |
| organization_id | UUID | FK → organizations.id, NOT NULL | Linked organization |
| admin_email | VARCHAR(255) | NOT NULL, INDEX | Admin email address |
| admin_first_name | VARCHAR(100) | NOT NULL | Admin first name |
| admin_last_name | VARCHAR(100) | NOT NULL | Admin last name |
| admin_phone | VARCHAR(20) | NULL | Admin phone (E.164 format) |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Registration status |
| invite_status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | IdP invite status |
| invite_error | TEXT | NULL | Error message if invite failed |
| invite_attempted_at | TIMESTAMP | NULL | When invite was last attempted |
| idempotency_key | VARCHAR(64) | NULL, INDEX | Client-provided idempotency key |
| ip_address | VARCHAR(45) | NOT NULL | Client IP address |
| user_agent | TEXT | NULL | Client user agent |
| correlation_id | UUID | NOT NULL | Request correlation ID |
| created_at | TIMESTAMP | NOT NULL, auto | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, auto | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete (cleanup redacts PII) |

**Status Values**:
| Status | Description |
|--------|-------------|
| pending | Registration in progress |
| completed | Registration complete, invite sent |
| failed | Registration failed (invite failed) |
| expired | Registration expired, PII redacted |

**Invite Status Values**:
| Status | Description |
|--------|-------------|
| pending | Invite not yet attempted |
| sent | Invite sent successfully |
| failed | Invite failed |
| resent | Invite re-sent after failure |

**Indexes**:
- `ix_registrations_organization_id` on `organization_id`
- `ix_registrations_admin_email` on `admin_email`
- `ix_registrations_status` on `status`
- `ix_registrations_idempotency_key` on `idempotency_key`
- `ix_registrations_created_at` on `created_at` (for cleanup)

**Constraints**:
- `fk_registrations_organization` FOREIGN KEY on `organization_id`

## Validation Rules

### Organization

| Field | Rule |
|-------|------|
| name | 1-100 characters, required |
| slug | Auto-generated from name, lowercase alphanumeric + hyphens, unique |
| status | One of: pending_invite, active, suspended |
| country_code | ISO 3166-1 alpha-2, required |
| trial_plan | 'trial' for new registrations |
| accepted_at | Required for completed registration |
| terms_version | Required if accepted_at present |
| privacy_version | Required if accepted_at present |

### Registration

| Field | Rule |
|-------|------|
| admin_email | Valid email format, max 255 chars, required |
| admin_first_name | 1-100 characters, required |
| admin_last_name | 1-100 characters, required |
| admin_phone | E.164 format if provided, optional |
| idempotency_key | 1-64 characters, optional |
| ip_address | Valid IPv4 or IPv6, required |

## State Transitions

### Organization Status

```
                    ┌─────────────────┐
                    │ pending_invite  │
                    └────────┬────────┘
                             │
                             │ IdP verification (US-CP-002)
                             ▼
                    ┌─────────────────┐
                    │     active      │
                    └────────┬────────┘
                             │
                             │ Admin action (separate feature)
                             ▼
                    ┌─────────────────┐
                    │    suspended    │
                    └─────────────────┘
```

### Registration Status

```
┌──────────┐     submit      ┌───────────┐
│ (start)  │ ──────────────► │  pending  │
└──────────┘                 └─────┬─────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              │
             invite sent    invite fails         │
                    │              │              │
                    ▼              ▼              │
             ┌───────────┐  ┌───────────┐        │
             │ completed │  │   failed  │◄───────┘
             └───────────┘  └─────┬─────┘  retry/resend
                                   │
                                   │ 7 days
                                   ▼
                            ┌───────────┐
                            │  expired  │
                            └───────────┘
```

## Database Migrations

### Migration 1: Extend organizations table

```sql
-- Add new columns to organizations
ALTER TABLE organizations
ADD COLUMN slug VARCHAR(120) UNIQUE,
ADD COLUMN trial_plan VARCHAR(20),
ADD COLUMN trial_assigned_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN trial_starts_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN trial_ends_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN terms_version VARCHAR(20),
ADD COLUMN privacy_version VARCHAR(20),
ADD COLUMN accepted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN accepted_locale VARCHAR(10),
ADD COLUMN country_code VARCHAR(2) NOT NULL DEFAULT 'US';

-- Create indexes
CREATE INDEX ix_organizations_slug ON organizations(slug);
CREATE INDEX ix_organizations_status ON organizations(status);

-- Update existing records (if any)
UPDATE organizations SET
  slug = LOWER(REGEXP_REPLACE(name, '[^a-z0-9]+', '-', 'g')),
  status = 'active',
  country_code = 'US'
WHERE slug IS NULL;
```

### Migration 2: Create registrations table

```sql
CREATE TABLE registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    admin_email VARCHAR(255) NOT NULL,
    admin_first_name VARCHAR(100) NOT NULL,
    admin_last_name VARCHAR(100) NOT NULL,
    admin_phone VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    invite_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    invite_error TEXT,
    invite_attempted_at TIMESTAMP WITH TIME ZONE,
    idempotency_key VARCHAR(64),
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    correlation_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX ix_registrations_organization_id ON registrations(organization_id);
CREATE INDEX ix_registrations_admin_email ON registrations(admin_email);
CREATE INDEX ix_registrations_status ON registrations(status);
CREATE INDEX ix_registrations_idempotency_key ON registrations(idempotency_key);
CREATE INDEX ix_registrations_created_at ON registrations(created_at);
```
