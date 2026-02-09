"""Database session management for async SQLAlchemy."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings


def get_engine():
    """Create async database engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.control_plane_log_level == "debug",
        pool_pre_ping=True,
    )


_async_session_factory = async_sessionmaker(
    get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Usage:
        async with get_session() as session:
            # use session
    """
    async with _async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
