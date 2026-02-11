# Implementation Plan: OIDC Authentication

**Branch**: `002-oidc-auth` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-oidc-auth/spec.md`

## Summary

Implement OpenID Connect authentication with Zitadel as the identity provider. The system will redirect users to Zitadel for authentication, exchange authorization codes for tokens, validate tokens via JWKS, and automatically provision users on first login. Organization context is extracted from a custom `org_id` claim and enforced across all authenticated requests.

**Technical Approach**: Use FastAPI with async/await, python-jose for JWT validation, httpx for OIDC token exchange, and SQLAlchemy for user persistence. JWKS caching reduces external calls.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (async), Pydantic v2, python-jose[cryptography], httpx, SQLAlchemy 2.0 (async)
**Storage**: PostgreSQL with asyncpg driver
**Testing**: pytest with async support, pytest-asyncio
**Target Platform**: Linux server (containerized)
**Project Type**: web (API backend)
**Performance Goals**: 1000 concurrent authentication requests without degradation; <500ms token validation (p95) with cached JWKS
**Constraints**: 10-second max for full authentication flow (login to token receipt)
**Scale/Scope**: Supports multiple organizations sharing one IdP; JWKS cached for 5 minutes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. API-First Architecture | ✅ PASS | All functionality exposed via REST API; no web UI |
| II. Strict Tenancy Boundaries | ✅ PASS | org_id claim enforced; cross-org access blocked |
| III. Subscription-Based Access Control | ✅ PASS | N/A for auth feature (subscriptions checked separately) |
| IV. OIDC-First Authentication | ✅ PASS | Uses Zitadel with authorization code flow; JWKS validation |
| V. Coarse-Grained Authorization | ✅ PASS | N/A for auth feature (roles enforced separately) |
| VI. Idempotent Operations | ✅ PASS | User provisioning is idempotent (get-or-create by idp_sub) |
| VII. No External Billing Integration | ✅ PASS | N/A for auth feature |
| VIII. Audit Stubs Only | ✅ PASS | N/A for auth feature (audit added separately) |

**Architecture Standards**:
- ✅ Multi-Service Platform Context: Upstream to Zitadel IdP
- ✅ Data Flow: User → OIDC → Token → API calls with validation

**Technology Standards**:
- ✅ Language/Version: Python 3.11+ with FastAPI (async)
- ✅ Data Layer: PostgreSQL with SQLAlchemy 2.0 async
- ✅ Testing: pytest with async support
- ✅ API Documentation: OpenAPI 3.0 from FastAPI
- ✅ Configuration: Environment variables only

**API Standards**:
- ✅ Versioning: `/v1/` prefix for endpoints
- ✅ Error Format: Structured error responses
- ✅ Pagination: N/A for auth endpoints (single-user operations)

**Security Standards**:
- ✅ Authentication: Bearer token validation via JWKS
- ✅ Authorization Flow: Token validation → org extraction → boundary enforcement
- ✅ Correlation IDs: X-Request-ID header support

**Gate Result**: ✅ ALL PASSED - No violations to justify

## Project Structure

### Documentation (this feature)

```text
specs/002-oidc-auth/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research and decisions
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/           # Phase 1: API contracts (OpenAPI schemas)
│   ├── auth.yaml        # Authentication endpoint contract
│   └── user.yaml        # User info endpoint contract
└── tasks.md             # Phase 2: Implementation tasks (separate command)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── __init__.py
│   ├── dependencies.py      # FastAPI dependencies (get_current_user)
│   └── v1/
│       ├── __init__.py
│       └── auth.py          # /auth/login, /auth/callback, /auth/me endpoints
├── config.py                # Environment-based settings (OIDC config)
├── db/
│   ├── __init__.py
│   └── session.py           # Async database session management
├── models/
│   ├── __init__.py
│   ├── base.py              # Base model with timestamps
│   ├── user.py              # User model (idp_sub, organization_id, email, name, status)
│   └── organization.py      # Organization model (referenced by User)
├── schemas/
│   ├── __init__.py
│   ├── common.py            # Common response types
│   └── auth.py              # AuthResponse, UserResponse, TokenResponse
├── security/
│   ├── __init__.py
│   ├── oidc.py              # OIDCService (token validation, JWKS caching)
│   └── authorization.py     # Authorization helpers (role checking)
└── services/
    ├── __init__.py
    └── auth.py              # exchange_code_for_token, get_or_create_user

tests/
├── conftest.py              # pytest fixtures (test client, test database)
├── unit/                    # Unit tests for individual functions
│   └── test_oidc_validation.py
├── integration/             # Integration tests for full flows
│   └── test_auth_flow.py
└── contract/                # Contract tests verifying API behavior
    └── test_v1_auth.py
```

**Structure Decision**: Single backend API project following the existing Control Plane MVP structure. The `src/` directory contains all application code with clear separation of concerns: models (data), schemas (API contracts), services (business logic), security (auth/authorization), and api (endpoints). All database operations use async SQLAlchemy.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. This section is not applicable.
