# Quickstart: OIDC Authentication

**Feature**: 002-oidc-auth
**Date**: 2026-02-11

## Overview

This guide helps developers get started with the OIDC Authentication feature for the Control Plane. It covers setup, local development, testing, and common workflows.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- A Zitadel instance (or compatible OIDC provider)
- Access to configure Zitadel with custom claims

## Environment Setup

### 1. Clone and Install Dependencies

```bash
cd /path/to/control_plane
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/control_plane

# OIDC / Zitadel
OIDC_ISSUER=https://auth.craft-crew.com
OIDC_CLIENT_ID=control-plane-client
OIDC_CLIENT_SECRET=your-client-secret
OIDC_REDIRECT_URI=http://localhost:8000/v1/auth/callback
OIDC_SCOPES=openid profile email

# Application
CONTROL_PLANE_ENV=development
CONTROL_PLANE_HOST=0.0.0.0
CONTROL_PLANE_PORT=8000
```

### 3. Set Up Database

```bash
# Create database
createdb control_plane

# Run migrations
alembic upgrade head
```

### 4. Start the Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 5. Access API Documentation

Open your browser to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Zitadel Configuration

### Setting Up the OIDC Application

1. **Log in to Zitadel Console** at your configured issuer URL

2. **Create a new Project** (or use existing):
   - Navigate to: Projects → New
   - Name: `Control Plane`

3. **Create an Application**:
   - Navigate to: Projects → Control Plane → Applications → New
   - Application Type: `Web`
   - Application Name: `control-plane-web`
   - Redirect URIs:
     - Development: `http://localhost:8000/v1/auth/callback`
     - Production: `https://api.controlplane.example.com/v1/auth/callback`
   - Auth Method: `PKCE` (recommended) or `Authorization Code`

4. **Configure Custom Claims** (for `org_id`):
   - Navigate to: Settings → JWT Settings
   - Add a custom mapper for `org_id` that extracts the organization ID from user data
   - Example: Map from a custom user attribute `organizationId`

5. **Copy Client Credentials**:
   - Note the `Client ID` and `Client Secret` from the application details
   - Add these to your `.env` file

---

## Testing the Authentication Flow

### 1. Manual Browser Test

1. Navigate to: `http://localhost:8000/v1/auth/login`
2. You should be redirected to Zitadel's login page
3. Log in with your Zitadel credentials
4. After successful authentication, you'll be redirected back to `/v1/auth/callback`
5. The response will include your access token and user info

### 2. Using curl

```bash
# Step 1: Initiate login (get authorization URL manually)
curl -v "http://localhost:8000/v1/auth/login"

# Step 2: Complete login in browser with the returned URL

# Step 3: Use the returned access token to call protected endpoints
export TOKEN="your-access-token-from-callback"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/auth/me"
```

### 3. Using Python / httpx

```python
import httpx

async def test_auth_flow():
    async with httpx.AsyncClient() as client:
        # Step 1: Initiate login
        response = await client.get("http://localhost:8000/v1/auth/login")
        auth_url = response.headers.get('location')
        print(f"Visit: {auth_url}")

        # Step 2: Complete login manually in browser, get token

        # Step 3: Use token
        token = "your-access-token"
        response = await client.get(
            "http://localhost:8000/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(response.json())
```

---

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=src/security/oidc --cov-report=html
```

### Integration Tests

```bash
# Run integration tests (requires test database)
pytest tests/integration/ --asyncio-mode=auto

# Run specific test file
pytest tests/integration/test_auth_flow.py -v
```

### Contract Tests

```bash
# Run API contract tests
pytest tests/contract/test_v1_auth.py -v
```

### All Tests

```bash
# Run complete test suite
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing
```

---

## Common Development Workflows

### Adding a New Required Claim

If you need to add a new required claim from the OIDC token:

1. Update `src/security/oidc.py`:
   ```python
   def extract_required_claims(self, payload: dict) -> tuple[str, str, str]:
       # ... existing code ...
       new_claim = payload.get("new_claim")
       if not new_claim:
           raise OIDCValidationError("Token missing required 'new_claim' claim")
       return sub, org_id, new_claim
   ```

2. Update user provisioning in `src/services/auth.py`:
   ```python
   async def get_or_create_user(
       session: AsyncSession,
       idp_sub: str,
       org_id: str,
       email: str,
       name: str,
       new_claim: str,  # Add new parameter
   ) -> User:
       # ... use new_claim in user creation/update
   ```

3. Update tests to include the new claim

### Changing JWKS Cache TTL

To adjust the JWKS cache duration, modify `src/security/oidc.py`:

```python
def __init__(self, settings=None):
    self.settings = settings or get_settings()
    self._jwks_client: PyJWKClient | None = None
    self._jwks_last_update: datetime | None = None
    self._jwks_cache_ttl = timedelta(minutes=10)  # Change from 5 to 10
```

### Adding a New Authentication Endpoint

1. Define the endpoint in `src/api/v1/auth.py`
2. Create Pydantic schemas in `src/schemas/auth.py`
3. Add business logic in `src/services/auth.py`
4. Write tests in `tests/contract/test_v1_auth.py`

---

## Troubleshooting

### "Token missing required 'org_id' claim"

**Cause**: Zitadel is not configured to include the `org_id` claim in tokens.

**Solution**: Configure a custom claim mapper in Zitadel to add the `org_id` claim to JWTs.

### "Failed to fetch signing keys"

**Cause**: JWKS endpoint is unreachable or network issue.

**Solution**:
1. Verify `OIDC_ISSUER` is correct
2. Check network connectivity to `{OIDC_ISSUER}/.well-known/jwks.json`
3. Check if JWKS endpoint requires authentication (unusual)

### "Invalid token: Signature verification failed"

**Cause**: Token signature doesn't match any key in JWKS.

**Solution**:
1. Verify token is from the correct issuer
2. Check if keys have rotated recently
3. Clear JWKS cache by restarting the service

### User Created But No Organization Record Exists

**Cause**: Organization with the `org_id` from the claim doesn't exist in the database.

**Solution**: Create the organization record first (via organization management API or database seed).

### Tests Failing with "Database Not Available"

**Cause**: Test database not configured or migrations not run.

**Solution**:
```bash
# Create test database
createdb control_plane_test

# Set DATABASE_URL for tests
export DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/control_plane_test

# Run migrations
alembic upgrade head
```

---

## API Reference Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/v1/auth/login` | GET | No | Initiate OIDC login flow |
| `/v1/auth/callback` | GET | No | Handle OIDC callback |
| `/v1/auth/me` | GET | Yes | Get current user info |

---

## Next Steps

1. Review the full API contract in `contracts/auth.yaml`
2. Read the data model documentation in `data-model.md`
3. Explore the implementation in `src/security/oidc.py` and `src/api/v1/auth.py`
4. Check out the tests in `tests/` for usage examples

---

## Additional Resources

- [OpenID Connect Core 1.0 Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [Zitadel Documentation](https://zitadel.com/docs)
- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
