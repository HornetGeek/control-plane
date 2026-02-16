# User Stories — EPIC 0: Setup & Engineering Baseline

**Epic**: [epic.md](./epic.md)
**User Persona**: Developer
**Total Stories**: 5
**Total Points**: 12

---

## US-0.1: Specs Structure

**As a** developer,
**I want** a well-organized specification file structure,
**So that** I can easily navigate and maintain project documentation.

### Acceptance Criteria
- [ ] `specs/` directory exists with `master.md`
- [ ] `specs/epics/` directory with subfolder per epic
- [ ] Each epic folder contains `epic.md`, `user-stories.md`
- [ ] Constitution linked from `.specify/memory/constitution.md`

**Priority**: P0
**Points**: 1

---

## US-0.2: FastAPI Application Factory

**As a** developer,
**I want** a FastAPI application using the factory pattern with versioned routing,
**So that** I can easily extend the API and maintain backward compatibility.

### Acceptance Criteria
- [ ] `src/main.py` implements app factory pattern
- [ ] All routes prefixed with `/v1/`
- [ ] CORS middleware configured
- [ ] Error handling middleware catches and formats exceptions

### Files to Create
- `src/main.py`
- `src/api/__init__.py`
- `src/api/v1/__init__.py`
- `src/api/v1/router.py`
- `src/api/deps.py`

**Priority**: P0
**Points**: 3

---

## US-0.3: Observability Baseline

**As a** developer,
**I want** health check endpoints and structured logging,
**So that** I can monitor service health and debug issues in production.

### Acceptance Criteria
- [ ] `GET /healthz` returns 200 with `{"status": "healthy"}`
- [ ] `GET /readyz` checks database and Redis connectivity
- [ ] `GET /readyz` returns 503 with failure details if dependencies unavailable
- [ ] Request ID (`X-Request-ID`) generated and logged for every request
- [ ] Logs output as structured JSON to stdout

### Files to Create
- `src/core/__init__.py`
- `src/core/logging.py`
- `src/core/middleware.py`
- `src/api/v1/health.py`

**Priority**: P0
**Points**: 3

---

## US-0.4: PostgreSQL + Alembic Bootstrap

**As a** developer,
**I want** a configured PostgreSQL connection with Alembic migrations,
**So that** I can manage database schema changes reliably.

### Acceptance Criteria
- [ ] SQLAlchemy 2.0 async engine configured in `src/db/session.py`
- [ ] Alembic initialized with async support
- [ ] `alembic upgrade head` runs without errors
- [ ] Database connection pooling configured

### Files to Create
- `src/db/__init__.py`
- `src/db/base.py`
- `src/db/session.py`
- `alembic/env.py`
- `alembic.ini`
- `alembic/versions/` directory

**Priority**: P0
**Points**: 3

---

## US-0.5: Redis Bootstrap

**As a** developer,
**I want** a configured Redis client,
**So that** I can cache authorization decisions for performance.

### Acceptance Criteria
- [ ] Redis client initialized in `src/cache/redis.py`
- [ ] Redis health check integrated into `/readyz` endpoint
- [ ] Service logs warning if Redis is unavailable but doesn't crash

### Files to Create
- `src/cache/__init__.py`
- `src/cache/redis.py`

**Priority**: P0
**Points**: 2

---

## Story Dependencies

```
US-0.1 (Specs)
     │
     ▼
US-0.2 (FastAPI)
     │
     ├──► US-0.3 (Observability) ──┐
     │                             │
     ├──► US-0.4 (Postgres) ───────┼──► Ready for EPIC 1
     │                             │
     └──► US-0.5 (Redis) ──────────┘
```
