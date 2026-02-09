<!--
SYNC IMPACT REPORT
==================
Version change: N/A -> 1.0.0
Modified principles: N/A (initial constitution)
Added sections:
  - Core Principles (8 principles)
  - Architecture Standards
  - Technology Standards
  - API Standards
  - Security Standards
  - MVP Deliverables
Removed sections: N/A
Templates requiring updates:
  - ✅ spec-template.md - No updates needed (aligned with generic structure)
  - ✅ plan-template.md - No updates needed (Constitution Check section exists)
  - ✅ tasks-template.md - No updates needed (generic task categorization)
Follow-up TODOs: None
-->

# Control Plane Constitution

## Core Principles

### I. API-First Architecture
**All functionality is exposed via REST API; no web UI in this service.**

Rationale: As a microservice in a larger SaaS platform, the Control Plane serves as the backend for other services and potential frontends. Keeping it API-only ensures clean separation of concerns and enables multiple client types (web, mobile, other services) to interact without UI coupling.

### II. Strict Tenancy Boundaries
**Organization and tenant boundaries MUST be enforced at all layers; cross-organization access is FORBIDDEN.**

Rules:
- An Organization contains many Tenants (branches)
- A User belongs to exactly one Organization
- A User may have membership in multiple Tenants under the same Organization
- Cross-organization access MUST be rejected at the authorization layer
- Client-supplied `org_id` MUST never be trusted; derive from authenticated user mapping

Rationale: Data isolation between organizations is critical for multi-tenant SaaS security. Any breach of tenancy boundaries is a critical security vulnerability.

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
**All authentication uses OpenID Connect with Zitadel (auth.craft-crew.com issuer); no password storage.**

Rules:
- Service acts as OIDC client using authorization code flow
- Tokens validated via issuer + JWKS endpoint
- Required claims: `sub` (user ID), `tenant_id` (assumed available from Zitadel)
- Reject unsigned tokens or unknown algorithms
- Token validation MUST happen before any authorization checks

Rationale: Centralized auth with Zitadel provides consistent identity across the platform, eliminates password management risk, and enables SSO.

### V. Coarse-Grained Authorization
**Authorization uses three predefined roles; custom roles are NOT supported in MVP.**

Roles:
- `org_admin`: Can manage all tenants within their organization
- `tenant_admin`: Can manage a specific tenant only
- `tenant_member`: Read/launch access for that tenant

Rationale: MVP requires simple, predictable authorization. Complex role systems add overhead that can be added later if needed.

### VI. Idempotent Operations
**All state-changing operations that may be retried MUST be idempotent.**

Required for:
- Creating tenant memberships (no duplicate entries)
- Subscribing tenants to applications (idempotent by tenant_id + app_id)

Rationale: Distributed systems experience network failures and retries. Idempotency prevents duplicate state and simplifies client error handling.

### VII. No External Billing Integration
**Subscription status is managed internally; manual activation only.**

Rules:
- No Stripe or payment processing in MVP
- Subscription status stored as database field
- Admin API endpoints exist to activate/deactivate subscriptions manually

Rationale: Billing integration adds significant complexity. For MVP, manual subscription management is sufficient.

### VIII. Audit Stubs Only
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
- **Upstream**: OIDC Provider (Zitadel)
- **Downstream**: Application services (PACS, ERP, etc.) receive launch requests
- **Lateral**: Core services (future: RBAC, audit, notifications)

### Data Flow
1. User authenticates via OIDC → receives bearer token
2. Client includes bearer token on API requests
3. Control Plane validates token → extracts `sub` and `tenant_id`
4. Control Plane checks organization membership and tenant access
5. For launch requests: validates subscription → returns redirect URL to target application

## Technology Standards

### Language & Framework
- **Python 3.11+** with **FastAPI** (async)
- **Pydantic v2** for data validation and serialization

### Data Layer
- **PostgreSQL** (preferred) with **SQLAlchemy 2.0** (async)
- **Alembic** for database migrations
- All database operations MUST be async

### Testing
- **pytest** with async support
- Test organization: `tests/unit/`, `tests/integration/`, `tests/contract/`

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
Standard error response structure:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable description",
  "details": { /* optional context */ }
}
```

RFC7807-like semantics recommended but consistency is mandatory.

### Pagination
List endpoints that may grow MUST support pagination:
- Query params: `limit` (default: 50, max: 1000), `offset` (default: 0)
- Response includes: `total`, `limit`, `offset`, `items`

## Security Standards

### Authentication
- All non-auth endpoints require valid bearer token
- Token validation: issuer URL + JWKS endpoint verification
- Reject tokens with: invalid signature, expired, unknown algorithm

### Authorization Flow
1. Extract and validate bearer token
2. Derive user identity (`sub`) and organization mapping
3. Enforce organization boundary (reject if user not in requested org)
4. Enforce tenant membership (user must be member of tenant)
5. Enforce subscription status (if accessing application)
6. Apply role-based permissions

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

## MVP Deliverables

The following endpoints/features are in scope for MVP v1.0:

### Authentication
- `GET /v1/auth/login` - Redirect to Zitadel OIDC authorization
- `GET /v1/auth/callback` - OIDC callback handler

### Organization Management
- `POST /v1/organizations` - Create organization
- `GET /v1/organizations/{id}` - Get organization details
- `GET /v1/organizations` - List organizations (paginated)

### Tenant Management
- `POST /v1/tenants` - Create tenant (requires org membership)
- `GET /v1/tenants/{id}` - Get tenant details
- `GET /v1/tenants` - List tenants (paginated, filtered by org/membership)

### Membership Management
- `POST /v1/tenants/{tenant_id}/members` - Add user to tenant
- `DELETE /v1/tenants/{tenant_id}/members/{user_id}` - Remove user from tenant
- `GET /v1/tenants/{tenant_id}/members` - List tenant members

### Application Catalog
- `GET /v1/applications` - List available applications (read-only catalog)

### Subscriptions
- `POST /v1/tenants/{tenant_id}/subscriptions` - Subscribe tenant to application
- `GET /v1/tenants/{tenant_id}/subscriptions` - List tenant subscriptions
- `PATCH /v1/tenants/{tenant_id}/subscriptions/{sub_id}` - Update subscription status (admin only)

### Launch Endpoint
- `POST /v1/launch` - Returns redirect URL to target application with tenant context

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

**Version**: 1.0.0 | **Ratified**: 2026-02-09 | **Last Amended**: 2026-02-09
