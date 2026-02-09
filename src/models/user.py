"""User model."""

import uuid
from enum import Enum
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDType


class UserStatus(str, Enum):
    """User status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class User(Base, TimestampMixin):
    """
    Person authenticated via OIDC.
    Belongs to exactly one organization.
    """

    __tablename__ = "user_account"

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
    idp_sub: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        String(20),
        nullable=False,
        default=UserStatus.ACTIVE,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
