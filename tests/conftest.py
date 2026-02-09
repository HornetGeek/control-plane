"""Test fixtures and configuration for pytest."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, String, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Custom UUID type for SQLite compatibility
class UUIDv6(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type in production, String(36) for SQLite in tests.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, UUID):
            return value
        return UUID(value)


# Set test environment variables BEFORE importing any src modules
os.environ.update({
    "CONTROL_PLANE_ENV": "test",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "OIDC_ISSUER": "https://test.zitadel.example.com",
    "OIDC_CLIENT_ID": "test-client-id",
    "OIDC_CLIENT_SECRET": "test-client-secret",
    "OIDC_REDIRECT_URI": "http://localhost:8000/v1/auth/callback",
    "OIDC_SCOPES": "openid profile email",
})

from src.config import get_settings
from src.main import app
from src.models.base import Base
# Import all models to register them with Base
from src.models.organization import Organization
from src.models.tenant import Tenant
from src.models.user import User, UserStatus
from src.models.membership import Membership
from src.models.application import Application
from src.models.subscription import Subscription

# Set app state for testing
app.state.settings = get_settings()


# Test settings - override with test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def get_test_settings() -> dict[str, Any]:
    """Get test settings."""
    return {
        "CONTROL_PLANE_ENV": "test",
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test_db",
        "OIDC_ISSUER": "https://test.zitadel.example.com",
        "OIDC_CLIENT_ID": "test-client-id",
        "OIDC_CLIENT_SECRET": "test-client-secret",
        "OIDC_REDIRECT_URI": "http://localhost:8000/v1/auth/callback",
        "OIDC_SCOPES": "openid profile email",
    }


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    # Create engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Add UUID support for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def http_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for testing."""

    async def override_get_session():
        yield db_session

    from src.api.dependencies import get_session
    from src.main import app

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_oidc_service():
    """Mock OIDC service for testing."""
    mock = MagicMock()
    mock.validate_token = AsyncMock()
    mock.extract_required_claims = MagicMock()

    # Default behavior: return valid claims
    async def mock_validate(token: str):
        if token == "valid-token":
            return {
                "sub": "test-user-idp-sub",
                "org_id": "test-org-id",
                "email": "test@example.com",
                "name": "Test User",
            }
        raise ValueError("Invalid token")

    mock.validate_token = mock_validate
    mock.extract_required_claims.return_value = ("test-user-idp-sub", UUID("00000000-0000-0000-0000-000000000001"))

    return mock


@pytest.fixture
def test_organization_data():
    """Test organization data."""
    return {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Test Organization",
    }


@pytest_asyncio.fixture(scope="function")
async def test_organization(db_session: AsyncSession, test_organization_data) -> Organization:
    """Create test organization in database."""
    org = Organization(**test_organization_data)
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "organization_id": UUID("00000000-0000-0000-0000-000000000001"),
        "idp_sub": "test-user-idp-sub",
        "email": "test@example.com",
        "name": "Test User",
        "status": UserStatus.ACTIVE,
    }


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_organization, test_user_data) -> User:
    """Create test user in database."""
    user = User(**test_user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def sample_oidc_claims():
    """Sample OIDC claims for testing."""
    return {
        "sub": "test-user-idp-sub",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def sample_oidc_token_response():
    """Sample OIDC token response for testing."""
    from src.schemas.auth import OIDCTokenResponse
    return OIDCTokenResponse(
        access_token="test-access-token",
        token_type="bearer",
        expires_in=3600,
        id_token="test-id-token",
    )
