<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 -> 1.1.0
Modified principles:
  - IV. OIDC-First Authentication (Zitadel → Keycloak, claim changes)
  - II. Strict Tenancy Boundaries (added One User = One Org)
Added sections:
  - Pre-login Onboarding principle
  - Trial Subscriptions principle
Removed sections: None
Templates requiring updates:
  - ✅ spec-template.md - No updates needed
  - ✅ plan-template.md - No updates needed
  - ✅ tasks-template.md - No updates needed
Follow-up TODOs: Regenerate tasks.md to align with updated constitution
-->

# Control Plane Constitution

## Core Principles

### I. API-First Architecture
**All functionality is exposed via REST API; no web UI in this service.**

Rationale: As a microservice in a larger SaaS platform, the Control Plane serves as the backend for other services and potential frontends. Keeping it API-only ensures clean separation of concerns and enables multiple client types (web, mobile, other services) to interact without UI coupling.

### II. Strict Tenancy Boundaries
**Organization and tenant boundaries MUST be enforced at all layers; cross-organization access is FORBIDDEN. One user belongs to exactly ONE organization.**

Rules:
- An Organization contains many Tenants (branches)
- A User belongs to exactly **one** Organization
- A User may have membership in multiple Tenants under the same Organization
- Cross-organization access MUST be rejected at the authorization layer
- Client-supplied `org_id` MUST never be trusted; derive from authenticated user mapping
- **Same IdP user (`idp_sub`) attempting to onboard into a different org is BLOCKED with error**

Rationale: Data isolation between organizations is critical for multi-tenant SaaS security. Any breach of tenancy boundaries is a critical security vulnerability. One-user-one-org simplifies security model for MVP.

### III. Subscription-Based Access Control
**Access to applications requires BOTH active tenant subscription AND user membership in that tenant.**

Rules:
- Subscriptions are managed at Tenant level (not organization or user level)
- Application access checks verify:
  1. Tenant has an active subscription to the application
  2. User has membership in the tenant
- Missing either condition results in 403 Forbidden

Rationale: This dual-requirement ensures proper billing boundaries and team/branch access control.

### IV. OIDC-First Authentication
**All authentication uses OpenID Connect with Keycloak (realm: control-plane); no password storage.**

Rules:
- Service acts as OIDC client using authorization code flow
- Keycloak realm: `control-plane`
- Issuer URL: `http://localhost:18080/realms/control-plane`
- Tokens validated via issuer + JWKS endpoint
- Required claims from IdP: `sub` (user ID), `email`, `name`
- **Organization association derived from pre-login onboarding session, NOT from IdP claim**
- `aud` (audience) claim validation is enforced
- Reject unsigned tokens or unknown algorithms
- Token validation MUST happen before any authorization checks

Rationale: Centralized auth with Keycloak provides consistent identity across the platform, eliminates password management risk, and enables SSO. Organization is determined by onboarding flow, not IdP, enabling self-service signup.

### V. Pre-Login Onboarding
**User selects application and provides org/tenant names BEFORE authentication.**

Rules:
- Onboarding collects: `app_id`, `org_name`, `tenant_name`
- Onboarding session has 60-minute TTL
- Onboarding session is single-consume (status: pending → consumed)
- OIDC `state` parameter MUST be bound to `onboarding_token` for CSRF protection
- On callback: auto-provision org (if not exists), tenant (if not exists), user, membership, trial subscription
- Onboarding session is consumed after successful provisioning

Rationale: Pre-login flow enables self-service signup without admin intervention. Session-based onboarding with TTL prevents abuse while allowing reasonable time for authentication.

### VI. Trial Subscriptions (MVP)
**All subscriptions are 14-day trials; no paid plans or billing in MVP.**

Rules:
- New subscriptions default to `status=trial`
- `trial_ends_at` is set to `now + 14 days` on creation
- Launch requests check if trial has expired
- No Stripe or payment processing
- Post-login endpoint allows adding additional trial subscriptions

Rationale: MVP focuses on user acquisition and platform validation. Billing complexity is deferred. Trial duration is sufficient for evaluation without indefinite free access.

