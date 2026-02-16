<!--
SYNC IMPACT REPORT
==================
Version change: 1.1.0 -> 2.0.0

Modified principles:
  - I. API-First Architecture → I. Mission & Scope (now includes admin UI)
  - II. Strict Tenancy Boundaries → Absorbed into 3-plane architecture
  - III. Subscription-Based Access Control → Implicit in Mission & Scope
  - IV. OIDC-First Authentication → III. Trust & Security Model (local validation + delegation)
  - VII. Coarse-Grained Authorization → IV. Roles & Access Semantics (delegated to Core)
  - VIII. Idempotent Operations → VII. CP↔Core Synchronization (membership creation)
  - X. Audit Stubs Only → Removed (deferred to Core service)

Removed sections:
  - V. Pre-Login Onboarding (no longer in scope for CP)
  - IX. Launch via Short-Lived JWT (replaced with redirect flow)

Added sections:
  - II. Architectural Position (3-plane model: CP/Core/Data Plane)
  - V. Caching Strategy (Redis for authorization decisions)
  - VI. Data Lifecycle Rules (soft delete + status)
  - VIII. App Launch & SSO Behavior (redirect, no token issuance)
  - IX. API Governance (public vs protected, error contract)
  - X. Subscription Trial Period (14-day trials for MVP)

Templates requiring updates:
  - ✅ spec-template.md - No structural changes needed
  - ✅ plan-template.md - Constitution Check section remains valid
  - ✅ tasks-template.md - No structural changes needed

Follow-up TODOs:
  - Regenerate tasks.md for existing features to align with new architecture
  - Update feature specs if they reference removed principles (Pre-Login Onboarding, Launch JWT)
  - Review existing code for Launch JWT implementation that needs removal
  - Implement mock Core client for authorization decisions (MVP)

MVP Clarification (2026-02-15):
  - Core service is out of scope for this project
  - Authorization delegation uses a mock Core client for MVP
  - Mock will be replaced with actual Core service calls in future phase
  - 14-day trial subscriptions are IN SCOPE for MVP (added as Principle X)
-->

# Control Plane Constitution

## Core Principles

### I. Mission & Scope
**Control Plane (CP) is the public-facing Generic SaaS management service.**

CP provides:
- Application catalog management (PACS/ERP and future apps)
- Organization and tenant (branch) registry
- Tenant subscription registry (tenant ↔ app)
- Administrative views for SaaS operations (dashboard, tenants, organizations, settings)

CP explicitly does **not** provide:
- Business-domain workflows (these belong to Data Plane apps)
- Role/permission data ownership (belongs to Core)
- Session issuance or launch JWT issuance

Rationale: Clear boundary definition prevents scope creep and ensures each service in the platform has focused responsibilities. CP manages the SaaS registry; Core manages identity and access; Data Plane apps manage domain workflows.

### II. Architectural Position (3-Plane Model)
**The platform consists of three distinct planes with clear ownership boundaries.**

- **Control Plane (this service):** SaaS registry + management APIs (Postgres)
- **Core Service:** identity/membership/RBAC + authorization decisions
- **Data Plane:** application microservices (PACS/ERP) with tenant-aware domain data

CP is the source of truth for:
- applications, organizations, tenants, subscriptions

Core is the source of truth for:
- users (IdP-linked), memberships, roles/permissions, authorization decisions

Rationale: This separation enables independent scaling, clear data ownership, and simplifies compliance. Each plane can evolve independently while maintaining well-defined integration contracts.

### III. Trust & Security Model (Public Service)
**CP is public internet accessible with strict authentication and delegated authorization.**

#### 3.1 Local OIDC Token Validation (CP responsibility)
CP must validate each incoming bearer access token locally:
- signature verification using Keycloak JWKS
- issuer match
- audience match (`aud == client_id`)
- expiration check
- clock skew tolerance (small, configurable)

CP does not rely on Core for token validity.

#### 3.2 Authorization Delegation (Core responsibility)
CP must not encode authorization rules internally. Instead, CP delegates all authorization checks to Core:
- CP provides subject context (sub, org/tenant scope, requested action)
- Core returns allow/deny + scoped entitlements

**MVP Note**: Core service is out of scope for this project. CP uses a **mock Core client** for authorization decisions during MVP. The mock:
- Returns predictable allow/deny responses based on configured test scenarios
- Simulates role-based access (super_admin, org_admin, tenant_admin)
- Will be replaced with actual Core service integration in a future phase

If Core (or mock) is unreachable:
- CP fails closed for protected endpoints (deny with service error)
- Only health endpoints may remain available

Rationale: Centralizing authorization in Core ensures consistent policy enforcement across all platform services. Local token validation prevents unnecessary network calls for every request while maintaining security.

### IV. Roles & Access Semantics (enforced by Core)
**CP supports predefined roles conceptually, enforced via Core decisions.**

- **super_admin** (global)
  - Can manage applications, organizations, view global dashboards, list all users (via Core)
  - Created manually one time (bootstrap)
- **org_admin** (org scoped)
  - Can view/manage all tenants and subscriptions under their organization
- **tenant_admin** (tenant scoped)
  - Can view/manage only their tenant and its subscriptions
- **tenant_member**
  - No access to CP

CP assumes Core will return authorization decisions consistent with these semantics.

Rationale: MVP requires simple, predictable authorization. Complex role systems add overhead that can be added later if needed. Core enforces these roles so CP remains policy-agnostic.

### V. Caching Strategy (Redis) — Authorization Decisions Only
**CP uses Redis to cache authorization decisions, not token validation.**

