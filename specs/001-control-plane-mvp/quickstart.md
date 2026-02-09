# Quickstart: Control Plane MVP

**Feature**: Control Plane MVP
**Date**: 2026-02-09

## Overview

This guide provides step-by-step instructions for setting up a local development environment for the Control Plane MVP.

---

## Prerequisites

### Required Software

- **Python 3.11+** - Download from [python.org](https://www.python.org/)
- **PostgreSQL 14+** - Download from [postgresql.org](https://www.postgresql.org/)
- **Git** - Download from [git-scm.com](https://git-scm.com/)
- **Docker** (optional) - For containerized Zitadel

### External Services

- **Zitadel Instance** - OIDC provider at `https://auth.craft-crew.com` (or local)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd control_plane
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

### 4. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Application
CONTROL_PLANE_ENV=development
CONTROL_PLANE_HOST=0.0.0.0
CONTROL_PLANE_PORT=8000
CONTROL_PLANE_LOG_LEVEL=debug

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/control_plane

# OIDC / Zitadel
OIDC_ISSUER=https://auth.craft-crew.com
OIDC_CLIENT_ID=control-plane-client
OIDC_CLIENT_SECRET=your-client-secret
OIDC_REDIRECT_URI=http://localhost:8000/v1/auth/callback
OIDC_SCOPES=openid profile email

# Application Catalog
APPLICATION__PACS__NAME="PACS"
APPLICATION__PACS__URL="https://pacs.example.com/launch"
APPLICATION__PACS__STATUS="active"
APPLICATION__ERP__NAME="ERP"
APPLICATION__ERP__URL="https://erp.example.com/launch"
APPLICATION__ERP__STATUS="active"
```

### 5. Start PostgreSQL

**Using Docker** (recommended):

```bash
docker run --name control-plane-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=control_plane \
  -p 5432:5432 \
  -d postgres:14
```

**Or use local installation**:

```bash
# Start PostgreSQL service
sudo service postgresql start

# Create database
createdb control_plane
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Seed Application Catalog

```bash
python -m src.db.seed
```

### 8. Start Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

---

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Contract tests only
pytest tests/contract/
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be in `htmlcov/index.html`.

### Run Specific Test

```bash
pytest tests/integration/test_auth_flow.py::test_login_redirect
```

---

## Local Zitadel Setup (Optional)

If you need a local Zitadel instance for development:

```bash
docker run -d --name zitadel \
  -p 8080:8080 \
  -e ZITADEL_DATABASE_HOSTPORT="zitadel-db:5432" \
  -e ZITADEL_EXTERNALDOMAIN="localhost:8080" \
  -e ZITADEL_EXTERNALPORT="8080" \
  -e ZITADEL_EXTERNALSECURE="false" \
  ghcr.io/zitadel/zitadel:latest
```

Update your `.env`:

```bash
OIDC_ISSUER=http://localhost:8080
OIDC_REDIRECT_URI=http://localhost:8000/v1/auth/callback
```

---

## API Usage Examples

### 1. Login via OIDC

```bash
# Initiate login (opens browser or returns redirect URL)
curl -X GET "http://localhost:8000/v1/auth/login"
```

### 2. Create Tenant (requires auth)

```bash
curl -X POST "http://localhost:8000/v1/tenants" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Branch Office A"}'
```

### 3. Add User to Tenant

```bash
curl -X POST "http://localhost:8000/v1/tenants/TENANT_ID/members" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID", "role": "tenant_member"}'
```

### 4. Subscribe to Application

```bash
curl -X POST "http://localhost:8000/v1/tenants/TENANT_ID/subscriptions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"app_key": "pacs"}'
```

### 5. Launch Application

```bash
curl -X POST "http://localhost:8000/v1/launch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "TENANT_ID", "app_key": "pacs"}'
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit files in `src/` directory.

### 3. Run Tests

```bash
pytest
```

### 4. Format Code

```bash
black src/
ruff check src/
```

### 5. Commit Changes

```bash
git add .
git commit -m "Description of changes"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

---

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Ensure PostgreSQL is running:
```bash
docker ps | grep control-plane-db
# or
sudo service postgresql status
```

### OIDC Token Validation Fails

```
OIDC validation error: unable to verify token
```

**Solution**: Verify Zitadel is accessible and credentials are correct:
```bash
curl $OIDC_ISSUER/.well-known/openid-configuration
```

### Import Errors

```
ModuleNotFoundError: No module named 'src'
```

**Solution**: Ensure the package is installed in editable mode:
```bash
pip install -e .
```

### Migration Fails

```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution**: Reset and re-run migrations:
```bash
alembic downgrade base
alembic upgrade head
```

---

## Useful Commands

### Database

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Development Server

```bash
# Start with auto-reload
uvicorn src.main:app --reload

# Start with specific host/port
uvicorn src.main:app --host 0.0.0.0 --port 9000

# Start with debug logging
uvicorn src.main:app --log-level debug
```

### Docker

```bash
# Start database
docker start control-plane-db

# Stop database
docker stop control-plane-db

# View logs
docker logs control-plane-db

# Remove database
docker rm -f control-plane-db
```

---

## Project Structure Reference

```
src/
├── main.py              # FastAPI application entry
├── config.py            # Configuration
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── api/                 # API routes
├── db/                  # Database utilities
└── security/            # Auth & authorization

tests/
├── conftest.py          # Pytest fixtures
├── unit/                # Unit tests
├── integration/         # Integration tests
└── contract/            # API contract tests
```

---

## Next Steps

1. Review the [API documentation](http://localhost:8000/docs)
2. Read the [feature specification](./spec.md)
3. Check the [data model documentation](./data-model.md)
4. Review [API contracts](./contracts/openapi.yaml)

---

## Support

For issues or questions:
- Check existing [GitHub Issues](../../issues)
- Create a new issue with details
- Contact the Control Plane team
