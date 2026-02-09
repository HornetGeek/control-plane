---

description: "Task list for Control Plane MVP implementation"
---

# Tasks: Control Plane MVP

**Input**: Design documents from `/docs/` and `/specs/001-control-plane-mvp/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Integration tests are included for each user story to ensure independent validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- This is a web application (REST API microservice)
- Source code in `src/` at repository root
- Tests in `tests/` at repository root
- Migrations in `alembic/versions/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md
- [ ] T002 Initialize Python project with pyproject.toml, dependencies (FastAPI, SQLAlchemy, pytest, etc.)
- [ ] T003 [P] Configure pre-commit hooks (black, ruff, mypy)
- [ ] T004 [P] Setup pytest configuration in pyproject.toml
- [ ] T005 [P] Create .env.example with all required environment variables
- [ ] T006 Create base FastAPI application in src/main.py with /health and /ready endpoints

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Models (Foundation for all stories)

- [ ] T007 Setup async SQLAlchemy engine and session factory in src/db/session.py
- [ ] T008 Create base declarative model in src/models/base.py (UUID id, timestamps)
- [ ] T009 [P] Create Organization model in src/models/organization.py
- [ ] T010 [P] Create Tenant model in src/models/tenant.py
- [ ] T011 [P] Create User model in src/models/user.py
- [ ] T012 [P] Create Membership model in src/models/membership.py
- [ ] T013 [P] Create Application model in src/models/application.py
- [ ] T014 [P] Create Subscription model in src/models/subscription.py
- [ ] T015 Configure Alembic for migrations in alembic/env.py

### Security Infrastructure (Foundation for all protected endpoints)

- [ ] T016 Create OIDC token validation in src/security/oidc.py (JWKS fetch, signature verification)
- [ ] T017 Create authorization helpers in src/security/authorization.py (role checking, org/tenant access)
- [ ] T018 Create FastAPI auth dependency in src/api/dependencies.py (token validation, user attachment)
- [ ] T019 Create audit stubs in src/security/audit.py (internal interfaces, minimal logging)

### API Infrastructure (Foundation for all endpoints)

- [ ] T020 Create error response schemas in src/schemas/common.py (standard error format)
- [ ] T021 Create correlation ID middleware in src/api/middleware.py (X-Request-ID handling)
- [ ] T022 Create exception handlers in src/main.py (transform exceptions to error responses)
- [ ] T023 Create pagination utilities in src/schemas/common.py (limit/offset params, response wrapper)

### Configuration

- [ ] T024 Create configuration class in src/config.py using pydantic-settings (all env vars)
- [ ] T025 Create Alembic initial migration generating all tables

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Authentication (Priority: P1) 🎯 MVP

**Goal**: Users can authenticate via OIDC and be associated with their organization

**Independent Test**: Run OIDC flow end-to-end, verify user is created/updated with correct org association

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T026 [P] [US1] Integration test for OIDC login redirect in tests/integration/test_auth_flow.py
- [ ] T027 [P] [US1] Integration test for OIDC callback with new user in tests/integration/test_auth_flow.py
- [ ] T028 [P] [US1] Integration test for OIDC callback with existing user in tests/integration/test_auth_flow.py
- [ ] T029 [P] [US1] Integration test for missing org_id claim rejection in tests/integration/test_auth_flow.py
- [ ] T030 [P] [US1] Integration test for /auth/me endpoint in tests/integration/test_auth_flow.py
- [ ] T031 [P] [US1] Contract test for /v1/auth endpoints in tests/contract/test_v1_auth.yaml

### Implementation for User Story 1

