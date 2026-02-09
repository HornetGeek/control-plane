# Feature Specification: Control Plane MVP

**Feature Branch**: `001-control-plane-mvp`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Control Plane MVP - Multi-tenant SaaS with OIDC auth, organization/tenant management, subscriptions, and launch routing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Authentication & Organization Association (Priority: P1)

A new user needs to authenticate via the organization's identity provider and be associated with their organization so they can access the platform.

**Why this priority**: Without authentication and user-to-org linking, no other functionality is accessible. This is the foundation for all secured operations.

**Independent Test**: Can be fully tested by initiating login flow, completing OIDC authentication, and verifying the user record is created with correct organization association.

**Acceptance Scenarios**:

1. **Given** no user exists, **When** user completes OIDC authentication via Zitadel, **Then** a new user record is created with idp_sub, email, name, and organization association
2. **Given** user exists, **When** user completes OIDC authentication, **Then** user's last_login_at is updated and session is established
3. **Given** user authentication fails, **When** invalid/expired token is presented, **Then** access is denied with appropriate error message

---

### User Story 2 - Tenant Management for Organization (Priority: P1)

An organization administrator needs to create and manage tenants (branches) within their organization to represent different business units or locations.

**Why this priority**: Tenants are the core organizational unit for subscription scoping. Without tenant creation, the platform cannot serve multi-branch organizations.

**Independent Test**: Can be fully tested by an org_admin creating a tenant, listing tenants, and verifying tenant details are correctly associated with the organization.

**Acceptance Scenarios**:

1. **Given** user is org_admin, **When** they create a new tenant with name, **Then** tenant is created and associated with their organization
2. **Given** user is org_admin, **When** they list tenants, **Then** all tenants in their organization are returned
3. **Given** user is org_admin, **When** they request tenant details by ID, **Then** tenant information is returned if it belongs to their organization
4. **Given** user is not org_admin, **When** they attempt to create a tenant, **Then** access is denied

---

### User Story 3 - Tenant Membership Management (Priority: P2)

An administrator needs to add users to tenants with specific roles so users can access tenant-specific resources and applications.

**Why this priority**: Membership enables users to work with specific tenants. This is critical for multi-user collaboration but can be initially seeded by admins.

**Independent Test**: Can be fully tested by adding a user to a tenant with a role, listing members, and verifying the user can access tenant resources.

**Acceptance Scenarios**:

1. **Given** user is org_admin or tenant_admin, **When** they add a user to a tenant with a role, **Then** membership is created and user can access tenant
2. **Given** user is org_admin or tenant_admin, **When** they list tenant members, **Then** all members and their roles are returned
3. **Given** user is org_admin or tenant_admin, **When** they remove a user from a tenant, **Then** membership is deleted and user loses access
4. **Given** user is not authorized, **When** they attempt to modify memberships, **Then** access is denied

---

### User Story 4 - Application Subscription Management (Priority: P2)

An administrator needs to subscribe their tenant to applications (PACS, ERP) so tenant members can launch and use those applications.

**Why this priority**: Subscriptions control which applications tenants can access. This is essential for the platform's business model but can be initially configured by admins.

**Independent Test**: Can be fully tested by subscribing a tenant to an application, listing subscriptions, and updating subscription status.

**Acceptance Scenarios**:

1. **Given** user is org_admin or tenant_admin, **When** they subscribe tenant to an application, **Then** subscription is created (idempotent - duplicate returns existing)
2. **Given** user is org_admin or tenant_admin, **When** they list tenant subscriptions, **Then** all subscriptions for the tenant are returned
3. **Given** user is org_admin or tenant_admin, **When** they update subscription status, **Then** status is changed (active/suspended/canceled)
4. **Given** duplicate subscription request, **When** same tenant+app is requested again, **Then** existing subscription is returned without error

---

### User Story 5 - Application Launch (Priority: P3)

A tenant member needs to launch a subscribed application so they can access the application with their tenant context and authentication.

**Why this priority**: Launch is the primary user action that delivers value. Members need to access applications they're entitled to use.

**Independent Test**: Can be fully tested by a tenant member requesting launch for a subscribed application and receiving a valid redirect URL.

**Acceptance Scenarios**:

1. **Given** user is tenant member, **When** they request launch for subscribed app, **Then** redirect URL with tenant_id and token is returned
2. **Given** user is tenant member, **When** they request launch for unsubscribed app, **Then** access is denied with appropriate error
3. **Given** user is not tenant member, **When** they request launch for app, **Then** access is denied
4. **Given** application is inactive, **When** user requests launch, **Then** access is denied

---

### Edge Cases

- What happens when a user's organization cannot be determined from OIDC claims during first login?
  - **Resolution**: Authentication fails with error. The `org_id` claim is required in the OIDC token. Zitadel must be configured to include this claim for all users.
- What happens when a user is removed from all tenants but still belongs to an organization?
  - User retains organization membership but cannot access any tenant resources
- What happens when a subscription is suspended while a user is actively using an application?
  - Existing sessions may continue but new launch requests are denied
- What happens when an organization has no tenants?
  - Organization exists but members have no tenant-specific access
