"""Membership model."""

import uuid
from enum import Enum
from uuid import UUID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDType


class MembershipRole(str, Enum):
    """Role values for tenant membership."""

    ORG_ADMIN = "org_admin"
    TENANT_ADMIN = "tenant_admin"
    TENANT_MEMBER = "tenant_member"


class Membership(Base, TimestampMixin):
    """
    Association between a user and a tenant with a specific role.
    """

    __tablename__ = "membership"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),)

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MembershipRole] = mapped_column(String(20), nullable=False)

    def __repr__(self) -> str:
        return f"<Membership(id={self.id}, role={self.role})>"
