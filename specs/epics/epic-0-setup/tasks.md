# Tasks — EPIC 0: Setup & Engineering Baseline

**Epic**: [epic.md](./epic.md)
**User Stories**: [user-stories.md](./user-stories.md)
**Total Tasks**: 25
**Estimated Time**: 2-3 days

---

## Format: `[ID] [P?] [US] Description`

- **[P]**: Parallelizable (different files, no dependencies)
- **[US]**: User Story reference

---

## Phase 1: Project Structure

- [ ] T001 Create project directories: `src/`, `tests/`, `alembic/`
- [ ] T002 [P] Create `pyproject.toml` with dependencies (FastAPI, SQLAlchemy, Pydantic, Redis, python-jose, httpx, pytest)
- [ ] T003 [P] Create `.env.example` with DATABASE_URL, REDIS_URL, KEYCLOAK_*, AUTHZ_CACHE_TTL
- [ ] T004 [P] Create `src/__init__.py`
- [ ] T005 [P] Create `.gitignore` for Python project

---

## Phase 2: Configuration (US-0.1)

- [ ] T006 Create `src/config.py` with Pydantic Settings class
- [ ] T007 Add environment variable validation in config

---

## Phase 3: FastAPI Factory (US-0.2)

- [ ] T008 [P] Create `src/api/__init__.py`
- [ ] T009 [P] Create `src/api/v1/__init__.py`
- [ ] T010 Create `src/api/v1/router.py` with empty v1 router
- [ ] T011 Create `src/main.py` with app factory pattern
- [ ] T012 Add CORS middleware in `src/main.py`
- [ ] T013 [P] Create `src/api/deps.py` for common dependencies
- [ ] T014 Create `src/core/__init__.py`

---

## Phase 4: Middleware (US-0.2)

- [ ] T015 Create `src/core/middleware.py` with error handling middleware
- [ ] T016 Add request ID middleware in `src/core/middleware.py`
- [ ] T017 Register middleware in `src/main.py`

---

## Phase 5: Observability (US-0.3)

- [ ] T018 [P] Create `src/core/logging.py` with structured JSON logging
- [ ] T019 Create `src/api/v1/health.py` with `/healthz` endpoint
- [ ] T020 Add `/readyz` endpoint in `src/api/v1/health.py`
- [ ] T021 Register health router in `src/api/v1/router.py`

---

## Phase 6: Database (US-0.4)

- [ ] T022 [P] Create `src/db/__init__.py`
- [ ] T023 [P] Create `src/db/base.py` with SQLAlchemy declarative base
- [ ] T024 Create `src/db/session.py` with async session factory
- [ ] T025 Initialize Alembic: `alembic init alembic`
- [ ] T026 Configure `alembic/env.py` for async SQLAlchemy
- [ ] T027 Create `alembic.ini` with env var database URL
- [ ] T028 Create initial empty migration

---

## Phase 7: Redis (US-0.5)

- [ ] T029 [P] Create `src/cache/__init__.py`
- [ ] T030 Create `src/cache/redis.py` with async Redis client
- [ ] T031 Add Redis check to `/readyz` in `src/api/v1/health.py`
- [ ] T032 Add Redis URL to `src/config.py`

---

## Phase 8: Tests & Validation

- [ ] T033 [P] Create `tests/conftest.py` with pytest async fixtures
- [ ] T034 [P] Create `tests/unit/test_main.py`
- [ ] T035 [P] Create `tests/unit/api/test_health.py`
- [ ] T036 Run `uvicorn src.main:app` and verify `/healthz` returns 200
- [ ] T037 Run `alembic upgrade head` and verify success

---

## Dependencies

```
T001 ──► T002-T005 (parallel)
          │
          ▼
       T006-T007
          │
          ▼
    T008-T014 (parallel) ──► T010, T011
              │
              ▼
          T015-T017
              │
              ▼
    T018-T021 ──► T019, T020
              │
              ▼
    T022-T028 ──► T024-T028
              │
              ▼
    T029-T032 ──► T031
              │
              ▼
          T033-T037
```

---

## Acceptance Checklist

- [ ] Service starts with `uvicorn src.main:app`
- [ ] `GET /healthz` returns `{"status": "healthy"}`
- [ ] `GET /readyz` returns 503 when Redis unavailable
- [ ] All routes under `/v1/` prefix
- [ ] Request ID in logs
- [ ] JSON structured logs
- [ ] `alembic upgrade head` succeeds
- [ ] Redis ping succeeds
