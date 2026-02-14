"""Authentication service for OIDC flow and user management."""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.schemas.auth import OIDCTokenResponse, OIDCUserInfo
from src.security.oidc import get_oidc_service
from src.models.user import User, UserStatus


async def exchange_code_for_token(code: str, redirect_uri: str | None = None) -> OIDCTokenResponse:
    """Exchange authorization code for access token at OIDC token endpoint.

    Args:
        code: Authorization code from OIDC provider
        redirect_uri: Optional redirect URI override

    Returns:
        OIDCTokenResponse with access_token and other token data

    Raises:
        httpx.HTTPError: If token request fails
        ValueError: If response is invalid
    """
    settings = get_settings()

    # Use Keycloak-style path (works with Keycloak, can be overridden for other providers)
    token_url = f"{settings.oidc_issuer}/protocol/openid-connect/token"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri or settings.oidc_redirect_uri,
        "client_id": settings.oidc_client_id,
        "client_secret": settings.oidc_client_secret,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, headers=headers, timeout=10.0)
        response.raise_for_status()
        token_data = response.json()

    return OIDCTokenResponse(**token_data)


async def get_or_create_user(
    session: AsyncSession,
    idp_sub: str,
    org_id: str | object,  # UUID or string
    email: str,
    name: str,
) -> User:
    """Get existing user or create new one from OIDC claims.

    Args:
        session: Database session
        idp_sub: Identity provider subject (OIDC sub claim)
        org_id: Organization ID from org_id claim (UUID or string)
        email: User email
        name: User display name

    Returns:
        User instance (existing or newly created)
    """
    from uuid import UUID

    # Convert org_id to string for storage (UUIDType handles conversion)
    if isinstance(org_id, UUID):
        org_id_str = str(org_id)
    else:
        org_id_str = org_id

    # Try to find existing user by idp_sub
    result = await session.execute(select(User).where(User.idp_sub == idp_sub))
    user = result.scalar_one_or_none()

    if user:
        # Update last login timestamp
        from datetime import datetime, timezone
        user.last_login_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)
        return user

    # Create new user
    new_user = User(
        idp_sub=idp_sub,
        organization_id=org_id_str,
        email=email,
        name=name,
        status=UserStatus.ACTIVE,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


async def get_current_user_info(
    session: AsyncSession,
    user_id: str,
) -> User | None:
    """Get current user information by ID.

    Args:
        session: Database session
        user_id: User ID (UUID string or idp_sub)

    Returns:
        User instance or None if not found
    """
    from uuid import UUID

    # Try as UUID first
    try:
        user_uuid = UUID(user_id)
        result = await session.execute(select(User).where(User.id == user_uuid))
        return result.scalar_one_or_none()
    except ValueError:
        # If not UUID, try as idp_sub
        result = await session.execute(select(User).where(User.idp_sub == user_id))
        return result.scalar_one_or_none()
