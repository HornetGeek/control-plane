# Feature Specification: OIDC Authentication

**Feature Branch**: `002-oidc-auth`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "OIDC Authentication - OpenID Connect authentication with Zitadel identity provider, including user login, token validation, user provisioning, and organization mapping from claims"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Login via Identity Provider (Priority: P1)

A user needs to log into the control plane using their organization's existing identity provider (Zitadel) so they can access applications without managing separate credentials.

**Why this priority**: Authentication is the foundational requirement. Without it, no user can access any functionality. This is the entry point for all user interactions.

**Independent Test**: Can be fully tested by initiating login flow, completing authentication at the IdP, and verifying the user receives a valid token and user record.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user, **When** they navigate to the login endpoint, **Then** they are redirected to the Zitadel authorization page
2. **Given** a user at the Zitadel login page, **When** they complete authentication with valid credentials, **Then** they are redirected back to the callback endpoint with an authorization code
3. **Given** a valid authorization code, **When** the callback processes the code, **Then** the system exchanges it for tokens and returns an access token with user information
4. **Given** an invalid or expired authorization code, **When** the callback processes it, **Then** an appropriate error response is returned

---

### User Story 2 - Automatic User Provisioning (Priority: P1)

A user logging in for the first time needs their account to be automatically created and linked to their organization so they can immediately access the platform without manual account setup.

**Why this priority**: User provisioning is tightly coupled with authentication. Without auto-provisioning, first-time users would need manual account creation, creating a barrier to entry.

**Independent Test**: Can be fully tested by authenticating a new user (with valid org_id claim) and verifying a user record is created with correct organization association and profile data.

**Acceptance Scenarios**:

1. **Given** a user authenticating for the first time, **When** their token contains valid sub, org_id, email, and name claims, **Then** a new user record is created with the idp_sub stored as the unique identifier
2. **Given** a user authenticating for the first time, **When** the user record is created, **Then** the user is automatically associated with the organization specified in the org_id claim
3. **Given** a user authenticating for the first time, **When** the user record is created, **Then** the user status is set to active
4. **Given** a returning user, **When** they authenticate with the same idp_sub, **Then** the existing user record is found and their last_login_at timestamp is updated

---

### User Story 3 - Token Validation for API Access (Priority: P1)

A user needs to make authenticated API calls using their access token so they can access protected resources like tenants, subscriptions, and application launch.

**Why this priority**: Token validation enables all secured API endpoints. Without it, there is no way to protect resources after login.

**Independent Test**: Can be fully tested by calling a protected endpoint with a valid token (should succeed) and with an invalid/expired token (should be rejected).

**Acceptance Scenarios**:

1. **Given** a user with a valid access token, **When** they call a protected endpoint with the Bearer token, **Then** the request is allowed and user context is extracted from the token
2. **Given** a user with an expired access token, **When** they call a protected endpoint, **Then** the request is rejected with a 401 Unauthorized response
3. **Given** a user with a tampered token, **When** they call a protected endpoint, **Then** the request is rejected with a 401 Unauthorized response
4. **Given** a request without any token, **When** they attempt to access a protected endpoint, **Then** the request is rejected with a 401 Unauthorized response

---

### User Story 4 - Current User Information Lookup (Priority: P2)

An authenticated user needs to retrieve their current profile information so they can display their name, email, organization, and last login timestamp in the application UI.

**Why this priority**: User info lookup is essential for UI personalization but is a read-only operation that doesn't block core functionality.

**Independent Test**: Can be fully tested by calling the /me endpoint with a valid token and verifying the response contains all user profile fields.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they request their current user information, **Then** the system returns their id, email, name, organization_id, and last_login_at
2. **Given** an unauthenticated request, **When** they attempt to access the /me endpoint, **Then** the request is rejected with a 401 Unauthorized response

---

### User Story 5 - Organization Context Enforcement (Priority: P2)

The system needs to enforce organization boundaries on every authenticated request so that users from one organization cannot access data from another organization.

**Why this priority**: Multi-tenancy security is critical for data isolation, but the enforcement mechanism can be validated independently per endpoint.

**Independent Test**: Can be fully tested by making authenticated requests for resources belonging to different organizations and verifying cross-org access is blocked.

**Acceptance Scenarios**:

1. **Given** a user from organization A, **When** they attempt to access a resource owned by organization B, **Then** the request is rejected with an authorization error
2. **Given** a user from organization A, **When** they access their own organization's resources, **Then** the request is allowed

---

### Edge Cases

- What happens when the org_id claim is missing from the OIDC token?
  - Authentication fails with a clear error message indicating the required claim is missing. The IdP must be configured to include the org_id claim for all users.

- What happens when the email claim is missing from the OIDC token?
  - Authentication fails with an error indicating the email claim is required. Email is a mandatory field for user records.

- What happens when a user's organization doesn't exist in the database?
  - The user is associated with the organization_id from the claim regardless of whether an organization record exists. This allows for organization records to be created separately (e.g., during customer onboarding).

- What happens when the OIDC provider (Zitadel) is unavailable during login?
  - The login redirect fails, and the user receives an error. The system does not cache or fallback to alternative authentication methods.

- What happens when JWKS endpoint is unavailable during token validation?
  - Token validation fails with an appropriate error. The system uses a cached JWKS when available but cannot validate tokens without access to signing keys.