- [ ] T032 [P] [US1] Create auth schemas in src/schemas/auth.py (TokenResponse, UserResponse, MeResponse)
- [ ] T033 [P] [US1] Create OIDC service in src/services/auth.py (token exchange, user lookup/creation)
- [ ] T034 [US1] Implement /v1/auth/login endpoint in src/api/v1/auth.py (redirect to Zitadel)
- [ ] T035 [US1] Implement /v1/auth/callback endpoint in src/api/v1/auth.py (handle callback, create/update user)
- [ ] T036 [US1] Implement /v1/auth/me endpoint in src/api/v1/auth.py (return current user info)
- [ ] T037 [US1] Add test seed data in tests/conftest.py (test organization for OIDC users)

**Checkpoint**: At this point, User Story 1 should be fully functional - users can authenticate and are associated with organizations

---

## Phase 4: User Story 2 - Tenant Management (Priority: P1) 🎯 MVP

**Goal**: Organization admins can create and manage tenants

**Independent Test**: Create tenant via API, verify it's associated with correct organization

### Tests for User Story 2

- [ ] T038 [P] [US2] Integration test for tenant creation by org_admin in tests/integration/test_tenants.py
- [ ] T039 [P] [US2] Integration test for tenant creation rejection by non-admin in tests/integration/test_tenants.py
- [ ] T040 [P] [US2] Integration test for listing tenants (org admin sees all) in tests/integration/test_tenants.py
- [ ] T041 [P] [US2] Integration test for listing tenants (member sees only theirs) in tests/integration/test_tenants.py
- [ ] T042 [P] [US2] Integration test for getting tenant by ID in tests/integration/test_tenants.py
- [ ] T043 [P] [US2] Integration test for cross-org tenant access rejection in tests/integration/test_tenants.py
- [ ] T044 [P] [US2] Contract test for /v1/tenants endpoints in tests/contract/test_v1_tenants.yaml

### Implementation for User Story 2

- [ ] T045 [P] [US2] Create tenant schemas in src/schemas/tenant.py (TenantCreate, TenantResponse, TenantListResponse)
- [ ] T046 [US2] Create tenant service in src/services/tenant.py (CRUD operations with org filtering)
- [ ] T047 [US2] Implement POST /v1/tenants endpoint in src/api/v1/tenants.py (create tenant, enforce org_admin)
- [ ] T048 [US2] Implement GET /v1/tenants endpoint in src/api/v1/tenants.py (list with pagination, org-scoped)
- [ ] T049 [US2] Implement GET /v1/tenants/{id} endpoint in src/api/v1/tenants.py (get single, enforce access)
- [ ] T050 [US2] Add tenant authorization helpers in src/security/authorization.py (org_admin check, membership check)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can authenticate and org admins can manage tenants

---

## Phase 5: User Story 3 - Membership Management (Priority: P2)

**Goal**: Admins can add/remove users from tenants with roles

**Independent Test**: Add user to tenant with role, verify membership is created and user can access tenant resources

### Tests for User Story 3

- [ ] T051 [P] [US3] Integration test for adding member by org_admin in tests/integration/test_memberships.py
- [ ] T052 [P] [US3] Integration test for adding member by tenant_admin in tests/integration/test_memberships.py
- [ ] T053 [P] [US3] Integration test for duplicate member rejection in tests/integration/test_memberships.py
- [ ] T054 [P] [US3] Integration test for listing tenant members in tests/integration/test_memberships.py
- [ ] T055 [P] [US3] Integration test for removing tenant member in tests/integration/test_memberships.py
- [ ] T056 [P] [US3] Integration test for member modification rejection by tenant_member in tests/integration/test_memberships.py
- [ ] T057 [P] [US3] Contract test for /v1/memberships endpoints in tests/contract/test_v1_memberships.yaml

### Implementation for User Story 3

