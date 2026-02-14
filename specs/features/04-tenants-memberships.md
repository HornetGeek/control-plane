# Feature Spec: Orgs/Tenants/Memberships

**Feature ID**: `04-tenants-memberships`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Manages organizations, tenants (branches within organizations), and user memberships. Organizations are top-level customer entities. Tenants represent branches/divisions within an organization. Memberships link users to tenants with specific roles.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-016 | System MUST enforce `UNIQUE(org_id, tenant_name)` constraint |
| FR-017 | System MUST allow `org_admin` to create tenants within their organization |
| FR-018 | System MUST allow users to list tenants they are members of |
| FR-019 | System MUST allow `org_admin` and `tenant_admin` to add users to tenants |
| FR-020 | System MUST assign role (`org_admin`, `tenant_admin`, `tenant_member`) to memberships |
| FR-021 | System MUST reject membership modifications by `tenant_member` |

## Clarifications

| Question | Decision |
|----------|----------|
| First user role | `org_admin` (set during onboarding) |
| Orphaned users allowed | Yes, user can have zero tenant memberships |

## Roles

| Role | Permissions |
|------|-------------|
| `org_admin` | Create tenants, add members to any tenant in org, manage all subscriptions |
| `tenant_admin` | Add/remove members to their tenant, manage tenant subscriptions |
| `tenant_member` | Access tenant resources, launch applications |

## Endpoints

### `POST /v1/tenants`

Create a new tenant within the authenticated user's organization.

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` only

#### Request

```json
{
  "name": "West Coast Branch"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tenant name (3-50 chars, alphanumeric + spaces/hyphens) |

#### Response

**201 Created**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "org_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "West Coast Branch",
  "created_at": "2026-02-14T10:30:00Z"
}
```

#### Behavior

1. Validate user is `org_admin`
2. Validate `name` format (3-50 chars, alphanumeric + spaces/hyphens)
3. Check `UNIQUE(org_id, tenant_name)` constraint
4. Create tenant
5. Return created tenant

---

### `GET /v1/tenants`

List all tenants the authenticated user is a member of.

**Authentication**: Required (Bearer token)

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page (max 100) |

#### Response

**200 OK**

```json
{
  "tenants": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "org_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Headquarters",
      "role": "org_admin",
      "member_count": 5,
      "created_at": "2026-02-01T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3
  }
}
```

#### Behavior

1. Look up all memberships for authenticated user
2. Join with tenant and organization data
3. Return paginated list with user's role in each tenant

---

### `GET /v1/tenants/{id}`

Get details of a specific tenant.

**Authentication**: Required (Bearer token)
**Authorization**: Must be member of tenant

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tenant ID |

#### Response

**200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "org_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Headquarters",
  "created_at": "2026-02-01T09:00:00Z",
  "subscriptions": [
    {
      "app_id": "550e8400-e29b-41d4-a716-446655440002",
      "app_name": "PACS",
      "status": "trial",
      "trial_ends_at": "2026-02-15T09:00:00Z"
    }
  ]
}
```

#### Behavior

1. Validate user is member of tenant
2. Load tenant with subscriptions
3. Return tenant details

---

### `POST /v1/tenants/{id}/members`

Add a user to a tenant.

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` or `tenant_admin` of this tenant

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tenant ID |

#### Request

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "tenant_member"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | UUID | Yes | User to add |
| `role` | string | Yes | `tenant_admin` or `tenant_member` |

#### Response

**201 Created**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "tenant_member",
  "created_at": "2026-02-14T10:30:00Z"
}
```

#### Behavior

1. Validate user is `org_admin` or `tenant_admin` of this tenant
2. Validate target user exists and is in same organization
3. Validate role is valid (`tenant_admin` or `tenant_member`)
4. Check membership doesn't already exist
5. Create membership
6. Return created membership

---

### `GET /v1/tenants/{id}/members`

List members of a tenant.

**Authentication**: Required (Bearer token)
**Authorization**: Must be member of tenant

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tenant ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page (max 100) |

#### Response

**200 OK**

```json
{
  "members": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "user_id": "550e8400-e29b-41d4-a716-446655440003",
      "user_name": "John Doe",
      "user_email": "john@example.com",
      "role": "tenant_member",
      "created_at": "2026-02-14T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5
  }
}
```

#### Behavior

1. Validate user is member of tenant
2. Load all memberships for tenant with user details
3. Return paginated list

---

### `DELETE /v1/tenants/{id}/members/{user_id}`

Remove a user from a tenant.

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` or `tenant_admin` of this tenant

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tenant ID |
| `user_id` | UUID | User ID to remove |

#### Response

**204 No Content**

#### Behavior

1. Validate user is `org_admin` or `tenant_admin` of this tenant
2. Validate membership exists
3. Cannot remove the last `org_admin` from org (business rule)
4. Delete membership
5. Return 204

**Note**: User becomes "orphaned" if they have no more memberships, but user record is retained.

## Entities

### Organization

```python
class Organization:
    id: UUID
    name: str            # Globally unique
    created_at: datetime
```

### Tenant

```python
class Tenant:
    id: UUID
    org_id: UUID         # Parent organization
    name: str            # Unique within org
    created_at: datetime
```

**Constraint**: `UNIQUE(org_id, name)`

### Membership

```python
class Membership:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str            # org_admin | tenant_admin | tenant_member
    created_at: datetime
```

**Constraint**: `UNIQUE(tenant_id, user_id)`

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `FORBIDDEN` | 403 | User lacks required role |
| `NOT_TENANT_MEMBER` | 403 | User not member of tenant |
| `TENANT_NAME_EXISTS` | 409 | Tenant name already in org |
| `TENANT_NOT_FOUND` | 404 | Tenant not found |
| `USER_NOT_FOUND` | 404 | User not found |
| `MEMBERSHIP_EXISTS` | 409 | User already member of tenant |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `CROSS_ORG_ACCESS` | 403 | Cannot add user from different org |
| `LAST_ADMIN` | 400 | Cannot remove last admin |

## Acceptance Criteria

- [ ] `org_admin` can create tenants within their organization
- [ ] `UNIQUE(org_id, tenant_name)` constraint enforced
- [ ] Users can list tenants they are members of
- [ ] Users can view tenant details (if member)
- [ ] `org_admin` and `tenant_admin` can add members
- [ ] `org_admin` and `tenant_admin` can remove members
- [ ] `tenant_member` cannot add/remove members
- [ ] User can have zero memberships (orphaned)
- [ ] First user during onboarding gets `org_admin` role
- [ ] Cross-organization access blocked

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-016 | UNIQUE(org_id, tenant_name) constraint |
| FR-017 | org_admin creates tenants |
| FR-018 | Users list their tenant memberships |
| FR-019 | org_admin/tenant_admin add members |
| FR-020 | Role assignment on membership |
| FR-021 | tenant_member blocked from member management |

## Dependencies

- Feature `03-oidc-auth-keycloak` (for user authentication)
