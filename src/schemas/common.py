"""Common Pydantic schemas for API responses."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format."""

    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error context")
    request_id: str | None = Field(None, description="Correlation ID for troubleshooting")

    model_config = {"json_schema_extra": {"examples": [{"code": "UNAUTHORIZED", "message": "Authentication required"}]}}


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list responses."""

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Maximum items per page")
    offset: int = Field(..., description="Number of items skipped")

    model_config = {"json_schema_extra": {"examples": [{"total": 100, "limit": 50, "offset": 0}]})


class PagedParams(BaseModel):
    """Query parameters for pagination."""

    limit: int = Field(default=50, ge=1, le=1000, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Items to skip")


class LaunchRequest(BaseModel):
    """Request to launch an application."""

    tenant_id: UUID = Field(..., description="Tenant ID")
    app_key: str = Field(..., description="Application key")
    return_to: str | None = Field(None, description="Optional return URL after launch")


class LaunchResponse(BaseModel):
    """Response with application launch URL."""

    redirect_url: str = Field(..., description="URL to redirect to application with context")
