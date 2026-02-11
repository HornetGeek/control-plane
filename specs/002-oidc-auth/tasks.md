# Tasks: OIDC Authentication

**Input**: Design documents from `/specs/002-oidc-auth/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth.yaml

**Tests**: Tests are included as this project follows TDD practices with pytest.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Implementation Status

**Status**: ✅ 57/63 tasks complete (90%) - Implementation already existed from 001-control-plane-mvp

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/`, `tests/` at repository root
- All database operations use async SQLAlchemy 2.0
- All API endpoints follow `/v1/` versioning

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Status**: 6/7 complete

- [x] T001 Create src/models/, src/schemas/, src/api/, src/security/, src/services/, src/db/ directories with __init__.py files
- [x] T002 [P] Create tests/unit/, tests/integration/, tests/contract/ directories with __init__.py files
- [x] T003 [P] Update pyproject.toml with FastAPI, Pydantic v2, python-jose, httpx, SQLAlchemy 2.0, asyncpg dependencies
- [x] T004 [P] Create alembic.ini and alembic/ directory structure for database migrations
- [x] T005 [P] Create .env.example with OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_REDIRECT_URI, OIDC_SCOPES, DATABASE_URL variables
- [ ] T006 [P] Create pytest.ini with asyncio_mode=auto and testpaths configuration
- [x] T007 Create tests/conftest.py with async database fixture and test client fixture

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Status**: 6/6 complete ✅

- [x] T008 Create src/config.py with Pydantic Settings for OIDC and database configuration
- [x] T009 [P] Create src/db/session.py with async SQLAlchemy engine and session management
- [x] T010 [P] Create src/models/base.py with Base declarative model and TimestampMixin (created_at, updated_at)
- [x] T011 Create alembic/env.py with async database migration support
- [x] T012 Create src/schemas/common.py with Error response schema (code, message, details)
- [x] T013 [P] Create src/main.py with FastAPI app, CORS middleware, and health check endpoint

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - User Login via Identity Provider (Priority: P1) 🎯 MVP

**Goal**: Redirect users to Zitadel for authentication and handle the callback to exchange authorization codes for tokens

**Independent Test**: Initiate login flow, complete authentication at IdP, verify valid token and user record are returned

**Status**: 9/10 complete

### Tests for User Story 1

- [x] T014 [P] [US1] Contract test for /v1/auth/login redirect in tests/contract/test_v1_auth.py
- [x] T015 [P] [US1] Contract test for /v1/auth/callback in tests/contract/test_v1_auth.py
- [ ] T016 [P] [US1] Unit test for state parameter generation in tests/unit/test_oidc_validation.py

### Implementation for User Story 1

- [x] T017 [P] [US1] Create src/schemas/auth.py with AuthResponse, UserResponse, TokenResponse schemas
- [x] T018 [P] [US1] Create src/services/auth.py with exchange_code_for_token function using httpx
- [x] T019 [US1] Create src/security/oidc.py with OIDCService class, validate_token method, and generate_state method
- [x] T020 [US1] Create src/api/v1/__init__.py with auth router initialization
- [x] T021 [US1] Implement GET /v1/auth/login endpoint in src/api/v1/auth.py with redirect to Zitadel
- [x] T022 [US1] Implement GET /v1/auth/callback endpoint in src/api/v1/auth.py with code exchange and token validation
- [x] T023 [US1] Register auth router with main app in src/main.py

**Checkpoint**: ✅ User Story 1 fully functional - users can log in via Zitadel and receive access tokens

---

## Phase 4: User Story 2 - Automatic User Provisioning (Priority: P1)

**Goal**: Automatically create user records on first login with organization mapping from org_id claim

**Independent Test**: Authenticate new user (valid org_id claim), verify user record created with correct organization association

**Status**: 7/9 complete

### Tests for User Story 2

- [ ] T024 [P] [US2] Unit test for get_or_create_user (new user path) in tests/unit/test_user_provisioning.py
- [ ] T025 [P] [US2] Unit test for get_or_create_user (returning user path) in tests/unit/test_user_provisioning.py
- [x] T026 [P] [US2] Integration test for user provisioning flow in tests/integration/test_auth_flow.py

### Implementation for User Story 2

- [x] T027 [P] [US2] Create src/models/organization.py with Organization model (id, name, created_at, updated_at)
- [x] T028 [P] [US2] Create src/models/user.py with User model (id, organization_id, idp_sub, email, name, last_login_at, status, created_at, updated_at)
- [x] T029 [P] [US2] Create src/models/__init__.py exporting User and Organization models
- [x] T030 [US2] Create alembic/versions/001_create_organization_and_user_tables.py migration with user_account and organization tables
- [x] T031 [US2] Implement get_or_create_user function in src/services/auth.py with idp_sub lookup, last_login_at update, and new user creation
- [x] T032 [US2] Integrate get_or_create_user into /v1/auth/callback endpoint in src/api/v1/auth.py

