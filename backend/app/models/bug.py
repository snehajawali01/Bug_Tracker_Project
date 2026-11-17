
import enum
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class BugPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BugStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    priority: Mapped[BugPriority] = mapped_column(
        Enum(
            BugPriority,
            name="bug_priority",
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ]
        ),
        default=BugPriority.MEDIUM,
        nullable=False
    )

    status: Mapped[BugStatus] = mapped_column(
        Enum(
            BugStatus,
            name="bug_status",
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ]
        ),
        default=BugStatus.OPEN,
        nullable=False
    )

    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    reporter = relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reported_bugs"
    )

    assignee = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_bugs"
    )

    comments = relationship(
        "Comment",
        back_populates="bug",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
