import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, TEXT, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Component(Base):
    __tablename__ = "components"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    category: Mapped[str] = mapped_column(TEXT, nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT)
    tech_tags: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(TEXT, default="stable")
    version: Mapped[str | None] = mapped_column(TEXT)
    github_path: Mapped[str | None] = mapped_column(TEXT)
    notes: Mapped[str | None] = mapped_column(TEXT)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now, onupdate=_now)

    deployments: Mapped[list["ComponentDeployment"]] = relationship(
        back_populates="component", cascade="all, delete-orphan"
    )


class ComponentDeployment(Base):
    __tablename__ = "component_deployments"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    component_id: Mapped[str] = mapped_column(TEXT, ForeignKey("components.id", ondelete="CASCADE"))
    project_id: Mapped[str] = mapped_column(TEXT, ForeignKey("projects.id", ondelete="CASCADE"))

    component: Mapped["Component"] = relationship(back_populates="deployments")
    project: Mapped["Project"] = relationship(back_populates="component_deployments")  # type: ignore[name-defined]
