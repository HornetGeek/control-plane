# Feature Specification: Organization Registration

**Feature Branch**: `001-organization-registration`
**Created**: 2026-02-17
**Status**: Draft
**Input**: User description: "Organization Registration - Self-service registration for new customers to create their organization account"
**Epic**: EP-CP-001: Customer & Organization Management
**Source**: Vision v2.3, PRD v3.0

## Overview

Self-service organization registration for new customers to create their organization account on the platform. The registration follows an invite-only OIDC model where the platform does not handle passwords - instead, it initiates an IdP invite flow for the admin user.

## Clarifications

### Session 2026-02-17

- Q: How should unique organization slug be generated when name conflicts? → A: Short random suffix (e.g., `acme-corp-7x9k`)
- Q: What is the initial rate limit threshold per IP? → A: 10 attempts per hour (configurable); return `429` + `Retry-After` when blocked; repeated violations follow backoff ladder (default: 1min, 5min, 15min, 1hr; configurable)
- Q: How long should failed/pending registrations be retained before cleanup? → A: 7 days (configurable); cleanup may delete/redact PII but MUST preserve audit evidence per retention policy
- Q: Which status transitions are valid for organizations? → A: pending_invite → active (via IdP verification), suspension handled separately by admin
- Q: How to handle concurrent registrations with same email? → A: First write wins, second gets duplicate error
- Q: What is the MVP scope for US-CP-001? → A: Form (no password), create org + pending admin, `pending_invite`, unique slug, duplicate email block, ToS/Privacy acceptance capture, Trial plan assigned, IdP invite attempt, baseline per-IP rate limiting, audit events
- Q: When does the trial start? → A: Assign Trial plan at org creation; trial clock and entitlements start when org becomes `active` (US-CP-002)
- Q: What is the minimal registration API contract? → A: Support `Idempotency-Key`; success returns `registration_id`, `organization_id`, `organization_slug`, `status`, `invite_status`; errors use `409`/`422`/`429` (and include `Retry-After` on `429`)
- Q: How should IdP invite failure behave at the API level? → A: Keep org as `pending_invite` with `invite_status=failed` and error flag; surface actionable message; allow "resend invite" without creating a new organization
- Q: Are audit events required for US-CP-001? → A: Yes; emit at minimum: registration.initiated, registration.submitted, invite.sent, invite.failed, registration.rate_limited (with correlation IDs; masked/minimized IP/email per policy)
- Q: What are canonical data formats? → A: `country_code` ISO 3166-1 alpha-2; `phone_number` E.164 (if present); `accepted_locale` BCP 47; timestamps UTC ISO-8601
- Q: Is CAPTCHA required? → A: Not required for MVP; policy-configurable
- Q: Is Stripe/payment part of registration? → A: No; payment/billing setup is post-activation and handled in a separate story

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Display Registration Form (Priority: P1)

As a new visitor on the platform website, I want to access the registration form so that I can start the process of creating my organization account.

**Why this priority**: This is the entry point for all new customers. Without this form, no registrations can occur.

**Independent Test**: Navigate to the registration page and verify all required fields are displayed without a password field.

**Acceptance Scenarios**:

1. **Given** I am a new visitor on the platform website, **When** I click "Get Started" or "Sign Up", **Then** I should see the organization registration form
2. **Given** the registration form is displayed, **When** I view the form fields, **Then** the form should request: Organization Name (required), Work Email (required), Admin First Name (required), Admin Last Name (required), Country (required), Phone Number (optional)
3. **Given** the registration form is displayed, **When** I look for password fields, **Then** no password field should be present

---

### User Story 2 - Complete Registration (Priority: P1)

As a new customer, I want to submit my registration information so that my organization is created and I receive an email to complete setup.

**Why this priority**: This is the core action that creates the organization and initiates the IdP invite flow.

**Independent Test**: Fill valid registration data, submit the form, and verify organization is created with pending_invite status and confirmation message is shown.

**Acceptance Scenarios**:

1. **Given** I am on the registration form, **When** I enter valid organization details and accept Terms of Service, **Then** organization should be created with status "pending_invite"
2. **Given** registration is successful, **When** the response is returned, **Then** it should include registration_id for tracking
3. **Given** registration is successful, **When** I view the confirmation, **Then** I should see "Check your email to complete setup"
4. **Given** registration is successful, **When** the system processes the registration, **Then** IdP invite should be initiated for admin email

