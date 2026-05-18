import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, TEXT, UUID, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    client_id: Mapped[str | None] = mapped_column(TEXT, ForeignKey("clients.id"))
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    health: Mapped[str] = mapped_column(TEXT, nullable=False, default="green")
    live_since: Mapped[str | None] = mapped_column(TEXT)
    renewal_date: Mapped[str | None] = mapped_column(TEXT)
    stack_tags: Mapped[str | None] = mapped_column(JSON)
    external_links: Mapped[str | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now, onupdate=_now)

    client: Mapped["Client"] = relationship(back_populates="projects")  # type: ignore[name-defined]
    blockers: Mapped[list["ProjectBlocker"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectBlocker.created_at"
    )
    notes: Mapped[list["ProjectNote"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectNote.created_at"
    )
    monitoring_config: Mapped["MonitoringConfig | None"] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")  # type: ignore[name-defined]
    monitoring_events: Mapped[list["MonitoringEvent"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    monitoring_metrics: Mapped[list["MonitoringMetric"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    infra_costs: Mapped[list["InfraCost"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    component_deployments: Mapped[list["ComponentDeployment"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]
    incidents: Mapped[list["IncidentLog"]] = relationship(back_populates="project", cascade="all, delete-orphan")  # type: ignore[name-defined]


class ProjectBlocker(Base):
    __tablename__ = "project_blockers"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(TEXT, ForeignKey("projects.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(TEXT, nullable=False)
    owner: Mapped[str | None] = mapped_column(TEXT)
    due_date: Mapped[str | None] = mapped_column(TEXT)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)

    project: Mapped["Project"] = relationship(back_populates="blockers")


class ProjectNote(Base):
    __tablename__ = "project_notes"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(TEXT, ForeignKey("projects.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)

    project: Mapped["Project"] = relationship(back_populates="notes")