- What happens when a user's idp_sub changes (e.g., account recreation at IdP)?
  - A new user record is created because idp_sub is the unique identifier. The old record remains but is no longer accessible via SSO.

- What happens when multiple organizations share the same IdP?
  - The org_id claim in the token determines which organization the user belongs to. Users with different org_id values are isolated even if they authenticate through the same IdP.

## Requirements *(mandatory)*

### Functional Requirements

**Authentication Flow**

- **FR-001**: System MUST redirect users to the OIDC provider's authorization endpoint when initiating login
- **FR-002**: System MUST include the response_type=code, client_id, redirect_uri, scope, and state parameters in the authorization request
- **FR-003**: System MUST generate a cryptographically random state parameter for CSRF protection
- **FR-004**: System MUST exchange the authorization code for tokens at the OIDC token endpoint using the authorization_code grant type
- **FR-005**: System MUST validate the received ID token (or access token if ID token unavailable) before trusting its claims

**Token Validation**

- **FR-006**: System MUST validate tokens using the JWKS (JSON Web Key Set) endpoint from the OIDC provider
- **FR-007**: System MUST verify the token signature using the signing key from JWKS
- **FR-008**: System MUST verify the token's issuer matches the configured OIDC issuer URL
- **FR-009**: System MUST verify the token's audience matches the configured client ID
- **FR-010**: System MUST reject expired, invalid, or tampered tokens
- **FR-011**: System MUST cache JWKS keys for 5 minutes to reduce network calls

**Required Claims**

- **FR-012**: System MUST extract the sub (subject) claim as the user's unique identifier from the IdP
- **FR-013**: System MUST extract the org_id claim as the user's organization identifier
- **FR-014**: System MUST extract the email claim as the user's email address
- **FR-015**: System MUST extract the name claim as the user's display name
- **FR-016**: System MUST reject authentication when the sub claim is missing
- **FR-017**: System MUST reject authentication when the org_id claim is missing
- **FR-018**: System MUST reject authentication when the email claim is missing

**User Provisioning**

- **FR-019**: System MUST automatically create a new user record on first successful authentication
- **FR-020**: System MUST store the idp_sub (sub claim) as a unique identifier for the user
- **FR-021**: System MUST associate the user with the organization specified in the org_id claim
- **FR-022**: System MUST set the user's status to active upon creation
- **FR-023**: System MUST update the user's last_login_at timestamp on each successful authentication
- **FR-024**: System MUST return the existing user record if a user with the same idp_sub already exists
- **FR-025**: System MUST NOT modify the user's organization if they already exist (org_id is set only on creation)

**API Authentication**

- **FR-026**: System MUST accept bearer tokens via the Authorization header for protected endpoints
- **FR-027**: System MUST validate the bearer token on every request to protected endpoints
- **FR-028**: System MUST return 401 Unauthorized for requests with invalid, expired, or missing tokens
- **FR-029**: System MUST extract user context (user_id, org_id, email, name) from validated tokens
- **FR-030**: System MUST make user context available to endpoint handlers for authorization decisions

**User Information Endpoint**

- **FR-031**: System MUST provide an endpoint to retrieve current user information
- **FR-032**: System MUST require authentication for the user information endpoint
- **FR-033**: System MUST return the user's id, email, name, organization_id, and last_login_at

**Security**

- **FR-034**: System MUST use HTTPS for all OIDC communications
- **FR-035**: System MUST not log sensitive token data (access tokens, ID tokens)
- **FR-036**: System MUST validate and sanitize all redirect URIs to prevent open redirect vulnerabilities

### Key Entities

**User**: Person authenticated via OIDC. Key attributes: unique identifier (UUID), identity provider subject (idp_sub - from OIDC sub claim), organization reference (organization_id - from OIDC org_id claim), email, display name, last login timestamp, status. Relationships: belongs to one organization.

**Organization**: Top-level customer entity. Key attributes: unique identifier (UUID), name. Relationships: has many users.

**OIDC Token**: JSON Web Token issued by the identity provider. Contains claims: sub (user's unique IdP identifier), org_id (user's organization ID), email, name, issuer, audience, expiration time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the full authentication flow (login redirect to token receipt) in under 10 seconds under normal network conditions
- **SC-002**: New users are automatically provisioned with correct organization association 100% of the time when valid claims are present
- **SC-003**: Token validation completes in under 500 milliseconds for 95% of requests when JWKS is cached
- **SC-004**: 100% of requests without valid bearer tokens are rejected with 401 Unauthorized
- **SC-005**: 100% of tokens with invalid signatures, wrong issuer, or wrong audience are rejected
- **SC-006**: System handles 1000 concurrent authentication requests without degradation
- **SC-007**: JWKS caching reduces external calls by at least 90% under sustained load
- **SC-008**: Cross-organization access attempts are blocked 100% of the time
- **SC-009**: User information lookup returns complete profile data in under 200 milliseconds

## Assumptions

1. The identity provider (Zitadel) is configured to include a custom org_id claim in tokens for all users
2. Organizations are created in the system before users authenticate (or are created through a separate onboarding process)
3. The system uses the authorization code flow (not implicit or hybrid flows)
4. The OIDC provider supports JWKS for public key discovery
5. Tokens use RS256 algorithm for signing
6. The system trusts the OIDC provider's user claims without additional verification
7. Session management (logout, session revocation) is handled separately or via IdP session management
8. Refresh token rotation is not implemented in this feature (access tokens are used until expiration)