---

### User Story 3 - Trial Plan Assignment (Priority: P1)

As a new customer, I want my organization to have a trial plan assigned automatically so that I can start using the platform immediately after verification.

**Why this priority**: Trial plan is essential for customer acquisition and immediate value delivery.

**Independent Test**: Complete registration and verify trial plan is assigned with correct duration.

**Acceptance Scenarios**:

1. **Given** organization is created with status "pending_invite", **When** registration completes, **Then** organization should have "Trial" plan assigned immediately (plan is present even while pending)
2. **Given** trial plan is assigned, **When** I check the trial duration, **Then** it should be 14 days (configurable)
3. **Given** organization is "pending_invite", **When** the organization later becomes "active" (US-CP-002), **Then** the trial clock and trial entitlements should start at activation time (not at form submission time)

---

### User Story 4 - Duplicate Email Prevention (Priority: P2)

As a platform, I want to prevent duplicate admin email registrations so that each email is uniquely associated with one account.

**Why this priority**: Prevents confusion and ensures account integrity, but registration can still function without this check temporarily.

**Independent Test**: Attempt to register with an already-registered email and verify appropriate error message and sign-in link.

**Acceptance Scenarios**:

1. **Given** email "admin@acme.com" is already registered, **When** I try to register with email "admin@acme.com", **Then** I should see error "This email is already associated with an account"
2. **Given** duplicate email registration attempt, **When** the error is displayed, **Then** I should see link "Sign in instead"
3. **Given** duplicate email registration attempt, **When** I view the result, **Then** registration should be blocked

---

### User Story 5 - Duplicate Organization Name Handling (Priority: P2)

As a new customer, I want to use any organization name I prefer, even if it's already taken, so that I can name my organization appropriately.

**Why this priority**: Enhances user experience by allowing flexible naming while maintaining unique identifiers.

**Independent Test**: Attempt to register with a duplicate organization name and verify unique slug is auto-generated.

**Acceptance Scenarios**:

1. **Given** organization with display name "Acme Corp" already exists, **When** I try to register organization "Acme Corp", **Then** organization slug should be auto-generated as unique
2. **Given** duplicate organization name, **When** slug is generated, **Then** I should see the resulting slug/URL preview for transparency
3. **Given** duplicate organization name, **When** I view the guidance, **Then** I should see "Organization name 'Acme Corp' is in use. Your organization URL will be unique."
4. **Given** duplicate organization name, **When** I submit registration, **Then** registration should proceed with unique slug

---

### User Story 6 - Terms and Privacy Policy Acceptance (Priority: P2)

As a platform operator, I want to ensure customers accept legal terms before registration so that we have proper legal consent.

**Why this priority**: Legal compliance is important but can be temporarily bypassed in development.

**Independent Test**: Attempt registration without accepting terms and verify error; complete registration with acceptance and verify metadata is captured.

**Acceptance Scenarios**:

1. **Given** I have filled all registration fields correctly, **When** I have not checked "I accept the Terms of Service and Privacy Policy" and click "Create Account", **Then** I should see error "Please accept the Terms of Service and Privacy Policy"
2. **Given** I complete registration with legal acceptance, **When** the system records acceptance, **Then** it should capture: terms_version, privacy_policy_version, accepted_at, accepted_locale

---

### User Story 7 - Personal Email Warning (Priority: P3)

As a new customer, I want to be warned when using a personal email so that I understand the recommendation to use a business email.

**Why this priority**: Nice-to-have feature that improves user experience but doesn't block registration.

**Independent Test**: Enter a personal email domain and verify warning is displayed while registration remains allowed.

**Acceptance Scenarios**:

1. **Given** I am on the registration form, **When** I enter email from personal domain (gmail.com, yahoo.com, etc.), **Then** I should see warning "We recommend using a business email address"
2. **Given** personal email warning is displayed, **When** I proceed with registration, **Then** registration should still be allowed (soft warning)
3. **Given** personal email policy is configured to block personal domains, **When** I submit registration with a personal email, **Then** registration should be blocked with error "Please use a business email address"

---

### User Story 8 - Rate Limiting and Abuse Prevention (Priority: P2)

