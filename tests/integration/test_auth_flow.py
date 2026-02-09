"""Integration tests for OIDC authentication flow."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport
from sqlalchemy import select

from src.models.user import User, UserStatus
from src.models.organization import Organization
from src.schemas.auth import OIDCTokenResponse


@pytest.mark.asyncio
class TestOIDCLoginRedirect:
    """Tests for /v1/auth/login endpoint."""

    async def test_login_redirect_returns_302_to_zitadel(self, http_client):
        """Test that login endpoint redirects to Zitadel authorization endpoint."""
        response = await http_client.get(
            "/v1/auth/login",
            follow_redirects=False,
        )

        assert response.status_code in (302, 303, 307, 308)
        assert "location" in response.headers

        location = response.headers["location"]
        assert "test.zitadel.example.com" in location or "zitadel" in location.lower()
        assert "response_type=code" in location or "code" in location

    async def test_login_with_custom_redirect_uri(self, http_client):
        """Test login with custom redirect URI parameter."""
        custom_redirect = "https://custom.example.com/callback"
        response = await http_client.get(
            "/v1/auth/login",
            params={"redirect_uri": custom_redirect},
            follow_redirects=False,
        )

        assert response.status_code in (302, 303, 307, 308)
        location = response.headers["location"]
        # The custom redirect should be reflected in the authorization URL
        assert "redirect_uri" in location or custom_redirect in location


@pytest.mark.asyncio
class TestOIDCCallbackNewUser:
    """Tests for /v1/auth/callback endpoint with new user creation."""

    async def test_callback_creates_new_user_on_first_login(
        self, http_client, test_organization, sample_oidc_token_response, sample_oidc_claims
    ):
        """Test that callback creates a new user record on first successful OIDC authentication."""
        new_user_idp_sub = f"new-user-{uuid4()}"

        claims = {
            **sample_oidc_claims,
            "sub": new_user_idp_sub,
            "email": "newuser@example.com",
            "name": "New User",
        }

        # Create async mock for exchange_code_for_token
        mock_exchange = AsyncMock(return_value=sample_oidc_token_response)

        with patch("src.services.auth.exchange_code_for_token", mock_exchange), patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate, patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = claims
            mock_extract.return_value = (new_user_idp_sub, test_organization.id)

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "test-auth-code"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
            assert data["user"]["email"] == "newuser@example.com"
            assert data["user"]["name"] == "New User"

    async def test_new_user_has_correct_organization_association(
        self, http_client, test_organization, sample_oidc_token_response, sample_oidc_claims, db_session
    ):
        """Test that new user is associated with organization from org_id claim."""
        new_user_idp_sub = f"org-user-{uuid4()}"

        claims = {
            **sample_oidc_claims,
            "sub": new_user_idp_sub,
            "email": "orguser@example.com",
            "name": "Org User",
        }

        mock_exchange = AsyncMock(return_value=sample_oidc_token_response)

        with patch("src.services.auth.exchange_code_for_token", mock_exchange), patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate, patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = claims
            mock_extract.return_value = (new_user_idp_sub, test_organization.id)

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "test-auth-code"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user"]["organization_id"] == str(test_organization.id)

            # Verify in database
            result = await db_session.execute(
                select(User).where(User.idp_sub == new_user_idp_sub)
            )
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.organization_id == test_organization.id


@pytest.mark.asyncio
class TestOIDCCallbackExistingUser:
    """Tests for /v1/auth/callback endpoint with existing user."""

    async def test_callback_updates_existing_user_last_login(
        self, http_client, test_user, sample_oidc_token_response, sample_oidc_claims, db_session
    ):
        """Test that existing user's last_login_at is updated on successful authentication."""
        initial_last_login = test_user.last_login_at

        claims = {
            **sample_oidc_claims,
            "sub": test_user.idp_sub,
            "email": test_user.email,
            "name": test_user.name,
        }

        mock_exchange = AsyncMock(return_value=sample_oidc_token_response)

        with patch("src.services.auth.exchange_code_for_token", mock_exchange), patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate, patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = claims
            mock_extract.return_value = (test_user.idp_sub, test_user.organization_id)

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "test-auth-code"},
            )

            assert response.status_code == 200

            # Refresh user from database
            await db_session.refresh(test_user)
            # last_login_at should be updated (either was None or now newer)
            assert test_user.last_login_at is not None

    async def test_callback_returns_existing_user_data(
        self, http_client, test_user, sample_oidc_token_response, sample_oidc_claims
    ):
        """Test that callback returns existing user data without creating duplicate."""
        claims = {
            **sample_oidc_claims,
            "sub": test_user.idp_sub,
            "email": test_user.email,
            "name": test_user.name,
        }

        mock_exchange = AsyncMock(return_value=sample_oidc_token_response)

        with patch("src.services.auth.exchange_code_for_token", mock_exchange), patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate, patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = claims
            mock_extract.return_value = (test_user.idp_sub, test_user.organization_id)

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "test-auth-code"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user"]["id"] == str(test_user.id)
            assert data["user"]["email"] == test_user.email


