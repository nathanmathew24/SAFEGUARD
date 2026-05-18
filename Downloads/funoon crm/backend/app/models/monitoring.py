import uuid
from datetime import datetime, timezone

from sqlalchemy import TEXT, Boolean, Float, ForeignKey, Integer, UniqueConstraint, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class MonitoringConfig(Base):
    __tablename__ = "monitoring_configs"
    __table_args__ = (UniqueConstraint("project_id"),)

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(TEXT, ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    sentry_dsn: Mapped[str | None] = mapped_column(TEXT)
    uptime_monitor_id: Mapped[str | None] = mapped_column(TEXT)
    anthropic_key_label: Mapped[str | None] = mapped_column(TEXT)
    error_rate_threshold: Mapped[float] = mapped_column(Float, default=5.0)
    token_budget_monthly: Mapped[int | None] = mapped_column(Integer)
    alert_whatsapp: Mapped[str | None] = mapped_column(TEXT)

    project: Mapped["Project"] = relationship(back_populates="monitoring_config")  # type: ignore[name-defined]


class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(TEXT, ForeignKey("projects.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(TEXT, nullable=False)
    severity: Mapped[str] = mapped_column(TEXT, nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    occurred_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)

    project: Mapped["Project"] = relationship(back_populates="monitoring_events")  # type: ignore[name-defined]


class MonitoringMetric(Base):
    __tablename__ = "monitoring_metrics"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(TEXT, ForeignKey("projects.id", ondelete="CASCADE"))
    metric_type: Mapped[str] = mapped_column(TEXT, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)

    project: Mapped["Project"] = relationship(back_populates="monitoring_metrics")  # type: ignore[name-defined]
