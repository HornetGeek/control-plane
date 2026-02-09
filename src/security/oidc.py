"""OIDC token validation and JWKS caching."""

import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import httpx
from jwt import decode, PyJWKClient, PyJWKClientError
from jwt.exceptions import InvalidTokenError

from src.config import get_settings


class OIDCValidationError(Exception):
    """OIDC token validation failed."""

    pass


class OIDCService:
    """
    Service for validating OIDC tokens via JWKS.

    Caches JWKS keys for 5 minutes to reduce calls to the OIDC provider.
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._jwks_client: PyJWKClient | None = None
        self._jwks_last_update: datetime | None = None
        self._jwks_cache_ttl = timedelta(minutes=5)

    def _get_jwks_client(self) -> PyJWKClient:
        """Get or refresh JWKS client."""
        now = datetime.now(timezone.utc)

        # Refresh if TTL expired
        if (
            self._jwks_client is None
            or self._jwks_last_update is None
            or now - self._jwks_last_update > self._jwks_cache_ttl
        ):
            self._jwks_client = PyJWKClient(f"{self.settings.oidc_issuer}/.well-known/jwks.json")
            self._jwks_last_update = now

        return self._jwks_client

    async def validate_token(self, token: str) -> dict:
        """
        Validate and decode a JWT bearer token.

        Args:
            token: The JWT token string

        Returns:
            Decoded token payload

        Raises:
            OIDCValidationError: If token is invalid or expired
        """
        try:
            jwks_client = self._get_jwks_client()

            # Decode and validate token
            payload = decode(
                token,
                key=jwks_client.get_signing_key_from_jwt(token),
                algorithms=["RS256"],
                audience=[self.settings.oidc_client_id],
                issuer=self.settings.oidc_issuer,
            )
            return payload

        except InvalidTokenError as e:
            raise OIDCValidationError(f"Invalid token: {str(e)}")
        except PyJWKClientError as e:
            raise OIDCValidationError(f"Failed to fetch signing keys: {str(e)}")

    def extract_required_claims(self, payload: dict) -> tuple[str, str]:
        """
        Extract required claims from validated token.

        Args:
            payload: Decoded token payload

        Returns:
            Tuple of (sub, org_id) claims

        Raises:
            OIDCValidationError: If required claims are missing
        """
        sub = payload.get("sub")
        org_id = payload.get("org_id")

        if not sub:
            raise OIDCValidationError("Token missing required 'sub' claim")
        if not org_id:
            raise OIDCValidationError("Token missing required 'org_id' claim")

        return sub, org_id

    def generate_state(self) -> str:
        """
        Generate a random state parameter for CSRF protection.

        Returns:
            Random state string
        """
        return secrets.token_urlsafe(32)


@lru_cache
def get_oidc_service() -> OIDCService:
    """Get cached OIDC service instance."""
    return OIDCService()