As a platform operator, I want to prevent registration abuse so that the platform is protected from spam and malicious registrations.

**Why this priority**: Baseline controls are required for production readiness due to fraud/spam risk in EP-CP-001; advanced controls can be added later.

**Independent Test**: Exceed registration attempt threshold and verify appropriate blocking with exponential backoff.

**Acceptance Scenarios**:

1. **Given** an IP address has exceeded the registration attempt threshold (default: 10 attempts per hour; configurable), **When** another registration is attempted, **Then** registration should be blocked with `429`
2. **Given** rate limit is triggered, **When** I view the error, **Then** I should see "Too many registration attempts. Please try again later."
3. **Given** rate limit is triggered, **When** the block is applied, **Then** `Retry-After` should be returned and block duration should follow exponential backoff policy (default ladder: 1min, 5min, 15min, 1hr; configurable)
4. **Given** CAPTCHA policy is enabled, **When** registration abuse policy requires CAPTCHA, **Then** a CAPTCHA challenge should be presented before registration can proceed (not required for MVP)

---

### User Story 9 - IdP Invite Failure Handling (Priority: P2)

As a platform, I want to handle IdP invite failures gracefully so that users receive actionable feedback and pending registrations can be cleaned up.

**Why this priority**: Critical for production reliability but fail-closed behavior ensures data consistency.

**Independent Test**: Simulate IdP failure and verify organization remains in pending_invite status with error flag.

**Acceptance Scenarios**:

1. **Given** registration form is submitted successfully, **When** IdP invite initiation fails, **Then** organization should NOT be activated
2. **Given** IdP invite failure, **When** the system handles the error, **Then** organization should remain in "pending_invite" with error flag
3. **Given** IdP invite failure, **When** user views the result, **Then** they should see actionable error: "Unable to complete setup. Please try again or contact support."
4. **Given** IdP invite failure, **When** the user retries via "Resend invite" (or support triggers a resend), **Then** the system should re-attempt IdP invite for the same registration without creating a new organization

---

### Edge Cases

- What happens when the IdP service is unavailable for an extended period?
- How does the system handle registration with an invalid country code?
- What happens if the email contains special characters or is malformed?
- **Concurrent registrations with same email**: First write wins, second request receives duplicate email error.
- What happens when phone number format is invalid for the selected country?
- How does the system handle network timeout during registration submission?
- What happens if Terms of Service version changes during registration flow?

**Pending Registration Cleanup**: Failed/pending registrations are automatically cleaned up after 7 days.

## Requirements *(mandatory)*

### Functional Requirements

**Registration Form**
- **FR-001**: System MUST display registration form without password field
- **FR-002**: System MUST collect: Organization Name (required), Work Email (required), First Name (required), Last Name (required), Country (required), Phone Number (optional)
- **FR-003**: System SHOULD display warning when personal email domain is detected (soft warning, does not block; policy MAY optionally block personal domains)
- **FR-004**: System MUST require Terms of Service and Privacy Policy acceptance before submission

**Organization Creation**
- **FR-005**: System MUST create organization with status "pending_invite" upon successful form submission
- **FR-006**: System MUST generate unique organization slug if display name conflicts with existing organization, using a short random suffix (e.g., `acme-corp-7x9k`)
- **FR-007**: System MUST return registration_id for tracking upon successful registration
- **FR-008**: System MUST display confirmation message "Check your email to complete setup" after successful registration

**IdP Integration**
- **FR-009**: System MUST initiate IdP invite for admin email upon successful registration
- **FR-010**: System MUST remain in "pending_invite" status if IdP invite fails
- **FR-011**: System MUST display actionable error message when IdP invite fails

**Duplicate Prevention**
- **FR-012**: System MUST block registration with email already registered in the system
- **FR-013**: System MUST display "Sign in instead" link when duplicate email is detected
- **FR-014**: System MUST allow duplicate organization display names with unique slugs

**Trial Assignment**
- **FR-015**: System MUST assign "Trial" plan immediately upon organization creation (even while "pending_invite")
- **FR-016**: System MUST set trial duration to 14 days (configurable)

**Legal Acceptance**
- **FR-017**: System MUST capture terms_version, privacy_policy_version, accepted_at, and accepted_locale upon acceptance

