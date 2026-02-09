"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User information response."""

    id: UUID = Field(..., description="User ID")
    organization_id: UUID = Field(..., description="Organization ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User display name")
    last_login_at: datetime | None = Field(None, description="Last login timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "last_login_at": "2024-01-15T10:30:00Z",
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Token response from OIDC callback."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int | None = Field(None, description="Token expiration in seconds")
    refresh_token: str | None = Field(None, description="Refresh token (if available)")
    id_token: str | None = Field(None, description="ID token (JWT)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            ]
        }
    }


class AuthResponse(BaseModel):
    """Complete authentication response."""

    access_token: str = Field(..., description="Access token for API calls")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                        "email": "user@example.com",
                        "name": "John Doe",
                        "last_login_at": "2024-01-15T10:30:00Z",
                    },
                }
            ]
        }
    }


class OIDCTokenResponse(BaseModel):
    """Internal model for OIDC token endpoint response."""

    access_token: str
    token_type: str
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None


class OIDCUserInfo(BaseModel):
    """OIDC user claims."""

    sub: str = Field(..., description="Subject - unique user identifier from IdP")
    org_id: str = Field(..., description="Organization ID from custom claim")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User display name")
    given_name: str | None = Field(None, description="Given name")
    family_name: str | None = Field(None, description="Family name")