### VII. Coarse-Grained Authorization
**Authorization uses three predefined roles; custom roles are NOT supported in MVP.**

Roles:
- `org_admin`: Can manage all tenants within their organization
- `tenant_admin`: Can manage a specific tenant only
- `tenant_member`: Read/launch access for that tenant

Rationale: MVP requires simple, predictable authorization. Complex role systems add overhead that can be added later if needed.

### VIII. Idempotent Operations
**All state-changing operations that may be retried MUST be idempotent.**

Required for:
- Creating tenant memberships (no duplicate entries)
- Subscribing tenants to applications (idempotent by tenant_id + app_id)
- Onboarding session consumption

Rationale: Distributed systems experience network failures and retries. Idempotency prevents duplicate state and simplifies client error handling.

### IX. Launch via Short-Lived JWT
**Application launch uses Control Plane-issued short-lived Launch JWT, not direct access token passthrough.**

Rules:
- Launch JWT is short-lived (5 minutes)
- Launch JWT contains: `sub`, `tenant_id`, `app_id`, `exp`, `jti`
- Apps validate Launch JWT using Control Plane's public key or shared secret
- Launch endpoint returns 302 redirect with token in query string
- Standard error format for invalid/expired tokens

Rationale: Short-lived tokens limit exposure window. Apps don't need to understand OIDC tokens. Control Plane maintains control over what claims apps receive.

### X. Audit Stubs Only
**Audit logging uses internal interfaces with minimal persistence; no external dispatch in MVP.**

Rules:
- Define internal stub interfaces for audit events
- Optional database table for critical actions
- No external notification service integration
- No real-time audit stream to external systems

Rationale: Full audit infrastructure is a cross-cutting concern best extracted to a Core service. For MVP, stubs enable future expansion without premature optimization.

## Architecture Standards

### Multi-Service Platform Context
The Control Plane is one microservice in a larger platform:
- **Upstream**: OIDC Provider (Keycloak)
- **Downstream**: Application services (PACS, ERP, etc.) receive launch requests via Launch JWT
- **Lateral**: Core services (future: RBAC, audit, notifications)

### Data Flow (New User)
1. User completes pre-login form (app + org_name + tenant_name)
2. Control Plane creates onboarding session → returns onboarding_token
3. User redirected to Keycloak → authenticates
4. Keycloak redirects to callback with auth code
5. Control Plane validates tokens, resolves onboarding session
6. Control Plane auto-provisions: org, tenant, user, membership, trial subscription
7. Control Plane issues Launch JWT → redirects to app

### Data Flow (Returning User)
1. User calls `/v1/auth/login` (no onboarding_token)
2. Redirected to Keycloak → authenticates
3. Callback validates tokens → looks up existing user
4. User can list tenants, request launch for subscribed apps

## Technology Standards

### Language & Framework
- **Python 3.11+** with **FastAPI** (async)
- **Pydantic v2** for data validation and serialization
- **python-jose[cryptography]** for JWT handling
- **httpx** for async HTTP requests

### Data Layer
- **PostgreSQL** with **SQLAlchemy 2.0** (async)
- **Alembic** for database migrations
- All database operations MUST be async
- **asyncpg** driver for PostgreSQL

### Testing
- **pytest** with async support
- Test organization: `tests/unit/`, `tests/integration/`, `tests/contract/`
- Mock Keycloak for integration tests

### API Documentation
- OpenAPI 3.0 generated from FastAPI routes
- Verified with automated tests

### Configuration
- Environment variables only (12-factor app)
- No config files in production
- Secrets via environment (no hardcoded credentials)

## API Standards

### Versioning
- All endpoints under `/v1/` prefix
- Breaking changes require `/v2/` with migration path

