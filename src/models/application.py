"""Application model."""

from enum import Enum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class ApplicationStatus(str, Enum):
    """Application status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class Application(Base, TimestampMixin):
    """
    Product that tenants can subscribe to (PACS, ERP).
    """

    __tablename__ = "application"

    app_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    launch_base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ApplicationStatus.ACTIVE,
    )

    def __repr__(self) -> str:
        return f"<Application(app_key={self.app_key}, name={self.name})>"
