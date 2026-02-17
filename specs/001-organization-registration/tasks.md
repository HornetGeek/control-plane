# Tasks: Organization Registration

**Input**: Design documents from `/specs/001-organization-registration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, configuration, and environment setup

- [ ] T001 Verify Python 3.11+ and dependencies (FastAPI, Pydantic v2, SQLAlchemy 2.0 async, Redis) in pyproject.toml
- [ ] T002 [P] Add registration configuration settings in src/config.py (rate limits, trial duration, retention days, personal email domains)
- [ ] T003 [P] Create IdP adapter interface in src/clients/idp_adapter.py with Protocol class and StubIdPAdapter implementation
- [ ] T004 [P] Update .env.example with new registration environment variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create database migration to extend organizations table with slug, status, trial fields in alembic/versions/002_extend_organizations.py
- [ ] T006 [P] Create database migration for registrations table in alembic/versions/003_create_registrations.py
- [ ] T007 [P] Extend Organization model in src/models/organization.py with slug, status, trial_plan, trial_assigned_at, trial_starts_at, trial_ends_at, terms_version, privacy_version, accepted_at, accepted_locale, country_code fields
- [ ] T008 [P] Create Registration model in src/models/registration.py with all fields from data-model.md
- [ ] T009 Create registration schemas (RegistrationRequest, RegistrationResponse, ErrorResponse) in src/schemas/registration.py
- [ ] T010 Create rate limiter utility with Redis sliding window in src/core/rate_limiter.py
- [ ] T011 Add rate limiting dependency in src/api/deps.py
- [ ] T012 Create slug generation utility (lowercase, hyphens, 4-char random suffix) in src/core/slug_utils.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1, 2, 3 - MVP Registration (Priority: P1) 🎯 MVP

**Goal**: Display registration form, complete registration, and assign trial plan

**Independent Test**: POST valid registration data, verify organization created with pending_invite status, trial plan assigned, unique slug generated, IdP invite initiated (stub)

### Implementation for MVP (US1, US2, US3)

- [ ] T013 [US1,US2,US3] Create RegistrationService in src/services/registration_service.py with create_organization, generate_unique_slug, assign_trial_plan, initiate_idp_invite methods
- [ ] T014 [US1,US2,US3] Create public registration router in src/api/v1/registration.py with POST /registration endpoint
- [ ] T015 [US1,US2,US3] Register public registration router in src/api/v1/router.py under /public prefix
- [ ] T016 [US1,US2,US3] Add validation for registration request (email format, country code ISO 3166-1, phone E.164, accept_terms required)
- [ ] T017 [US1,US2,US3] Emit audit events (registration.initiated, registration.submitted, invite.sent) from registration service
- [ ] T018 [US1,US2,US3] Add correlation ID middleware/dependency for request tracking in src/api/deps.py

**Checkpoint**: At this point, basic registration should work: form submission creates org with pending_invite status and trial plan, returns registration_id, shows confirmation message

---

## Phase 4: User Story 4 - Duplicate Email Prevention (Priority: P2)

**Goal**: Prevent registrations with emails already in the system

**Independent Test**: Register with an existing email, verify 409 conflict with error code EMAIL_ALREADY_REGISTERED and sign_in_url in response

### Implementation for US4

- [ ] T019 [US4] Add email uniqueness check in RegistrationService.create_organization in src/services/registration_service.py
- [ ] T020 [US4] Add EMAIL_ALREADY_REGISTERED error handling with sign_in_url details in src/api/v1/registration.py

**Checkpoint**: Duplicate email prevention working independently

---

## Phase 5: User Story 5 - Duplicate Organization Name Handling (Priority: P2)

**Goal**: Allow duplicate organization names with unique slugs

**Independent Test**: Register two organizations with same name, verify both succeed with unique slugs (e.g., acme-corp and acme-corp-7x9k)

### Implementation for US5

- [ ] T021 [US5] Implement slug uniqueness check and suffix generation in src/core/slug_utils.py (query existing slugs, append 4-char suffix if conflict)
- [ ] T022 [US5] Integrate slug generation in RegistrationService in src/services/registration_service.py

**Checkpoint**: Duplicate organization names result in unique slugs

---

## Phase 6: User Story 6 - Terms and Privacy Policy Acceptance (Priority: P2)

**Goal**: Capture legal acceptance metadata

**Independent Test**: Submit registration without accept_terms=true, verify 422 with TERMS_NOT_ACCEPTED error; complete registration with acceptance, verify metadata captured

### Implementation for US6

- [ ] T023 [US6] Add accept_terms validation in registration schema (must be true) in src/schemas/registration.py
- [ ] T024 [US6] Capture terms_version, privacy_version, accepted_at, accepted_locale on organization in src/services/registration_service.py
- [ ] T025 [US6] Add TERMS_NOT_ACCEPTED error response in src/api/v1/registration.py

**Checkpoint**: Legal acceptance metadata captured for all registrations

---

## Phase 7: User Story 7 - Rate Limiting and Abuse Prevention (Priority: P2)

**Goal**: Prevent registration abuse with per-IP rate limiting

**Independent Test**: Exceed 10 registration attempts per IP, verify 429 with RATE_LIMITED error and Retry-After header

### Implementation for US7

- [ ] T026 [US7] Integrate rate limiter dependency in POST /registration endpoint in src/api/v1/registration.py
- [ ] T027 [US7] Add per-IP rate limit check (10/hour) with Redis sliding window in src/core/rate_limiter.py
- [ ] T028 [US7] Add per-email rate limit check (3/hour) as secondary protection in src/core/rate_limiter.py
- [ ] T029 [US7] Emit registration.rate_limited audit event in src/api/v1/registration.py
- [ ] T030 [US7] Add RATE_LIMITED error response with Retry-After header in src/api/v1/registration.py

**Checkpoint**: Rate limiting prevents excessive registration attempts

---

## Phase 8: User Story 8 - IdP Invite Failure Handling (Priority: P2)

**Goal**: Handle IdP invite failures gracefully with resend flow

**Independent Test**: Simulate IdP failure, verify org stays pending_invite with invite_status=failed; call resend-invite endpoint, verify new invite attempt

### Implementation for US8

- [ ] T031 [US8] Handle IdP adapter exceptions in RegistrationService in src/services/registration_service.py
- [ ] T032 [US8] Set invite_status=failed and invite_error on registration when IdP fails in src/services/registration_service.py
- [ ] T033 [US8] Emit invite.failed audit event in src/services/registration_service.py
- [ ] T034 [US8] Create POST /registration/{registration_id}/resend-invite endpoint in src/api/v1/registration.py
- [ ] T035 [US8] Add validation: only allow resend when invite_status=failed in src/services/registration_service.py
- [ ] T036 [US8] Add INVALID_INVITE_STATUS error response in src/api/v1/registration.py

**Checkpoint**: IdP failures handled gracefully with resend capability

---

## Phase 9: User Story 9 - Personal Email Warning (Priority: P3)

**Goal**: Warn users about personal email usage (soft warning, not blocking)

**Independent Test**: Enter gmail.com email, verify warning returned in response but registration still succeeds

### Implementation for US9

- [ ] T037 [US9] Create personal email domain detection service in src/core/email_utils.py
- [ ] T038 [US9] Add PERSONAL_EMAIL_DOMAINS configuration (gmail.com, yahoo.com, etc.) in src/config.py
- [ ] T039 [US9] Add personal_email_warning field to RegistrationResponse in src/schemas/registration.py
- [ ] T040 [US9] Integrate personal email check in registration flow in src/services/registration_service.py

**Checkpoint**: Personal email warning displayed without blocking registration

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Testing, documentation, and cleanup

- [ ] T041 [P] Create unit tests for RegistrationService in tests/unit/services/test_registration_service.py
- [ ] T042 [P] Create unit tests for registration API in tests/unit/api/test_registration.py
- [ ] T043 [P] Create integration tests for registration flow in tests/integration/test_registration_flow.py
- [ ] T044 [P] Create unit tests for slug generation in tests/unit/core/test_slug_utils.py
- [ ] T045 [P] Create unit tests for rate limiter in tests/unit/core/test_rate_limiter.py
- [ ] T046 Update models __init__.py to export new models in src/models/__init__.py
- [ ] T047 Update schemas __init__.py to export registration schemas in src/schemas/__init__.py
- [ ] T048 Add pending registration cleanup task placeholder in src/services/registration_service.py (scheduled job for 7-day cleanup)
- [ ] T049 Run quickstart.md validation to verify curl examples work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - MVP (Phase 3) must complete first
  - US4-US8 (Phase 4-8) can proceed in parallel after MVP
  - US9 (Phase 9) can proceed after any Phase 4-8
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1, US2, US3 (MVP - Phase 3)**: Can start after Foundational (Phase 2) - Core registration flow
- **US4 (Duplicate Email - Phase 4)**: Depends on MVP - Adds email uniqueness check
- **US5 (Slug Generation - Phase 5)**: Depends on MVP - Enhances slug handling
- **US6 (Legal Acceptance - Phase 6)**: Depends on MVP - Adds validation
- **US7 (Rate Limiting - Phase 7)**: Depends on MVP - Adds protection layer
- **US8 (IdP Failure - Phase 8)**: Depends on MVP - Adds error handling
- **US9 (Personal Email - Phase 9)**: Depends on MVP - Adds warning feature

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T002, T003, T004) can run in parallel
- Foundational migrations (T005, T006) can run in parallel
- Foundational models (T007, T008) can run in parallel
- US4-US8 can be worked on in parallel after MVP completes
- All test tasks (T041-T045) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Run migrations in parallel:
Task: "Create database migration to extend organizations table (T005)"
Task: "Create database migration for registrations table (T006)"

# Run model creation in parallel after migrations:
Task: "Extend Organization model (T007)"
Task: "Create Registration model (T008)"
```

---

## Implementation Strategy

### MVP First (Phase 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: MVP (US1, US2, US3)
4. **STOP and VALIDATE**: Test basic registration flow
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add MVP (US1-US3) → Test independently → Deploy/Demo (MVP!)
3. Add US4 (Duplicate Email) → Test independently → Deploy/Demo
4. Add US5-US8 → Test each independently → Deploy/Demo
5. Add US9 (Personal Email Warning) → Test independently → Deploy/Demo
6. Complete Polish phase → Full feature ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Team completes MVP together (critical path)
3. Once MVP is done:
   - Developer A: US4 (Duplicate Email)
   - Developer B: US5 (Slug Generation)
   - Developer C: US6 (Legal Acceptance)
   - Developer D: US7 (Rate Limiting)
4. Continue with US8, US9, Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Rate limiter uses Redis (already in infrastructure)
- IdP adapter is stubbed for MVP (real implementation in separate feature)