**Rate Limiting**
- **FR-018**: System MUST enforce rate limits on registration attempts per IP address (10 attempts per hour before blocking)
- **FR-019**: System MUST apply exponential backoff for repeated rate limit violations

**Trial Activation Timing**
- **FR-020**: System MUST start the trial clock and enable trial entitlements when the organization becomes "active" (US-CP-002), not at registration submission time

**CAPTCHA (Policy-Configurable)**
- **FR-021**: System MAY require a CAPTCHA challenge for registration based on deployment policy (not required for MVP)

**Audit Trail**
- **FR-022**: System MUST emit audit events for registration lifecycle (at minimum: registration.initiated, registration.submitted, invite.sent, invite.failed, registration.rate_limited)
- **FR-023**: System MUST include correlation identifiers (e.g., request_id/correlation_id) and apply privacy-safe handling (mask/minimize IP address and email) per policy

**Retention & Cleanup**
- **FR-024**: System MUST apply a retention policy for non-activated registrations (default: 7 days; configurable) while preserving audit evidence

**API Contract**
- **FR-025**: System MUST support idempotent registration submission via `Idempotency-Key` to prevent duplicate organizations on retries/timeouts
- **FR-026**: System MUST return machine-readable errors with appropriate HTTP codes (`409` duplicate email, `422` validation errors, `429` rate limited) and return `Retry-After` when rate limited

**Data Validation**
- **FR-027**: System MUST validate canonical formats: `country_code` (ISO 3166-1 alpha-2), `phone_number` (E.164 if present), `accepted_locale` (BCP 47), and timestamps in UTC

### Key Entities

- **Organization**: Represents a customer's business entity on the platform. Key attributes: display name, unique slug, status (pending_invite, active, suspended), trial plan, trial_assigned_at, trial_starts_at, trial_ends_at, creation timestamp, legal acceptance metadata. **Status transitions**: pending_invite → active (via IdP verification in US-CP-002); suspension is a separate admin action outside this feature's scope.

- **Admin User (Pending)**: The initial administrator for the organization. Key attributes: email, first name, last name, phone (optional), IdP invite status (pending/sent/failed), link to organization.

- **Registration**: Tracks the registration process. Key attributes: registration_id, organization reference, admin email, status, invite_status, timestamps, error flags, correlation data for audit, idempotency key.

- **Legal Acceptance**: Records consent to terms. Key attributes: terms_version, privacy_policy_version, accepted_at, accepted_locale, organization reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete registration form submission in under 2 minutes
- **SC-002**: Registration completion rate exceeds 85% (started vs completed submissions)
- **SC-003**: IdP invite is initiated within 5 seconds of successful registration
- **SC-004**: System supports 100 concurrent registration attempts without degradation
- **SC-005**: Duplicate email detection prevents 100% of duplicate registrations
- **SC-006**: Unique slug generation handles 100% of duplicate organization name scenarios
- **SC-007**: Rate limiting blocks 100% of excessive registration attempts from single IP
- **SC-008**: Error messages are displayed to users within 2 seconds of validation failure
- **SC-009**: Trial plan is assigned to 100% of newly created organizations
- **SC-010**: Legal acceptance metadata is captured for 100% of completed registrations

## Assumptions

- The platform uses an external Identity Provider (IdP) such as Keycloak, Auth0, or Okta
- The IdP adapter interface is already implemented and available
- Email service is operational for sending IdP invite emails
- Country list is predefined and maintained by the platform
- Personal email domains list includes common providers (gmail.com, yahoo.com, hotmail.com, outlook.com, etc.)
- Terms of Service and Privacy Policy versions are managed by the platform
- Default trial duration is 14 days but is configurable per deployment
- Registration rate limits use standard exponential backoff (1min, 5min, 15min, 1hr)

## Dependencies

- IdP Adapter interface (for initiating user invites)
- Email Service (for sending invite emails)
- Audit event emission (for compliance logging)
- Country/region data service
- Rate limiting storage/mechanism (e.g., Redis or gateway rate limiting)

## Out of Scope

- Social login integration (Google, Microsoft) - Future enhancement
- SSO/SAML registration - Covered in separate feature
- Bulk organization import - Enterprise feature
- Password handling - IdP responsibility
- Email verification flow - Separate feature (US-CP-002)
- Payment/billing setup during registration (e.g., Stripe) - Separate feature (post-activation onboarding)
