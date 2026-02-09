"""Tenant model."""

import uuid
from uuid import UUID
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDType


class Tenant(Base, TimestampMixin):
    """
    Branch or business unit within an organization.
    Subscription is scoped at tenant level.
    """

    __tablename__ = "tenant"

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"
