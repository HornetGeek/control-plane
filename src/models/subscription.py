"""Subscription model."""

import uuid
from enum import Enum
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDType


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


class Subscription(Base, TimestampMixin):
    """
    Entitlement that allows a tenant to access an application.
    """

    __tablename__ = "subscription"
    __table_args__ = (UniqueConstraint("tenant_id", "app_key", name="uq_subscription_tenant_app"),)

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
    app_key: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("application.app_key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, status={self.status})>"
