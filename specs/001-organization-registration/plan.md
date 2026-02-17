# Implementation Plan: Organization Registration

**Branch**: `001-organization-registration` | **Date**: 2026-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-organization-registration/spec.md`

## Summary

Self-service organization registration for new customers following an invite-only OIDC model. The feature collects organization details and admin information, creates an organization in `pending_invite` status with a unique slug, assigns a 14-day trial plan (clock starts at activation in US-CP-002), initiates an IdP invite for the admin (adapter-based; stubbed by default), and handles failures with a resend-invite flow.

## Technical Context

**Language/Version**: Python 3.11+ (per constitution)
**Primary Dependencies**: FastAPI (async), Pydantic v2, SQLAlchemy 2.0 (async), python-jose[cryptography], httpx, Redis
**Storage**: PostgreSQL (existing)
**Testing**: pytest with async support (existing pattern in tests/)
**Target Platform**: Linux server (Docker containerized)
**Project Type**: Single web service (existing Control Plane API)
**Performance Goals**: 100 concurrent registrations, <2 min form submission, <5 sec IdP invite initiation
**Constraints**: Public endpoint (no auth for registration), rate limiting required, idempotent operations; only trust proxy headers (e.g., `X-Forwarded-For`) from configured trusted proxies
**Scale/Scope**: Self-service registration, ~1000 registrations/day expected

## Key Decisions

- **IdP integration**: Keep an IdP adapter interface; use a stub adapter by default for unit/integration tests; support a real IdP adapter (e.g., Keycloak) behind configuration for manual/E2E validation.
- **Trial semantics**: Assign Trial at organization creation; set `trial_starts_at`/`trial_ends_at` and enable entitlements only when the organization becomes `active` (US-CP-002).
- **CP↔Core sync (MVP)**: Persist a durable sync intent (outbox event or `core_sync_status=pending`) so it can be replayed later; do not call Core in US-CP-001 MVP.
- **Cleanup**: Run a scheduled cleanup job to redact PII and mark registrations `expired` after 7 days (configurable), while preserving audit evidence.
- **Rate limiting**: Use client IP as primary key; derive IP from `request.client.host` unless behind trusted proxy; return `429` with `Retry-After`; enforce a backoff ladder (default: 1min, 5min, 15min, 1hr; configurable).
- **Error contract**: Use `422` for validation (including terms not accepted), `409` for duplicate email, `429` for rate limits; return a consistent `ErrorResponse` and include a request/correlation ID on every response.
- **Audit events**: Emit business events from the registration service (not middleware) and attach correlation IDs; apply privacy-safe handling (mask/minimize IP and avoid storing full emails in events).
- **Tests**: Keep IdP stubbed in integration tests; add an optional IdP smoke test profile (runs only when real IdP is available).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Mission & Scope | ✅ PASS | Organization registration is within CP scope (registry management) |
| II. 3-Plane Model | ✅ PASS | CP owns organizations, Core owns users/memberships |
| III. Trust & Security | ✅ PASS | Registration is PUBLIC endpoint (no auth); IdP handles user creation |
| IV. Roles & Access | ✅ PASS | Not applicable (registration is pre-auth) |
| V. Caching Strategy | ✅ PASS | Not applicable (no authorization decisions for public endpoint) |
| VI. Data Lifecycle | ✅ PASS | Will implement soft delete + status per constitution |
| VII. CP↔Core Sync | ⚠️ STUB | MVP: Persist durable sync intent (outbox/status), no actual Core calls |
| VIII. App Launch | ✅ PASS | Not applicable |
| IX. API Governance | ✅ PASS | Will use `/v1/public/registration` namespace; error contract uses `409`/`422`/`429` and includes correlation IDs |
| X. Trial Period | ✅ PASS | 14-day trial assigned at org creation; trial clock starts at activation (US-CP-002) |

**Gate Status**: ✅ PASSED - All principles satisfied or stubbed for MVP

## Project Structure

### Documentation (this feature)

```text
specs/001-organization-registration/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
│   └── openapi.yaml
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── deps.py              # Add rate limiting dependency
│   └── v1/
│       ├── router.py        # Register registration router
│       └── registration.py  # NEW: Public registration endpoints
├── models/
│   ├── organization.py      # EXTEND: Add slug, status, trial fields
│   └── registration.py      # NEW: Registration tracking entity
├── schemas/
│   └── registration.py      # NEW: Request/response schemas
├── services/
│   └── registration_service.py  # NEW: Registration business logic
├── core/
│   └── rate_limiter.py      # NEW: Rate limiting utility
└── clients/
    └── idp_adapter.py       # NEW: IdP invite interface (stub for MVP)

tests/
├── unit/
│   ├── services/
│   │   └── test_registration_service.py  # NEW
│   └── api/
│       └── test_registration.py          # NEW
└── integration/
    └── test_registration_flow.py         # NEW
```

**Structure Decision**: Extends existing single-service structure. Public endpoint under `/v1/public/` namespace per API governance.

## Complexity Tracking

> No constitution violations requiring justification.
