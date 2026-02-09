"""FastAPI dependencies for authentication and authorization."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.membership import MembershipRole
from src.security.oidc import OIDCValidationError, get_oidc_service
from src.security.authorization import AuthorizationService, check_role
from src.db.session import get_session as _get_session


security = HTTPBearer()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async for session in _get_session():
        yield session


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """
    Dependency to extract and validate current user from JWT token.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials

    Returns:
        Decoded token payload with user info

    Raises:
        HTTPException: 401 if token is invalid
    """
    token = credentials.credentials
    oidc_service = get_oidc_service()

    try:
        # Validate token and extract claims
        payload = await oidc_service.validate_token(token)
        sub, org_id = oidc_service.extract_required_claims(payload)

        # Attach user info to request state for use in endpoints
        request.state.user_id = sub
        request.state.org_id = org_id

        return {
            "user_id": sub,
            "org_id": org_id,
            "email": payload.get("email"),
            "name": payload.get("name"),
        }

    except OIDCValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    authorization: Annotated[str | None, Header(...)] = None,
) -> dict | None:
    """
    Optional user dependency - doesn't raise if no token provided.

    Returns user info if token is valid, None otherwise.
    """
    if not authorization:
        return None

    try:
        if not authorization.startswith("Bearer "):
            return None

        token = authorization[7:]  # Remove "Bearer " prefix
        oidc_service = get_oidc_service()
        payload = await oidc_service.validate_token(token)
        sub, org_id = oidc_service.extract_required_claims(payload)

        request.state.user_id = sub
        request.state.org_id = org_id

        return {
            "user_id": sub,
            "org_id": org_id,
            "email": payload.get("email"),
            "name": payload.get("name"),
        }

    except Exception:
        return None


CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[dict | None, Depends(get_optional_user)]


def require_role(required_role: MembershipRole):
    """
    Factory to create a dependency that requires a specific role.

    Usage:
        @app.get("/admin-endpoint")
        async def admin_endpoint(user: CurrentUser, _=Depends(require_role(MembershipRole.ORG_ADMIN))):
            ...
    """

    async def role_checker(current_user: CurrentUser = None) -> None:
        # Note: In a real implementation, you'd fetch the user's role from the database
        # For now, this is a placeholder that would be implemented with full user context
        pass

    return Depends(role_checker)
