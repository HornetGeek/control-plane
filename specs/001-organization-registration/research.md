# Research: Organization Registration

**Feature**: 001-organization-registration
**Date**: 2026-02-17

## Technical Decisions

### 1. Slug Generation Algorithm

**Decision**: Short random suffix (4 alphanumeric characters)

**Rationale**:
- Predictable and easy to communicate
- Sufficient entropy for uniqueness (36^4 = 1.6M combinations per name prefix)
- Professional appearance compared to UUIDs
- Simple to implement with `secrets` module

**Alternatives Considered**:
| Approach | Rejected Because |
|----------|------------------|
| Sequential suffix (acme-corp-2) | Predictable, looks unprofessional |
| Full UUID suffix | Too long, hard to communicate |
| Timestamp-based | Collisions possible with concurrent registrations |

**Implementation**:
```python
import secrets
import string

def generate_unique_slug(base_name: str, existing_slugs: set[str]) -> str:
    slug_base = slugify(base_name)  # lowercase, hyphens
    if slug_base not in existing_slugs:
        return slug_base
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"{slug_base}-{suffix}"
```

### 2. Rate Limiting Strategy

**Decision**: Redis-based sliding window with IP + email combination

**Rationale**:
- Redis already in infrastructure for auth caching
- Sliding window provides smoother rate limiting than fixed window
- Track both IP (primary) and email (secondary) to prevent abuse from multiple IPs
- Configurable thresholds via environment variables

**Rate Limits**:
| Scope | Limit | Window |
|-------|-------|--------|
| Per IP | 10 attempts | 1 hour |
| Per email | 3 attempts | 1 hour |

**Backoff Ladder**: 1min → 5min → 15min → 1hr (configurable)

**Implementation Pattern**:
```python
# Redis key: rate_limit:registration:{ip_address}
# Value: count of attempts
# TTL: window duration

async def check_rate_limit(ip: str, email: str) -> tuple[bool, int]:
    # Check IP limit
    ip_key = f"rate_limit:registration:ip:{ip}"
    ip_count = await redis.incr(ip_key)
    if ip_count == 1:
        await redis.expire(ip_key, 3600)
    if ip_count > 10:
        ttl = await redis.ttl(ip_key)
        return False, ttl

    # Check email limit
    email_key = f"rate_limit:registration:email:{email}"
    email_count = await redis.incr(email_key)
    if email_count == 1:
        await redis.expire(email_key, 3600)
    if email_count > 3:
        ttl = await redis.ttl(email_key)
        return False, ttl

    return True, 0
```

### 3. Idempotency Key Handling

**Decision**: Store idempotency key with registration record, 24-hour retention

**Rationale**:
- Prevents duplicate organizations on network retries
- 24 hours sufficient for client retry scenarios
- Simple database-based approach (no additional infrastructure)

**Implementation**:
```python
# Check for existing registration with same idempotency key
existing = await session.execute(
    select(Registration).where(
        Registration.idempotency_key == idempotency_key,
        Registration.created_at > datetime.utcnow() - timedelta(hours=24)
    )
)
if existing:
    return existing  # Return original result
```

### 4. Personal Email Domain Detection

**Decision**: Client-side warning only (MVP), configurable blocklist

**Rationale**:
- Soft warning improves UX without blocking legitimate users
- Domain list configurable via environment variable
- Future: enterprise deployments can enable blocking

**Default Blocklist**:
```
gmail.com, yahoo.com, hotmail.com, outlook.com, aol.com,
icloud.com, mail.com, protonmail.com, zoho.com, yandex.com
```

### 5. Pending Registration Cleanup

**Decision**: Background task with 7-day retention, preserve audit trail

**Rationale**:
- 7 days allows reasonable retry window
- Cleanup removes PII but preserves audit evidence
- Async background task avoids blocking registration flow