- What happens when the last member of a tenant is removed?
  - Tenant persists (soft delete not required for MVP) and can be re-populated

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Authorization**
- **FR-001**: System MUST authenticate users via OpenID Connect authorization code flow with Zitadel
- **FR-002**: System MUST validate bearer tokens using issuer URL and JWKS endpoint discovery
- **FR-003**: System MUST extract user identity (sub claim) from validated tokens
- **FR-004**: System MUST extract organization association from the required `org_id` claim in the OIDC token (authentication fails if claim is missing)
- **FR-005**: System MUST deny access to protected resources without valid bearer token
- **FR-006**: System MUST enforce organization boundaries on every request (no cross-org access)
- **FR-007**: System MUST enforce role-based permissions (org_admin, tenant_admin, tenant_member)

**User Management**
- **FR-008**: System MUST create user record on first successful OIDC authentication with idp_sub, email, name
- **FR-009**: System MUST associate each user with exactly one organization
- **FR-010**: System MUST update user's last_login_at timestamp on successful authentication
- **FR-011**: System MUST allow querying current user information (/auth/me endpoint)

**Tenant Management**
- **FR-012**: System MUST allow org_admin to create tenants within their organization
- **FR-013**: System MUST allow org_admin to list all tenants in their organization
- **FR-014**: System MUST allow users to list tenants they are members of
- **FR-015**: System MUST allow authorized users to retrieve tenant details by ID
- **FR-016**: System MUST reject tenant creation by non-org_admin users

**Membership Management**
- **FR-017**: System MUST allow org_admin to add users to any tenant in their organization
- **FR-018**: System MUST allow tenant_admin to add users to their specific tenant
- **FR-019**: System MUST allow org_admin and tenant_admin to list tenant members
- **FR-020**: System MUST allow org_admin and tenant_admin to remove users from a tenant
- **FR-021**: System MUST assign a role (org_admin, tenant_admin, tenant_member) to each membership
- **FR-022**: System MUST reject membership modifications by tenant_member

**Application Management**
- **FR-023**: System MUST provide a read-only catalog of available applications
- **FR-024**: System MUST include application key, name, and launch base URL in catalog
- **FR-025**: System MUST seed initial applications (PACS, ERP) on startup

**Subscription Management**
- **FR-026**: System MUST allow org_admin and tenant_admin to subscribe their tenant to applications
- **FR-027**: System MUST make subscription creation idempotent per (tenant_id, app_key)
- **FR-028**: System MUST allow listing all subscriptions for a tenant
- **FR-029**: System MUST allow org_admin and tenant_admin to update subscription status
- **FR-030**: System MUST support subscription statuses: active, suspended, canceled
- **FR-031**: System MUST reject subscription modifications by tenant_member

**Launch**
- **FR-032**: System MUST validate user is member of tenant (or org_admin) before launch
- **FR-033**: System MUST validate tenant has active subscription to requested application
- **FR-034**: System MUST validate application is active and has launch base URL configured
- **FR-035**: System MUST return redirect URL with tenant_id, access_token, and return_to parameters
- **FR-036**: System MUST reject launch requests when membership, subscription, or application status is invalid

**Observability**
- **FR-037**: System MUST accept or generate correlation ID (X-Request-ID header) for each request
- **FR-038**: System MUST return correlation ID in response headers
- **FR-039**: System MUST log all authorization failures with correlation ID
- **FR-040**: System MUST provide OpenAPI schema for all endpoints

### Key Entities

**Organization**: Top-level customer entity containing tenants and users. Key attributes: unique identifier, name, creation timestamp. Relationships: has many tenants, has many users.

**Tenant**: Branch or business unit within an organization. Subscription is scoped at tenant level. Key attributes: unique identifier, organization reference, name, creation timestamp. Relationships: belongs to organization, has many memberships, has many subscriptions.

**User**: Person authenticated via OIDC. Belongs to exactly one organization. Key attributes: unique identifier, organization reference, identity provider subject (idp_sub), email, name, creation timestamp, last login timestamp, status. Relationships: belongs to organization, has many memberships.

**Membership**: Association between a user and a tenant with a specific role. Key attributes: unique identifier, tenant reference, user reference, role (org_admin/tenant_admin/tenant_member), status, creation timestamp. Relationships: belongs to tenant, belongs to user.

**Application**: Product that tenants can subscribe to (PACS, ERP). Key attributes: unique key (app_key), name, launch base URL, status. Relationships: has many subscriptions.

**Subscription**: Entitlement that allows a tenant to access an application. Key attributes: unique identifier, tenant reference, application key, status (active/suspended/canceled), start timestamp, update timestamp. Relationships: belongs to tenant, references application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: New users can complete authentication and access the platform within 30 seconds
- **SC-002**: Organization administrators can create a new tenant in under 10 seconds
- **SC-003**: Administrators can add users to tenants with roles in under 5 seconds per user
- **SC-004**: Tenant members can launch subscribed applications and receive redirect URL within 2 seconds
- **SC-005**: 100% of protected endpoints reject requests without valid bearer token
- **SC-006**: 100% of cross-organization access attempts are blocked
- **SC-007**: 100% of unauthorized role-based access attempts are blocked
- **SC-008**: System supports 1000 concurrent authentication requests without degradation
- **SC-009**: 95% of API requests complete within 500 milliseconds
- **SC-010**: All authorization failures include correlation ID for troubleshooting