#### 5.1 Cache Inputs
- `token_fingerprint` = SHA-256(full bearer token)
- `request_scope` = tuple(action, resource_type, org_id?, tenant_id?)

#### 5.2 Cache Value
Cache stores Core's result:
- allow/deny
- resolved subject identifiers (sub, org_id, tenant_ids scope)
- effective role scope (super/org/tenant)
- expiry timestamp

#### 5.3 TTL Rules
- TTL must be short and safe (recommend: 60–300 seconds)
- TTL must never exceed token expiry
- Deny decisions may be cached briefly (e.g., 30–60 seconds) to reduce repeated load

#### 5.4 Revocation & Consistency
Membership/role changes may take up to cache TTL to reflect. This is acceptable for MVP; later phases may add explicit cache invalidation.

Rationale: Caching authorization decisions reduces load on Core and improves response times. Short TTLs balance performance with consistency. Token validation must not be cached for security reasons. The caching infrastructure is implemented in MVP (even with mock Core) to ensure architecture is ready for real Core integration.

### VI. Data Lifecycle Rules (Soft Delete + Status)
**All CP-owned entities must support soft deletion and status tracking.**

Required fields:
- `status` field (e.g., active/disabled)
- `deleted_at` timestamp (soft delete)

Rules:
- Soft-deleted records are not returned by default list endpoints
- Deleting an org/tenant must be restricted by Core authorization
- Deleting an org/tenant must not silently orphan critical dependencies

Rationale: Soft deletion enables recovery from accidental deletions and supports audit requirements. Status tracking enables temporary suspension without data loss.

### VII. CP↔Core Synchronization Responsibilities
**When CP creates or updates registry entities that affect access, CP must synchronize corresponding access artifacts in Core.**

**MVP Note**: Since Core is out of scope for MVP, synchronization calls are stubbed. The stub logs the intended sync operation without making actual calls. This will be replaced with real Core integration in a future phase.

#### 7.1 Membership Creation (MVP rule)
After CP commits DB changes:
- CP calls Core to create membership/role bindings
- This call must be idempotent (safe to retry)
- If Core fails after CP commit:
  - CP returns a controlled error and records a "sync_pending" state for later retry
  - MVP can retry inline + log

This ensures CP (registry) and Core (access) remain aligned.

Rationale: CP owns the registry data, but Core owns the access enforcement. Synchronization ensures consistency. Idempotency enables safe retries in distributed systems.

### VIII. App Launch & SSO Behavior
**CP must not issue any launch tokens.**

When a user selects "Open PACS/ERP":
- CP redirects to the Data Plane application base URL
- The application performs its own OIDC login against Keycloak
- Keycloak redirects back to the application domain
- Application enforces tenant isolation and authorization using Core

Rationale: Eliminating launch tokens simplifies the architecture and removes CP as a token issuer. Each application manages its own authentication, reducing CP's security surface.

### IX. API Governance
**All APIs must follow consistent governance rules.**

#### 9.1 Public vs Protected APIs
- Public endpoints are explicitly versioned and namespaced (e.g., `/v1/public/...`)
- All other endpoints are protected and require valid bearer token + Core authorization

#### 9.2 Error Contract
All endpoints must return a consistent error envelope:

```json
{
  "error_code": "STRING",
  "message": "STRING",
  "details": {}
}
```

Rationale: Consistent API governance improves developer experience and enables automated tooling. Clear error contracts simplify debugging and client implementation.

### X. Subscription Trial Period (MVP)
**Subscriptions default to 14-day trial status; no billing in MVP.**

Rules:
- New subscriptions default to `status=trial`
- `trial_ends_at` is set to `now + 14 days` on creation
- Expired trials cannot launch apps
- No payment processing (deferred to future phase)
- Idempotent: one trial per `(tenant_id, app_id)`

Rationale: MVP focuses on user acquisition and platform validation. Billing complexity is deferred. Trial duration is sufficient for evaluation without indefinite free access.

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

### Caching
- **Redis** for authorization decision caching
- Cache keys MUST include token fingerprint + request scope
- Cache invalidation via TTL only (MVP)

### Testing
- **pytest** with async support
- Test organization: `tests/unit/`, `tests/integration/`, `tests/contract/`
- Mock Keycloak for integration tests
- **Mock Core client** used for authorization in all tests (real Core out of scope)

### API Documentation
- OpenAPI 3.0 generated from FastAPI routes
- Verified with automated tests

### Configuration
- Environment variables only (12-factor app)
- No config files in production
- Secrets via environment (no hardcoded credentials)

## Security Standards

### Authentication Flow
1. Extract and validate bearer token locally (JWKS)
2. Derive user identity (`sub`) from token
3. Proceed to authorization delegation

### Authorization Flow
1. Build request context (action, resource, org_id, tenant_id)
2. Generate token fingerprint
3. Check Redis cache for authorization decision
4. If cache miss: call Core with subject context
5. Cache Core's decision per TTL rules
6. Enforce allow/deny

### Correlation IDs
- Accept `X-Request-ID` header from client
- Generate UUID if not provided
- Return in response headers
- Include in all log entries

### Security Checklist
- [ ] Validate all tokens locally before processing requests
- [ ] Delegate all authorization checks to Core (mock for MVP, real Core in future)
- [ ] Fail closed when Core/mock is unreachable
- [ ] Log all authorization failures
- [ ] Include correlation ID in all logs
- [ ] Use parameterized queries (SQL injection prevention)
- [ ] Sanitize error messages (no internal details in client errors)
- [ ] Never issue launch tokens or session tokens

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

**Version**: 2.0.0 | **Ratified**: 2026-02-09 | **Last Amended**: 2026-02-15