**Implementation Pattern**:
```python
# Scheduled task (e.g., hourly)
async def cleanup_expired_registrations():
    cutoff = datetime.utcnow() - timedelta(days=7)
    expired = await session.execute(
        select(Registration).where(
            Registration.status == "pending_invite",
            Registration.created_at < cutoff
        )
    )
    for reg in expired:
        # Preserve audit log, redact PII
        reg.admin_email = f"[REDACTED-{reg.id}]"
        reg.admin_phone = None
        reg.status = "expired"
    await session.commit()
```

### 6. IdP Invite Integration (MVP Stub)

**Decision**: Interface-based adapter with stub implementation for MVP

**Rationale**:
- Interface allows easy swap to real IdP integration
- Stub logs invite attempts for testing/verification
- Returns configurable success/failure for testing scenarios

**Interface**:
```python
class IdPAdapter(Protocol):
    async def send_invite(
        self,
        email: str,
        first_name: str,
        last_name: str,
        org_slug: str,
        correlation_id: str,
    ) -> InviteResult:
        ...

class StubIdPAdapter:
    async def send_invite(...) -> InviteResult:
        logger.info(f"STUB: Would send IdP invite to {email} for org {org_slug}")
        return InviteResult(success=True, invite_id=f"stub-{uuid4()}")
```

### 7. Audit Event Structure

**Decision**: Structured JSON events with correlation ID chain

**Rationale**:
- Consistent with existing logging patterns
- Correlation IDs enable request tracing
- Privacy-safe handling of sensitive fields

**Event Types**:
- `registration.initiated` - Form submitted
- `registration.submitted` - Validation passed, creating org
- `invite.sent` - IdP invite successful
- `invite.failed` - IdP invite failed
- `registration.rate_limited` - Rate limit hit

**Event Structure**:
```json
{
  "event_type": "registration.submitted",
  "timestamp": "2026-02-17T10:30:00Z",
  "correlation_id": "uuid",
  "request_id": "uuid",
  "ip_address": "192.168.1.0",  // Masked /24
  "email_domain": "example.com",  // Domain only, not full email
  "organization_name": "Acme Corp",
  "country_code": "US"
}
```

### 8. Trial Plan Assignment

**Decision**: Create trial subscription record at org creation, activate at org activation

**Rationale**:
- Decouples registration from billing
- Trial clock starts at activation (US-CP-002), not registration
- Consistent with constitution Principle X

**Implementation**:
```python
# At registration
org = Organization(
    name=name,
    slug=slug,
    status="pending_invite",
    trial_plan="trial",
    trial_assigned_at=datetime.utcnow(),
    # trial_starts_at = None (set at activation)
    # trial_ends_at = None (set at activation)
)

# At activation (US-CP-002)
org.status = "active"
org.trial_starts_at = datetime.utcnow()
org.trial_ends_at = datetime.utcnow() + timedelta(days=14)
```

## Integration Patterns

### Existing Code Reuse

| Component | Reuse | Notes |
|-----------|-------|-------|
| `src/db/base.py` | SoftDeleteMixin, TimestampMixin | Existing |
| `src/db/session.py` | get_session | Existing |
| `src/cache/redis.py` | Redis client | Extend for rate limiting |
| `src/core/logging.py` | Structured logging | Existing |
| `src/schemas/` | Pydantic v2 patterns | Follow existing patterns |

### Database Migration Required

Extend `organizations` table:
- Add `slug` column (unique, indexed)
- Add `trial_plan` column
- Add `trial_assigned_at` column
- Add `trial_starts_at` column (nullable)
- Add `trial_ends_at` column (nullable)
- Modify `status` enum to include `pending_invite`

Create `registrations` table:
- New table for tracking registration process
- Links to organization
- Stores admin details and invite status

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| IdP unavailable | Graceful degradation, retry mechanism |
| Rate limit false positives | Configurable thresholds, monitoring alerts |
| Slug collision | Retry with new suffix (max 3 attempts) |
| Concurrent duplicate email | Database unique constraint, first-write-wins |
| Abuse from distributed IPs | Email-based secondary rate limiting |
