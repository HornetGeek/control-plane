"""Organization model."""

import uuid
from uuid import UUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDType


class Organization(Base, TimestampMixin):
    """
    Top-level customer entity containing tenants and users.
    """

    __tablename__ = "organization"

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