- [ ] T058 [P] [US3] Create membership schemas in src/schemas/membership.py (MembershipCreate, MembershipResponse, MemberListResponse)
- [ ] T059 [US3] Create membership service in src/services/membership.py (add, remove, list with idempotency)
- [ ] T060 [US3] Implement POST /v1/tenants/{tenant_id}/members in src/api/v1/memberships.py
- [ ] T061 [US3] Implement GET /v1/tenants/{tenant_id}/members in src/api/v1/memberships.py
- [ ] T062 [US3] Implement DELETE /v1/tenants/{tenant_id}/members/{user_id} in src/api/v1/memberships.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should work - users can authenticate, tenants can be managed, and users can be assigned to tenants

---

## Phase 6: User Story 4 - Subscription Management (Priority: P2)

**Goal**: Admins can subscribe tenants to applications

**Independent Test**: Subscribe tenant to application, verify subscription is created and idempotent

### Tests for User Story 4

- [ ] T063 [P] [US4] Integration test for subscribing tenant to application in tests/integration/test_subscriptions.py
- [ ] T064 [P] [US4] Integration test for idempotent subscription creation in tests/integration/test_subscriptions.py
- [ ] T065 [P] [US4] Integration test for listing tenant subscriptions in tests/integration/test_subscriptions.py
- [ ] T066 [P] [US4] Integration test for updating subscription status in tests/integration/test_subscriptions.py
- [ ] T067 [P] [US4] Integration test for subscription modification rejection by tenant_member in tests/integration/test_subscriptions.py
- [ ] T068 [P] [US4] Contract test for /v1/subscriptions endpoints in tests/contract/test_v1_subscriptions.yaml

### Implementation for User Story 4

- [ ] T069 [P] [US4] Create subscription schemas in src/schemas/subscription.py (SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate, SubscriptionListResponse)
- [ ] T070 [US4] Create subscription service in src/services/subscription.py (create idempotent, list, update status)
- [ ] T071 [US4] Implement POST /v1/tenants/{tenant_id}/subscriptions in src/api/v1/subscriptions.py
- [ ] T072 [US4] Implement GET /v1/tenants/{tenant_id}/subscriptions in src/api/v1/subscriptions.py
- [ ] T073 [US4] Implement PATCH /v1/tenants/{tenant_id}/subscriptions/{sub_id} in src/api/v1/subscriptions.py
- [ ] T074 [US4] Create application catalog service in src/services/application.py (read-only lookup)
- [ ] T075 [US4] Implement GET /v1/applications endpoint in src/api/v1/applications.py (read-only catalog)

**Checkpoint**: At this point, User Stories 1-4 should work - full subscription management is functional

---

## Phase 7: User Story 5 - Application Launch (Priority: P3)

**Goal**: Tenant members can launch subscribed applications

**Independent Test**: Tenant member requests launch for subscribed app, receives valid redirect URL

### Tests for User Story 5

- [ ] T076 [P] [US5] Integration test for launching subscribed application in tests/integration/test_launch.py
- [ ] T077 [P] [US5] Integration test for launch rejection for unsubscribed application in tests/integration/test_launch.py
- [ ] T078 [P] [US5] Integration test for launch rejection for non-member in tests/integration/test_launch.py
- [ ] T079 [P] [US5] Integration test for launch rejection for inactive application in tests/integration/test_launch.py
- [ ] T080 [P] [US5] Integration test for launch by org_admin (bypasses membership) in tests/integration/test_launch.py
- [ ] T081 [P] [US5] Contract test for /v1/launch endpoint in tests/contract/test_v1_launch.yaml

### Implementation for User Story 5

- [ ] T082 [P] [US5] Create launch schemas in src/schemas/common.py (LaunchRequest, LaunchResponse)
- [ ] T083 [US5] Create launch service in src/services/launch.py (validate membership, subscription, app; generate redirect URL)
- [ ] T084 [US5] Implement POST /v1/launch endpoint in src/api/v1/launch.py
- [ ] T086 [US5] Create application seed script in src/db/seed_applications.py (PACS, ERP)

**Checkpoint**: All user stories should now be independently functional - complete Control Plane MVP

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation

- [ ] T087 [P] Create README.md with project overview, setup instructions, and API documentation link
- [ ] T088 [P] Create docs/quickstart.md with detailed local development setup
- [ ] T089 [P] Create docs/deployment.md with container and deployment guidance

### Data Seeding

- [ ] T090 Create organization seed script in src/db/seed_organizations.py (initial test orgs)
- [ ] T091 Create user seed script in src/db/seed_users.py (initial test users with OIDC subs)

### Testing & Quality

- [ ] T092 [P] Add unit tests for OIDC validation in tests/unit/test_security.py
- [ ] T093 [P] Add unit tests for authorization helpers in tests/unit/test_security.py
- [ ] T094 [P] Add unit tests for all models in tests/unit/test_models.py
- [ ] T095 Run full test suite and ensure 90%+ coverage
- [ ] T096 Verify OpenAPI schema generation is complete and accurate

### Security Hardening

- [ ] T097 Verify all authorization failures are logged with correlation ID
- [ ] T098 Verify error messages don't leak internal details
- [ ] T099 Verify SQL injection protection via parameterized queries (SQLAlchemy default)

### Performance

- [ ] T100 Load test /v1/auth/login endpoint (target: 1000 concurrent requests)
- [ ] T101 Verify database indexes are created via Alembic migration
- [ ] T102 Verify JWKS caching is working (check OIDC service logs)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4 → US5)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (Authentication)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Tenant Management)**: Can start after Foundational (Phase 2) - Uses User model from US1 but works independently
- **User Story 3 (Membership Management)**: Can start after Foundational (Phase 2) - Integrates US1 (Users) and US2 (Tenants)
- **User Story 4 (Subscription Management)**: Can start after Foundational (Phase 2) - Integrates US2 (Tenants) + Applications
- **User Story 5 (Launch)**: Can start after Foundational (Phase 2) - Integrates US3 (Memberships) + US4 (Subscriptions)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD approach)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T006) can run in parallel
- All models in Foundational phase (T009-T014) can run in parallel
- All tests for a user story marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: Foundational Models

```bash
# Launch all model creation tasks together:
Task: "Create Organization model in src/models/organization.py"
Task: "Create Tenant model in src/models/tenant.py"
Task: "Create User model in src/models/user.py"
Task: "Create Membership model in src/models/membership.py"
Task: "Create Application model in src/models/application.py"
Task: "Create Subscription model in src/models/subscription.py"
```

---

## Parallel Example: User Story 2 Tests

```bash
# Launch all tests for User Story 2 together:
Task: "Integration test for tenant creation by org_admin in tests/integration/test_tenants.py"
Task: "Integration test for tenant creation rejection by non-admin in tests/integration/test_tenants.py"
Task: "Integration test for listing tenants (org admin sees all) in tests/integration/test_tenants.py"
Task: "Integration test for listing tenants (member sees only theirs) in tests/integration/test_tenants.py"
Task: "Integration test for getting tenant by ID in tests/integration/test_tenants.py"
Task: "Integration test for cross-org tenant access rejection in tests/integration/test_tenants.py"
Task: "Contract test for /v1/tenants endpoints in tests/contract/test_v1_tenants.yaml"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Authentication)
4. Complete Phase 4: User Story 2 (Tenant Management)
5. **STOP and VALIDATE**: Test both stories independently
6. Deploy/demo if ready - users can authenticate and org admins can create tenants

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP Milestone 1 (Auth works)
3. Add User Story 2 → Test independently → MVP Milestone 2 (Tenants work)
4. Add User Story 3 → Test independently → MVP Milestone 3 (Memberships work)
5. Add User Story 4 → Test independently → MVP Milestone 4 (Subscriptions work)
6. Add User Story 5 → Test independently → Complete MVP (Launch works)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Authentication)
   - Developer B: User Story 2 (Tenant Management)
   - Developer C: User Story 3 (Memberships) - waits for T010 (Tenant model)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
