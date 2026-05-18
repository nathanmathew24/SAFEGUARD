import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, TEXT, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class SOP(Base):
    __tablename__ = "sops"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(TEXT, nullable=False)
    category: Mapped[str | None] = mapped_column(TEXT)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now, onupdate=_now)


class IncidentLog(Base):
    __tablename__ = "incident_log"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(TEXT, ForeignKey("projects.id"))
    severity: Mapped[str] = mapped_column(TEXT, nullable=False)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(TEXT)
    resolution: Mapped[str | None] = mapped_column(TEXT)
    time_to_resolve: Mapped[int | None] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)

    project: Mapped["Project | None"] = relationship(back_populates="incidents")  # type: ignore[name-defined]


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    messages: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now, onupdate=_now)
