"""Audit event stubs for security logging.

These provide interfaces for future audit infrastructure without
implementing external dispatch in the MVP.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel


class AuditEventType(str, Enum):
    """Types of audit events."""

    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    TENANT_CREATED = "tenant_created"
    TENANT_UPDATED = "tenant_updated"
    TENANT_DELETED = "tenant_deleted"
    MEMBERSHIP_CREATED = "membership_created"
    MEMBERSHIP_DELETED = "membership_deleted"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    APPLICATION_LAUNCHED = "application_launched"


@dataclass
class AuditEvent:
    """Audit event data structure."""

    event_id: UUID
    event_type: AuditEventType
    timestamp: datetime
    user_id: str | None
    organization_id: str | None
    tenant_id: str | None
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any]
    correlation_id: str | None
    ip_address: str | None
    user_agent: str | None


class AuditLogger:
    """
    Audit logger stub interface.

    MVP: Minimal logging to internal storage
    Future: External dispatch to audit service
    """

    async def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        MVP implementation: Log to console (structured logging)
        Future: Send to audit service message queue
        """
        # Structured log entry (in production, use proper structured logging)
        log_entry = {
            "event_id": str(event.event_id),
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "organization_id": event.organization_id,
            "tenant_id": event.tenant_id,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "details": event.details,
            "correlation_id": event.correlation_id,
        }

        # In MVP: print to console (replace with proper logger in production)
        print(f"AUDIT: {log_entry}")

        # Future: Send to message queue for audit service processing


class AuditService:
    """Service for creating and logging audit events."""

    def __init__(self):
        self.logger = AuditLogger()

    def create_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        organization_id: str | None = None,
        tenant_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        """Create a new audit event."""
        return AuditEvent(
            event_id=uuid4(),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            organization_id=organization_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log(self, event: AuditEvent) -> None:
        """Log an audit event."""
        await self.logger.log_event(event)


@lru_cache
def get_audit_service() -> AuditService:
    """Get cached audit service instance."""
    return AuditService()
