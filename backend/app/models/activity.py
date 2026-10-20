import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User

# Use PostgreSQL JSONB with generic JSON fallback
JSON_FIELD_TYPE = JSON().with_variant(JSONB, "postgresql")


class ActivityLog(Base):
    """Audit and activity history trail for project events."""

    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON_FIELD_TYPE,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="activity_logs",
    )
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="activities",
    )

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, project_id={self.project_id}, action='{self.action}', entity='{self.entity_type}')>"
