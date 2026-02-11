# Data Model: OIDC Authentication

**Feature**: 002-oidc-auth
**Date**: 2026-02-11

## Overview

This document defines the data model for OIDC authentication, including entities, relationships, validation rules, and state transitions.

## Entities

### User

Represents a person authenticated via OIDC. Belongs to exactly one organization.

**Table**: `user_account`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key, Default: uuid_generate_v4() | Internal unique identifier |
| `organization_id` | UUID | Foreign Key → organization.id, NOT NULL, Indexed | Organization this user belongs to |
| `idp_sub` | String(255) | NOT NULL, UNIQUE, Indexed | Identity Provider subject (OIDC `sub` claim) |
| `email` | String(255) | NOT NULL, Indexed | User's email address |
| `name` | String(255) | NOT NULL | User's display name |
| `last_login_at` | Timestamptz | Nullable | Timestamp of most recent successful login |
| `status` | String(20) | NOT NULL, Default: 'active' | User status (active/inactive) |
| `created_at` | Timestamptz | NOT NULL, Default: now() | Record creation timestamp |
| `updated_at` | Timestamptz | NOT NULL, Default: now() | Record update timestamp |

**Indexes**:
- Primary key: `id`
- Unique index: `idp_sub` (for O(1) user lookup by IdP subject)
- Index: `organization_id` (for listing users by organization)
- Index: `email` (for user lookup by email)

**Constraints**:
- `idp_sub` must be unique across all users (enforced at database level)
- `organization_id` foreign key with CASCADE delete (if org deleted, users deleted)

**Relationships**:
- Belongs to: `Organization` (many-to-one)
- Has many: `Membership` (via user_id) - defined in separate feature

**Validation Rules**:
- `idp_sub`: Maximum 255 characters (OIDC spec allows long strings)
- `email`: Must be valid email format
- `name`: Cannot be empty
- `status`: Must be one of ['active', 'inactive']

---

### Organization

Top-level customer entity containing users and tenants.

**Table**: `organization`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key, Default: uuid_generate_v4() | Internal unique identifier |
| `name` | String(255) | NOT NULL | Organization name |
| `created_at` | Timestamptz | NOT NULL, Default: now() | Record creation timestamp |
| `updated_at` | Timestamptz | NOT NULL, Default: now() | Record update timestamp |

**Relationships**:
- Has many: `User` (one-to-many via organization_id)

**Note**: Organization creation is out of scope for this feature. Organizations are expected to exist before user authentication.

---

## State Transitions

### User Status

```
                    ┌─────────────┐
                    │   (new)     │
                    └──────┬──────┘
                           │
                           │ auto-provision
                           │ on first login
                           ▼
                    ┌─────────────┐
    ┌───────────────│   active    │───────────────┐
    │               └─────────────┘               │
    │                                              │
    │                                              │ admin action
    │                                              │ (future feature)
    │                                              ▼
    │               ┌─────────────┐
    └───────────────│  inactive   │
                    └─────────────┘
```

**Transitions**:
1. **(none) → active**: Occurs automatically on first successful OIDC authentication
2. **active → inactive**: Admin action (not implemented in this feature)
3. **inactive → active**: Admin action (not implemented in this feature)

**Login Behavior by Status**:
- `active`: Login proceeds, `last_login_at` updated
- `inactive`: Login rejected with 403 Forbidden (future enhancement)

---

## Entity Relationships Diagram

```
┌──────────────────┐
│  Organization    │
│  ──────────────  │
│  id: UUID        │
│  name: string    │
└────────┬─────────┘
         │ 1
         │
         │ N
┌────────▼─────────┐
│     User         │
│  ──────────────  │
│  id: UUID        │
│  organization_id │
│  idp_sub: string │
│  email: string   │
│  name: string    │
│  status: enum    │
└──────────────────┘
```

---

## Data Access Patterns

### User Lookup by IdP Subject (Primary)

**Use Case**: OIDC callback - find or create user after token validation

**Query**:
```sql
SELECT * FROM user_account WHERE idp_sub = $1;
```

**Result**:
- Found: Return existing user, update `last_login_at`
- Not found: Create new user with provided claims

### User Lookup by ID

**Use Case**: /auth/me endpoint - retrieve current user info

**Query**:
```sql
SELECT * FROM user_account WHERE id = $1;
```

### Users by Organization

**Use Case**: Admin lists all users in their organization

**Query**:
```sql
SELECT * FROM user_account WHERE organization_id = $1 ORDER BY created_at DESC;
```

---

## Constraints and Guarantees

### Uniqueness

- `idp_sub` is globally unique (enforced by database unique constraint)
- A user from one IdP cannot share the same `idp_sub` as a user from another IdP

### Immutability

- `idp_sub` is immutable once set (user's identity is tied to IdP subject)
- `organization_id` is immutable after user creation (user cannot change organizations)

### Data Integrity

- `organization_id` references an existing organization (foreign key)
- Cascade delete: deleting an organization deletes all its users

---

## Migration Notes

### Initial Migration

Create tables with the following order:
1. `organization` (must exist first for FK reference)
2. `user_account` (references organization)

### Rollback Considerations

- Dropping `user_account` before `organization` (due to FK)
- Consider data retention policies if organizations are deleted

---

## Performance Considerations

### Index Strategy

- `idp_sub` unique index: Critical for login performance (O(1) lookup)
- `organization_id` index: Enables efficient org-scoped user lists
- `email` index: Supports future user lookup by email

### Query Optimization

- Use indexed columns in WHERE clauses
- Avoid SELECT * for list queries (specify required columns)
- Consider pagination for organization user lists (future enhancement)

---

## Security Considerations

### Sensitive Data

- `idp_sub` is sensitive (links to external IdP account)
- Access tokens and ID tokens are NOT stored in database
- Tokens are validated and discarded; only claims are persisted

### PII (Personally Identifiable Information)

- `email` and `name` contain PII
- Ensure appropriate access controls and audit logging
- Consider GDPR/data retention requirements

### SQL Injection Prevention

- All queries must use parameterized statements
- SQLAlchemy async handles this automatically with proper query construction
