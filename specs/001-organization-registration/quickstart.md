# Quickstart: Organization Registration

**Feature**: 001-organization-registration
**Date**: 2026-02-17

## Overview

This guide walks through implementing and testing the Organization Registration feature.

## Prerequisites

- Python 3.11+
- PostgreSQL database (running via Docker Compose)
- Redis (running via Docker Compose)
- Keycloak (optional; required only for real IdP adapter smoke tests)

## Quick Test

### 1. Start Services

```bash
cd /media/hornet/84ACF2FAACF2E5981/control_plan
docker-compose up -d
```

### 2. Run Database Migrations

```bash
docker-compose --profile migrate up migrate
```

### 3. Test Registration Endpoint

```bash
# Basic registration
curl -X POST "http://localhost:8000/v1/public/registration" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-123" \
  -d '{
    "organization_name": "Test Company",
    "admin_email": "admin@testcompany.com",
    "admin_first_name": "John",
    "admin_last_name": "Doe",
    "country_code": "US",
    "accept_terms": true
  }'
```

Note: If the environment is configured to use a stub IdP adapter, no email will be sent. Verify `invite_status` in the response and check API logs.

### 4. Expected Response (201 Created)

```json
{
  "registration_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "660e8400-e29b-41d4-a716-446655440001",
  "organization_slug": "test-company",
  "status": "completed",
  "invite_status": "sent",
  "message": "Check your email to complete setup"
}
```

## Test Scenarios

### Scenario 1: Duplicate Email

```bash
# First registration
curl -X POST "http://localhost:8000/v1/public/registration" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Company A", "admin_email": "same@example.com", ...}'

# Second registration with same email (expect 409)
curl -X POST "http://localhost:8000/v1/public/registration" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Company B", "admin_email": "same@example.com", ...}'
```

Expected response (409 Conflict):
```json
{
  "error_code": "EMAIL_ALREADY_REGISTERED",
  "message": "This email is already associated with an account",
  "details": {"sign_in_url": "/login"}
}
```

### Scenario 2: Duplicate Organization Name

```bash
# Both succeed with unique slugs
curl -X POST ... -d '{"organization_name": "Acme Corp", ...}'
# Returns slug: "acme-corp"

curl -X POST ... -d '{"organization_name": "Acme Corp", ...}'
# Returns slug: "acme-corp-7x9k"
```

### Scenario 3: Rate Limiting

```bash
# Run 11 times rapidly from same IP
for i in {1..11}; do
  curl -X POST "http://localhost:8000/v1/public/registration" \
    -H "Content-Type: application/json" \
    -d "{\"organization_name\": \"Test $i\", \"admin_email\": \"admin$i@test.com\", ...}"
done

# 11th request returns 429
```

Expected response (429 Too Many Requests):
```json
{
  "error_code": "RATE_LIMITED",
  "message": "Too many registration attempts. Please try again later.",
  "details": {"retry_after": 3600}
}
```

### Scenario 4: Idempotency

```bash
# First request
curl -X POST "http://localhost:8000/v1/public/registration" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{"organization_name": "Idempotent Test", ...}'

# Retry with same key - returns same result without creating duplicate
curl -X POST "http://localhost:8000/v1/public/registration" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{"organization_name": "Idempotent Test", ...}'
```

### Scenario 5: Personal Email Warning

```bash
# Request with personal email
curl -X POST "http://localhost:8000/v1/public/registration" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test", "admin_email": "user@gmail.com", ...}'

# Still succeeds (soft warning in response)
```

## Running Tests

```bash
# Unit tests
pytest tests/unit/services/test_registration_service.py -v

# API tests
pytest tests/unit/api/test_registration.py -v

# Integration tests (requires running services)
pytest tests/integration/test_registration_flow.py -v

# All tests
pytest tests/ -v -k registration
```

## Configuration

Environment variables for registration behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `REGISTRATION_RATE_LIMIT_PER_HOUR` | 10 | Max registrations per IP per hour |
| `REGISTRATION_EMAIL_RATE_LIMIT` | 3 | Max registrations per email per hour |
| `REGISTRATION_PENDING_RETENTION_DAYS` | 7 | Days before cleanup |
| `TRIAL_DURATION_DAYS` | 14 | Trial period length |
| `PERSONAL_EMAIL_DOMAINS` | gmail.com,yahoo.com,... | Comma-separated list |

## Troubleshooting

### Issue: 500 Internal Server Error

Check logs:
```bash
docker-compose logs api
```

Common causes:
- Database connection failed
- Redis connection failed
- Missing required environment variables

### Issue: Organization created but invite failed

Check `invite_status` in response:
- `failed`: IdP adapter returned error
- Use `/registration/{id}/resend-invite` to retry

### Issue: Rate limit triggered unexpectedly

Check Redis:
```bash
docker-compose exec redis redis-cli keys "rate_limit:*"
```

Clear rate limits (development only):
```bash
docker-compose exec redis redis-cli FLUSHDB
```

## Next Steps

After registration succeeds:
1. If using a real IdP adapter, user receives email from the IdP (e.g., Keycloak). If using a stub adapter, verify the invite attempt via logs.
2. User clicks link to complete setup
3. Organization status changes to `active` (US-CP-002)
4. Trial clock starts
5. User can access Control Plane dashboard
