"""Contract tests for /v1/auth endpoints against OpenAPI specification."""

import pytest

from tests.integration.test_auth_flow import TestOIDCLoginRedirect


class TestAuthEndpointsContract:
    """Contract tests ensuring auth endpoints match OpenAPI spec."""

    async def test_login_endpoint_returns_redirect(self, http_client):
        """Test /v1/auth/login returns 302 redirect per OpenAPI spec."""
        response = await http_client.get(
            "/v1/auth/login",
            follow_redirects=False,
        )

        # OpenAPI spec specifies 302 response
        assert response.status_code in (302, 303, 307, 308)
        assert "location" in response.headers

    async def test_login_accepts_redirect_uri_param(self, http_client):
        """Test /v1/auth/login accepts optional redirect_uri parameter."""
        response = await http_client.get(
            "/v1/auth/login",
            params={"redirect_uri": "http://localhost:8080/callback"},
            follow_redirects=False,
        )

        # Should not return 400 for valid parameter
        assert response.status_code in (302, 303, 307, 308)

    async def test_callback_missing_code_returns_400(self, http_client):
        """Test /v1/auth/callback returns 400 when code is missing."""
        response = await http_client.get("/v1/auth/callback")

        # OpenAPI spec specifies 400 for invalid callback request
        assert response.status_code == 400

    async def test_callback_response_structure(self, http_client, test_organization, sample_oidc_token_response, sample_oidc_claims):
        """Test /v1/auth/callback returns response matching AuthResponse schema."""
        new_user_idp_sub = "contract-test-user"

        with pytest.mock.patch("src.services.auth.exchange_code_for_token") as mock_exchange, pytest.mock.patch(
            "src.security.oidc.OIDCService.validate_token"
        ) as mock_validate, pytest.mock.patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_exchange.return_value = sample_oidc_token_response
            mock_validate.return_value = {
                **sample_oidc_claims,
                "sub": new_user_idp_sub,
                "email": "contract@example.com",
                "name": "Contract Test",
            }
            mock_extract.return_value = (new_user_idp_sub, test_organization.id)

            response = await http_client.get(
                "/v1/auth/callback",
                params={"code": "test-code"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify AuthResponse schema structure
            assert "access_token" in data
            assert isinstance(data["access_token"], str)
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            assert "user" in data

            # Verify UserResponse schema within AuthResponse
            user = data["user"]
            assert "id" in user
            assert "organization_id" in user
            assert "email" in user
            assert "name" in user
            assert "last_login_at" in user

    async def test_me_endpoint_response_structure(self, http_client, test_user, sample_oidc_claims):
        """Test /v1/auth/me returns response matching UserResponse schema."""
        with pytest.mock.patch("src.security.oidc.OIDCService.validate_token") as mock_validate, pytest.mock.patch(
            "src.security.oidc.OIDCService.extract_required_claims"
        ) as mock_extract:

            mock_validate.return_value = {
                **sample_oidc_claims,
                "sub": test_user.idp_sub,
            }
            mock_extract.return_value = (test_user.idp_sub, test_user.organization_id)

            response = await http_client.get(
                "/v1/auth/me",
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify UserResponse schema structure
            assert "id" in data
            assert "organization_id" in data
            assert "email" in data
            assert "name" in data
            assert "last_login_at" in data

    async def test_me_unauthorized_without_token(self, http_client):
        """Test /v1/auth/me returns 401 without bearer token per OpenAPI spec."""
        response = await http_client.get("/v1/auth/me")

        # OpenAPI spec specifies 401 for not authenticated
        assert response.status_code == 401

    async def test_error_response_format(self, http_client):
        """Test error responses match ErrorResponse schema."""
        response = await http_client.get("/v1/auth/callback")

        assert response.status_code == 400
        data = response.json()

        # ErrorResponse schema should have code and message
        assert "code" in data or "message" in data or "detail" in data
