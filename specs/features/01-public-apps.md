# Feature Spec: Public App Catalog

**Feature ID**: `01-public-apps`
**Parent Spec**: `specs/001-control-plane-mvp/spec.md`
**Status**: Draft
**Created**: 2026-02-14

## Overview

Provides a public, unauthenticated endpoint for listing available SaaS applications. This endpoint is used during the onboarding flow to allow users to select an application before login.

## Requirements

| ID | Requirement |
|----|-------------|
| FR-029 | System MUST provide read-only catalog of available applications |
| FR-030 | System MUST seed initial applications (PACS, ERP) on startup |

## Endpoint

### `GET /v1/applications`

List all active applications in the catalog.

**Authentication**: None required (public endpoint)

#### Request

No request body required.

#### Response

**200 OK**

```json
{
  "applications": [
    {
      "app_key": "pacs",
      "name": "PACS",
      "base_url": "http://localhost:8001"
    },
    {
      "app_key": "erp",
      "name": "ERP",
      "base_url": "http://localhost:8002"
    }
  ]
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `applications` | array | List of active applications |
| `applications[].app_key` | string | Unique application identifier (used in onboarding) |
| `applications[].name` | string | Display name of the application |
| `applications[].base_url` | string | Base URL for the application (used in launch redirect) |

#### Behavior

- **Filtering**: Only applications with `status=active` are returned
- **Ordering**: No specific ordering guaranteed (MVP)
- **Fields**: Minimal fields only (no descriptions, metadata, etc.)

## Entity: Application

```python
class Application:
    id: UUID
    app_key: str       # Unique key (e.g., "pacs", "erp")
    name: str          # Display name
    base_url: str      # Application base URL
    status: str        # "active" | "inactive"
    created_at: datetime
```

### Constraints

- `app_key` must be unique
- `base_url` must be a valid URL

## Data Seeding

On application startup, the following applications MUST be seeded if not present:

| app_key | name | base_url | status |
|---------|------|----------|--------|
| `pacs` | PACS | `http://localhost:8001` | active |
| `erp` | ERP | `http://localhost:8002` | active |

**Implementation Note**: Use an idempotent upsert pattern to avoid duplicate entries on restart.

## Error Codes

This endpoint does not define custom error codes. Standard HTTP errors apply:

| HTTP | Description |
|------|-------------|
| 500 | Internal server error |

## Acceptance Criteria

- [ ] `GET /v1/applications` returns all applications with `status=active`
- [ ] Applications with `status=inactive` are not included in response
- [ ] Response contains only `app_key`, `name`, `base_url` (minimal fields)
- [ ] No authentication required to access this endpoint
- [ ] PACS and ERP applications are seeded on startup
- [ ] Seeding is idempotent (restart-safe)

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-029 | Endpoint returns application catalog |
| FR-030 | Startup seeding of PACS and ERP |

## Dependencies

None (this is the first feature in the onboarding flow).