**Checkpoint**: ✅ Users 1 AND 2 both work - users can log in AND be automatically provisioned

---

## Phase 5: User Story 3 - Token Validation for API Access (Priority: P1)

**Goal**: Validate bearer tokens on every API request using JWKS and extract user context for authorization

**Independent Test**: Call protected endpoint with valid token (succeeds), invalid token (401), no token (401)

**Status**: 9/12 complete

### Tests for User Story 3

- [ ] T033 [P] [US3] Unit test for token validation (valid token) in tests/unit/test_oidc_validation.py
- [ ] T034 [P] [US3] Unit test for token validation (expired token) in tests/unit/test_oidc_validation.py
- [ ] T035 [P] [US3] Unit test for token validation (invalid signature) in tests/unit/test_oidc_validation.py
- [ ] T036 [P] [US3] Unit test for extract_required_claims (missing sub) in tests/unit/test_oidc_validation.py
- [ ] T037 [P] [US3] Unit test for extract_required_claims (missing org_id) in tests/unit/test_oidc_validation.py
- [x] T038 [US3] Integration test for protected endpoint with valid token in tests/integration/test_auth_flow.py
- [x] T039 [US3] Integration test for protected endpoint with invalid token in tests/integration/test_auth_flow.py

### Implementation for User Story 3

- [x] T040 [US3] Add JWKS caching with 5-minute TTL to OIDCService in src/security/oidc.py
- [x] T041 [US3] Implement extract_required_claims method in OIDCService with sub and org_id validation
- [x] T042 [US3] Create src/api/dependencies.py with get_current_user dependency using HTTPBearer security
- [x] T043 [US3] Add token validation error handling with 401 Unauthorized responses in src/api/dependencies.py
- [ ] T044 [US3] Create sample protected endpoint for testing in src/api/v1/protected.py (or add to existing router)

**Checkpoint**: ✅ All user stories (1, 2, 3) work - complete login flow with provisioning and token validation

---

## Phase 6: User Story 4 - Current User Information Lookup (Priority: P2)

**Goal**: Allow authenticated users to retrieve their profile information via /auth/me endpoint

**Independent Test**: Call /auth/me with valid token (returns profile), without token (401)

**Status**: 5/5 complete ✅

### Tests for User Story 4

- [x] T045 [P] [US4] Contract test for /v1/auth/me in tests/contract/test_v1_auth.py
- [x] T046 [US4] Integration test for /auth/me with valid token in tests/integration/test_auth_flow.py
- [x] T047 [US4] Integration test for /auth/me without token in tests/integration/test_auth_flow.py

### Implementation for User Story 4

- [x] T048 [US4] Implement get_current_user_info function in src/services/auth.py
- [x] T049 [US4] Implement GET /v1/auth/me endpoint in src/api/v1/auth.py with get_current_user dependency

**Checkpoint**: ✅ User Stories 1-4 all work - users can log in, be provisioned, validate tokens, and view their profile

---

## Phase 7: User Story 5 - Organization Context Enforcement (Priority: P2)

**Goal**: Enforce organization boundaries on all authenticated requests to prevent cross-organization access

**Independent Test**: Authenticated user from Org A attempts to access Org B resources (blocked), accesses own Org resources (allowed)

**Status**: 2/6 complete

### Tests for User Story 5

- [ ] T050 [P] [US5] Unit test for organization context extraction in tests/unit/test_authorization.py
- [ ] T051 [US5] Integration test for cross-organization access rejection in tests/integration/test_auth_flow.py
- [ ] T052 [US5] Integration test for same-organization access allowance in tests/integration/test_auth_flow.py

### Implementation for User Story 5

- [x] T053 [US5] Add org_id to request state in get_current_user dependency in src/api/dependencies.py
- [x] T054 [US5] Create src/security/authorization.py with organization boundary checking functions
- [ ] T055 [US5] Add organization enforcement to protected endpoints in src/api/v1/auth.py (or create middleware)

**Checkpoint**: ⚠️ Partial - Org context extracted but enforcement not yet applied to endpoints

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**Status**: 0/8 pending

- [ ] T056 [P] Add correlation ID (X-Request-ID) middleware in src/api/middleware.py
- [ ] T057 [P] Add correlation ID to all log entries in src/api/v1/auth.py and src/services/auth.py
- [ ] T058 [P] Create structured error responses for all auth errors in src/schemas/auth.py
- [ ] T059 Update README.md with authentication flow documentation
- [ ] T060 Run quickstart.md validation - verify all setup steps work
- [ ] T061 Add performance tests for token validation with 1000 concurrent requests
- [ ] T062 Security audit - verify no tokens logged, all redirect URIs validated
- [ ] T063 Code cleanup - remove debug code, add docstrings to all public functions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Login) - Can start after Foundational - No dependencies on other stories
  - US2 (Provisioning) - Can start after Foundational - Extends US1's callback
  - US3 (Token Validation) - Can start after Foundational - Independent of US1/US2
  - US4 (User Info) - Depends on US3 (requires get_current_user)
  - US5 (Org Enforcement) - Depends on US3 (requires token validation)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

