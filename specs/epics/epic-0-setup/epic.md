# EPIC 0 — Spec-Kit Setup & Engineering Baseline

**Epic ID**: `epic-0-setup`
**Parent**: [../../master.md](../../master.md)
**Status**: Draft
**Created**: 2026-02-15
**Priority**: P0 (Foundation)

## Goal

Establish repo conventions, spec structure, and runnable service baseline with observability and infrastructure.

## Features

### F0.1 Specs Structure

Create the specification file structure:

```
specs/
├── master.md
└── epics/
    ├── epic-0-setup/
    ├── epic-1-security-authz/
    ├── epic-2-data-model/
    ├── epic-3-applications/
    ├── epic-4-organizations/
    ├── epic-5-tenants-sync/
    ├── epic-6-subscriptions-trial/
    ├── epic-7-dashboard/
    └── epic-8-users-listing/
```

### F0.2 FastAPI Skeleton + Routing/Versioning

- FastAPI application factory pattern
- Router versioning under `/v1/` prefix
- Health/readiness endpoints
- CORS middleware configuration
- Error handling middleware

### F0.3 Observability Baseline

- Request ID middleware (`X-Request-ID` header)
- Structured JSON logging to stdout
- `/healthz` - liveness probe
- `/readyz` - readiness probe (checks DB + Redis)

### F0.4 Postgres + Alembic Bootstrap

- SQLAlchemy 2.0 async engine setup
- Alembic migrations framework
- Database connection pooling
- Async session management

### F0.5 Redis Bootstrap

- Redis client initialization
- Connection health check
- Ready for authorization caching (EPIC 1)

## Requirements

| ID | Requirement |
|----|-------------|
| FR-0.1 | Service MUST start and respond to health checks |
| FR-0.2 | All endpoints MUST be versioned under `/v1/` |
| FR-0.3 | Request ID MUST be generated if not provided |
| FR-0.4 | Logs MUST be structured JSON to stdout |
| FR-0.5 | Database migrations MUST run via Alembic |
| FR-0.6 | Redis connection MUST be validated on startup |

## Endpoints

### `GET /healthz`

Liveness probe - returns 200 if service is running.

**Response**: `200 OK`
```json
{ "status": "healthy" }
```

### `GET /readyz`

Readiness probe - returns 200 if all dependencies are connected.

**Response**: `200 OK`
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

**Response**: `503 Service Unavailable`
```json
{
  "status": "not_ready",
  "checks": {
    "database": "ok",
    "redis": "failed"
  }
}
```

## Project Structure

```
src/
├── __init__.py
├── main.py                 # FastAPI app factory
├── config.py               # Settings via environment
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py       # v1 router
│   │   └── health.py       # /healthz, /readyz
│   └── deps.py             # Common dependencies
├── core/
│   ├── __init__.py
│   ├── logging.py          # Structured logging config
│   └── middleware.py       # Request ID middleware
├── db/
│   ├── __init__.py
│   ├── session.py          # Async session management
│   └── base.py             # SQLAlchemy base
└── cache/
    ├── __init__.py
    └── redis.py            # Redis client

tests/
├── __init__.py
├── conftest.py             # Pytest fixtures
├── unit/
└── integration/

alembic/
├── versions/
├── env.py
└── alembic.ini
```

## Acceptance Criteria

- [ ] FastAPI service starts and responds to `GET /healthz`
- [ ] `GET /readyz` returns 503 when Redis is unavailable
- [ ] All routes under `/v1/` prefix
- [ ] Request ID generated and logged
- [ ] Structured JSON logs to stdout
- [ ] Alembic migrations run successfully
- [ ] Redis client connects and can ping

## Dependencies

None - this is the foundation epic.

## Deliverables

- [ ] Service runs locally with `uvicorn src.main:app`
- [ ] Migrations run with `alembic upgrade head`
- [ ] Readiness checks pass for DB + Redis
