# Feature Spec: Admin Seed + Config

**Feature ID**: `09-admin-seed-config`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Provides administrative endpoints for application management, health checks, and configuration validation. Ensures the Control Plane can be properly seeded with applications and fails fast on misconfiguration.

## Clarifications

| Question | Decision |
|----------|----------|
| App seeding | API endpoint (`POST /v1/admin/apps`) |
| Health checks | `/health` only (liveness) |
| Migrations | Manual (alembic) |
| Config validation | Fail fast on startup |

## Endpoints

### `GET /health`

Simple liveness probe for k8s/deployment health checks.

**Authentication**: None required

#### Response

**200 OK**

```json
{
  "status": "healthy",
  "timestamp": "2026-02-14T10:30:00Z"
}
```

**503 Service Unavailable** (if database/connection issues)

```json
{
  "status": "unhealthy",
  "error": "Database connection failed",
  "timestamp": "2026-02-14T10:30:00Z"
}
```

#### Behavior

1. Check database connectivity (simple `SELECT 1`)
2. Return 200 if connected, 503 if not

---

### `POST /v1/admin/apps`

Create or update an application in the catalog.

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` only (or service account)

#### Request

```json
{
  "app_key": "pacs",
  "name": "PACS",
  "base_url": "http://localhost:8001",
  "status": "active"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `app_key` | string | Yes | Unique application identifier |
| `name` | string | Yes | Display name |
| `base_url` | string | Yes | Application base URL |
| `status` | string | No | `active` (default) or `inactive` |

#### Response

**201 Created** (new app)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "app_key": "pacs",
  "name": "PACS",
  "base_url": "http://localhost:8001",
  "status": "active",
  "created_at": "2026-02-14T10:30:00Z"
}
```

**200 OK** (updated existing)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "app_key": "pacs",
  "name": "PACS Pro",
  "base_url": "http://localhost:8001",
  "status": "active",
  "created_at": "2026-02-01T09:00:00Z",
  "updated": true
}
```

#### Behavior

1. Validate user is `org_admin` (or service account)
2. Validate request body
3. Upsert by `app_key`:
   - If exists → update name/base_url/status
   - If not exists → create new
4. Return app with appropriate status code

---

### `GET /v1/admin/apps`

List all applications (including inactive).

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` only

#### Response

**200 OK**

```json
{
  "applications": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "app_key": "pacs",
      "name": "PACS",
      "base_url": "http://localhost:8001",
      "status": "active",
      "created_at": "2026-02-01T09:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "app_key": "erp",
      "name": "ERP",
      "base_url": "http://localhost:8002",
      "status": "active",
      "created_at": "2026-02-01T09:00:00Z"
    }
  ]
}
```

---

### `DELETE /v1/admin/apps/{app_key}`

Deactivate (soft delete) an application.

**Authentication**: Required (Bearer token)
**Authorization**: `org_admin` only

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `app_key` | string | Application key |

#### Response

**204 No Content**

#### Behavior

1. Validate user is `org_admin`
2. Set application `status = inactive`
3. Return 204

**Note**: This is a soft delete. The app record is retained but won't appear in public catalog.

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/control_plane` |
| `KEYCLOAK_URL` | Keycloak base URL | `http://localhost:18080` |
| `KEYCLOAK_REALM` | Keycloak realm | `control-plane` |
| `KEYCLOAK_CLIENT_ID` | OIDC client ID | `control-plane` |
| `KEYCLOAK_CLIENT_SECRET` | OIDC client secret | `abc123...` |
| `LAUNCH_JWT_SECRET` | Shared secret for Launch JWT | `min-32-char-secret` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ONBOARDING_TTL_MINUTES` | Onboarding session TTL | `60` |
| `LAUNCH_JWT_TTL_MINUTES` | Launch JWT TTL | `5` |
| `TRIAL_DURATION_DAYS` | Trial subscription duration | `14` |

### Startup Validation

On application startup, validate:

1. **Database Connection**
   - Attempt connection to `DATABASE_URL`
   - Exit with error if unreachable

2. **Keycloak Reachability**
   - Attempt to fetch JWKS from `{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs`
   - Exit with error if unreachable (fail fast)

3. **Required Secrets**
   - Validate `LAUNCH_JWT_SECRET` is at least 32 characters
   - Exit with error if missing or too short

4. **Configuration Sanity**
   - Validate `ONBOARDING_TTL_MINUTES` is positive
   - Validate `TRIAL_DURATION_DAYS` is positive

**Example startup error**:

```
ERROR: Configuration validation failed:
  - DATABASE_URL: Connection refused
  - LAUNCH_JWT_SECRET: Must be at least 32 characters (got 10)
Exiting...
```

## Database Migrations

Migrations are managed via **Alembic** and run manually.

### Commands

```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Add subscription table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Migration Files

Migration files are stored in `alembic/versions/` and version-controlled.

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `FORBIDDEN` | 403 | User lacks admin role |
| `APP_KEY_EXISTS` | 409 | App key already exists (on create) |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `CONFIG_ERROR` | 500 | Configuration validation failed |

## Acceptance Criteria

- [ ] `GET /health` returns 200 when database connected
- [ ] `GET /health` returns 503 when database unreachable
- [ ] `POST /v1/admin/apps` creates new application
- [ ] `POST /v1/admin/apps` updates existing application (upsert by app_key)
- [ ] `GET /v1/admin/apps` lists all applications including inactive
- [ ] `DELETE /v1/admin/apps/{app_key}` deactivates application
- [ ] App exits immediately if required configs missing
- [ ] App exits immediately if database unreachable
- [ ] App exits immediately if Keycloak unreachable
- [ ] Alembic migrations documented and functional

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-030 | Application seeding via API |
| NFR-005 | Configuration validation |

## Dependencies

- Database connectivity
- Keycloak reachability
- Alembic for migrations
