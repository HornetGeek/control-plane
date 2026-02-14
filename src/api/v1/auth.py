"""OIDC authentication endpoints."""

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_session
from src.schemas.auth import AuthResponse, UserResponse
from src.services.auth import exchange_code_for_token, get_or_create_user
from src.security.oidc import get_oidc_service
from src.models.user import User


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/login")
async def login(
    request: Request,
    redirect_uri: str | None = Query(None, description="Optional override for redirect URI"),
) -> None:
    """Initiate OIDC login flow.

    Redirects the user's browser to the Zitadel authorization endpoint.
    After authentication, Zitadel will redirect back to the callback endpoint.
    """
    settings = request.app.state.settings
    oidc_service = get_oidc_service()

    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": redirect_uri or settings.oidc_redirect_uri,
        "scope": settings.oidc_scopes,
        "state": oidc_service.generate_state(),  # CSRF protection
    }

    # Use Keycloak-style path (works with Keycloak, can be overridden for other providers)
    auth_url = f"{settings.oidc_issuer}/protocol/openid-connect/auth?{urlencode(params)}"

    # Raise HTTPException with redirect status to trigger browser redirect
    raise HTTPException(status_code=302, headers={"Location": auth_url})


@router.get("/callback")
async def callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
    code: str = Query(..., description="Authorization code from Zitadel"),
) -> AuthResponse:
    """Handle OIDC callback from Zitadel.

    Exchanges the authorization code for tokens, validates the ID token,
    creates or updates the user record, and returns the user info with access token.
    """
    settings = request.app.state.settings
    oidc_service = get_oidc_service()

    try:
        # Exchange authorization code for tokens
        token_response = await exchange_code_for_token(code)

        # Validate the ID token and extract claims
        id_token = token_response.id_token or token_response.access_token
        payload = await oidc_service.validate_token(id_token)

        # Extract required claims (sub, org_id)
        idp_sub, org_id = oidc_service.extract_required_claims(payload)

        # Extract user info from claims
        email = payload.get("email", "")
        name = payload.get("name", "")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email claim is required but missing from token",
            )

        # Get or create user
        user = await get_or_create_user(
            session=session,
            idp_sub=idp_sub,
            org_id=org_id,
            email=email,
            name=name,
        )

        return AuthResponse(
            access_token=token_response.access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred during authentication",
        ) from e


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Get current authenticated user information.

    Returns the user record associated with the authenticated session.
    Requires a valid bearer token from the OIDC callback.
    """
    from src.services.auth import get_current_user_info
    from uuid import UUID

    user_id = current_user.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user context")

    user = await get_current_user_info(session, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)
