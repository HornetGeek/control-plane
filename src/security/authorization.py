"""Authorization helpers for role-based access control."""

from enum import Enum
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException, status

from src.models.membership import MembershipRole


class Permission(str, Enum):
    """Permission strings for authorization."""

    # Organization level
    ORG_ADMIN = "org_admin"

    # Tenant level
    TENANT_ADMIN = "tenant_admin"
    TENANT_MEMBER = "tenant_member"


class AuthorizationError(Exception):
    """Authorization check failed."""

    pass


class AuthorizationService:
    """Service for checking role-based permissions."""

    @staticmethod
    def require_role(user_role: MembershipRole, required_role: MembershipRole) -> None:
        """
        Check if user has required role.

        Role hierarchy: org_admin > tenant_admin > tenant_member

        Args:
            user_role: The user's role
            required_role: The minimum required role

        Raises:
            AuthorizationError: If user doesn't have required role
        """
        role_hierarchy = {
            MembershipRole.ORG_ADMIN: 3,
            MembershipRole.TENANT_ADMIN: 2,
            MembershipRole.TENANT_MEMBER: 1,
        }

        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise AuthorizationError(
                f"User with role '{user_role}' does not have required role '{required_role}'"
            )

    @staticmethod
    def can_manage_tenant(user_role: MembershipRole) -> bool:
        """Check if user can manage a tenant (org_admin or tenant_admin)."""
        return user_role in (MembershipRole.ORG_ADMIN, MembershipRole.TENANT_ADMIN)

    @staticmethod
    def can_modify_subscription(user_role: MembershipRole) -> bool:
        """Check if user can modify subscriptions (org_admin or tenant_admin)."""
        return user_role in (MembershipRole.ORG_ADMIN, MembershipRole.TENANT_ADMIN)


def check_role(user_role: MembershipRole, required_role: MembershipRole) -> None:
    """
    FastAPI dependency to check if user has required role.

    Raises:
        HTTPException: 403 Forbidden if user doesn't have required role
    """
    try:
        AuthorizationService.require_role(user_role, required_role)
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@lru_cache
def get_authorization_service() -> AuthorizationService:
    """Get cached authorization service instance."""
    return AuthorizationService()