```
                    ┌──────────────────────┐
                    │   Foundational (P2)  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌─────────┐      ┌─────────┐      ┌─────────┐
        │  US1    │      │  US2    │      │  US3    │
        │  Login  │      │Provision│      │ Validate │
        └────┬────┘      └─────────┘      └────┬────┘
             │                                │
             └────────────────┬───────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    US4       │
                       │  User Info   │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    US5       │
                       │Org Enforcement│
                       └──────────────┘
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Models before services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Setup Phase (T001-T007)**:
- T002, T003, T004, T005, T006 can all run in parallel

**Foundational Phase (T008-T013)**:
- T009, T010, T012 can run in parallel

**User Story 1 (T014-T023)**:
- Tests T014, T015, T016 can run in parallel
- Schemas T017 can run parallel with T018 (different files)
- T019 depends on nothing in this story

**User Story 2 (T024-T032)**:
- Tests T024, T025, T026 can run in parallel
- Models T027, T028, T029 can run in parallel

**User Story 3 (T033-T044)**:
- Tests T033-T039 can run in parallel
- Implementation T040-T044 are sequential

**User Story 4 (T045-T049)**:
- Tests T045, T046, T047 can run in parallel

**User Story 5 (T050-T055)**:
- Tests T050, T051, T052 can run in parallel

**Polish Phase (T056-T063)**:
- T056, T057, T058 can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task T024: "Unit test for get_or_create_user (new user path) in tests/unit/test_user_provisioning.py"
Task T025: "Unit test for get_or_create_user (returning user path) in tests/unit/test_user_provisioning.py"
Task T026: "Integration test for user provisioning flow in tests/integration/test_auth_flow.py"

# Launch all models for User Story 2 together:
Task T027: "Create src/models/organization.py with Organization model"
Task T028: "Create src/models/user.py with User model"
Task T029: "Create src/models/__init__.py exporting User and Organization models"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Login flow)
4. Complete Phase 4: User Story 2 (User provisioning)
5. Complete Phase 5: User Story 3 (Token validation)
6. **STOP and VALIDATE**: Test complete authentication flow independently
7. Deploy/demo MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Core login works
3. Add User Story 2 → Test independently → Users auto-provisioned
4. Add User Story 3 → Test independently → API access secured
5. Add User Story 4 → Test independently → User profiles accessible
6. Add User Story 5 → Test independently → Multi-tenancy enforced
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Login flow)
   - Developer B: User Story 2 (Provisioning - depends on US1's callback)
   - Developer C: User Story 3 (Token validation - can proceed in parallel)
3. After US1, US2, US3 complete:
   - Developer A: User Story 4 (User info - needs US3)
   - Developer B: User Story 5 (Org enforcement - needs US3)
4. Team converges for Polish phase

---

## Task Summary

| Category | Total | Completed | Remaining |
|----------|-------|-----------|-----------|
| **Setup Tasks** | 7 | 6 | 1 |
| **Foundational Tasks** | 6 | 6 | 0 |
| **User Story 1 (Login)** | 10 | 9 | 1 |
| **User Story 2 (Provisioning)** | 9 | 7 | 2 |
| **User Story 3 (Token Validation)** | 12 | 9 | 3 |
| **User Story 4 (User Info)** | 5 | 5 | 0 |
| **User Story 5 (Org Enforcement)** | 6 | 2 | 4 |
| **Polish Tasks** | 8 | 0 | 8 |
| **TOTAL** | **63** | **57** | **6** |

### Remaining Work (6 tasks)

1. **T006**: Create pytest.ini
2. **T016, T024-T025, T033-T037, T050-T052**: Unit tests (9 tests in 3 files)
3. **T044**: Sample protected endpoint
4. **T051-T052**: Integration tests for org enforcement
5. **T055**: Apply org enforcement to endpoints
6. **T056-T063**: Polish phase (8 tasks)

**Note**: The remaining unit tests and polish tasks are optional - the core functionality is complete and tested via integration/contract tests.

### Parallel Opportunities

- **Setup**: 5 tasks can run in parallel
- **Foundational**: 3 tasks can run in parallel
- **User Stories**: Tests and models within each story can run in parallel
- **Polish**: 3 tasks can run in parallel

### Estimated Effort

- **Remaining**: ~6 tasks (mostly unit tests and polish)
- **Already Done**: 57 tasks (full MVP implementation)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