### Error Format
Standard error response structure with error codes:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable description",
  "details": { /* optional context */ }
}
```

### Standard Error Codes (MVP)

| Code | HTTP | Description |
|------|------|-------------|
| `ONBOARDING_SESSION_EXPIRED` | 400 | Session TTL exceeded |
| `ONBOARDING_SESSION_CONSUMED` | 400 | Session already used |
| `USER_ORG_CONFLICT` | 409 | User exists in different org |
| `TENANT_NAME_EXISTS` | 409 | Tenant name already in org |
| `NOT_TENANT_MEMBER` | 403 | User not member of tenant |
| `NO_SUBSCRIPTION` | 403 | No subscription to app |
| `TRIAL_EXPIRED` | 403 | Trial period ended |
| `INVALID_TOKEN` | 401 | Invalid/expired token |

### Pagination
List endpoints that may grow MUST support pagination:
- Query params: `limit` (default: 50, max: 1000), `offset` (default: 0)
- Response includes: `total`, `limit`, `offset`, `items`

## Security Standards

### Authentication
- All non-public endpoints require valid bearer token
- Token validation: issuer URL + JWKS endpoint verification
- Reject tokens with: invalid signature, expired, unknown algorithm, wrong audience

### Authorization Flow
1. Extract and validate bearer token
2. Derive user identity (`sub`) from token
3. Look up user's organization association
4. Enforce organization boundary (reject if user not in requested org)
5. Enforce tenant membership (user must be member of tenant)
6. Enforce subscription status (if accessing application)
7. Apply role-based permissions

### Onboarding Security
- OIDC `state` parameter binds to `onboarding_token`
- Onboarding session has 60-minute maximum TTL
- Single-consume prevents replay attacks
- Same `idp_sub` cannot onboard into multiple orgs

### Correlation IDs
- Accept `X-Request-ID` header from client
- Generate UUID if not provided
- Return in response headers
- Include in all log entries

### Security Checklist
- [ ] Never trust client-supplied `org_id` or `tenant_id` for authorization
- [ ] Validate all tokens before processing requests
- [ ] Log all authorization failures
- [ ] Include correlation ID in all logs
- [ ] Use parameterized queries (SQL injection prevention)
- [ ] Sanitize error messages (no internal details in client errors)
- [ ] Bind OIDC state to onboarding token (CSRF protection)
- [ ] Enforce single-consume on onboarding sessions

## MVP Deliverables

The following endpoints/features are in scope for MVP v1.0:

### Pre-Login Onboarding
- `POST /v1/onboarding` - Create onboarding session (app + org_name + tenant_name)

### Authentication
- `GET /v1/auth/login` - Redirect to Keycloak OIDC (optional `onboarding_token`)
- `GET /v1/auth/callback` - OIDC callback handler (provisioning + Launch JWT)
- `GET /v1/auth/me` - Current user info

### Tenant Management
- `POST /v1/tenants` - Create tenant (requires org_admin)
- `GET /v1/tenants/{id}` - Get tenant details
- `GET /v1/tenants` - List tenants (filtered by membership)

### Membership Management
- `POST /v1/tenants/{tenant_id}/members` - Add user to tenant
- `DELETE /v1/tenants/{tenant_id}/members/{user_id}` - Remove user from tenant
- `GET /v1/tenants/{tenant_id}/members` - List tenant members

### Application Catalog
- `GET /v1/applications` - List available applications (read-only catalog)

### Subscriptions
- `POST /v1/subscriptions` - Subscribe tenant to application (creates 14-day trial)
- `GET /v1/tenants/{tenant_id}/subscriptions` - List tenant subscriptions

### Launch Endpoint
- `GET /v1/launch` - Issue Launch JWT and redirect to target application

## Governance

### Amendment Process
1. Propose change with rationale
2. Document impact on existing code/features
3. Provide migration plan if breaking
4. Update version per semantic versioning rules
5. Update dependent templates for consistency

### Versioning
- **MAJOR**: Backward-incompatible changes (principle removal, redefinition)
- **MINOR**: New principle or significant expansion
- **PATCH**: Clarifications, wording fixes, non-semantic changes

### Compliance
- All feature specifications MUST pass constitution checks
- Implementation plans MUST document any violations with justification
- Code reviews MUST verify constitutional compliance

**Version**: 1.1.0 | **Ratified**: 2026-02-09 | **Last Amended**: 2026-02-14