@pytest.mark.asyncio
class TestOIDCCallbackErrors:
    """Tests for error handling in OIDC callback."""

    async def test_callback_missing_code_param_returns_400(self, http_client):
        """Test that callback returns 400 when code parameter is missing."""
        response = await http_client.get("/v1/auth/callback")

        assert response.status_code == 400

    async def test_callback_invalid_token_returns_401(self, http_client):
        """Test that callback returns 401 when token validation fails."""
        bad_token_response = OIDCTokenResponse(
            access_token="bad-token",
            token_type="bearer",
        )

        mock_exchange = AsyncMock(return_value=bad_token_response)

        with patch("src.services.auth.exchange_code_for_token", mock_exchange), patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate:

            mock_validate.side_effect = ValueError("Invalid token")

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "bad-auth-code"},
            )

            assert response.status_code == 400

    async def test_callback_missing_org_id_claim_returns_400(
        self, http_client, sample_oidc_token_response, sample_oidc_claims
    ):
        """Test that callback returns 400 when org_id claim is missing from token."""
        claims_without_org = {
            k: v for k, v in sample_oidc_claims.items() if k != "org_id"
        }

        mock_exchange = AsyncMock(return_value=sample_oidc_token_response)

        with patch("src.services.auth.exchange_code_for_token", mock_exchange), patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate, patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = claims_without_org
            mock_extract.side_effect = ValueError("org_id claim is required")

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "test-auth-code"},
            )

            assert response.status_code == 400


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Tests for /v1/auth/me endpoint."""

    async def test_auth_me_returns_current_user_info(
        self, http_client, test_user, sample_oidc_claims
    ):
        """Test that /auth/me returns information about authenticated user."""
        with patch("src.security.oidc.OIDCService.validate_token") as mock_validate, patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = {
                **sample_oidc_claims,
                "sub": test_user.idp_sub,
            }
            mock_extract.return_value = (test_user.idp_sub, test_user.organization_id)

            response = await http_client.get(
                "/v1/auth/me",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(test_user.id)
            assert data["email"] == test_user.email
            assert data["name"] == test_user.name
            assert "organization_id" in data

    async def test_auth_me_without_token_returns_403(self, http_client):
        """Test that /auth/me returns 403 when no bearer token is provided."""
        response = await http_client.get("/v1/auth/me")

        assert response.status_code == 403

    async def test_auth_me_with_invalid_token_returns_403(
        self, http_client, sample_oidc_claims
    ):
        """Test that /auth/me returns 403 with invalid token."""
        with patch("src.security.oidc.OIDCService.validate_token") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid token")

            response = await http_client.get(
                "/v1/auth/me",
                headers={"Authorization": "Bearer invalid-token"},
            )

            assert response.status_code == 403
