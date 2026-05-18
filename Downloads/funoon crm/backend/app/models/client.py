import uuid
from datetime import datetime, timezone

from sqlalchemy import TEXT, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    contact_name: Mapped[str | None] = mapped_column(TEXT)
    whatsapp: Mapped[str | None] = mapped_column(TEXT)
    email: Mapped[str | None] = mapped_column(TEXT)
    source: Mapped[str | None] = mapped_column(TEXT)
    stage: Mapped[str] = mapped_column(TEXT, nullable=False, default="inbound")
    enquiry: Mapped[str | None] = mapped_column(TEXT)
    estimated_mrr: Mapped[int | None] = mapped_column(Integer)
    next_action: Mapped[str | None] = mapped_column(TEXT)
    next_action_due: Mapped[str | None] = mapped_column(TEXT)
    ai_context: Mapped[str | None] = mapped_column(TEXT)
    ai_context_updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now, onupdate=_now)

    stage_history: Mapped[list["ClientStageHistory"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", order_by="ClientStageHistory.moved_at"
    )
    notes: Mapped[list["ClientNote"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", order_by="ClientNote.created_at"
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="client")  # type: ignore[name-defined]
    billing_records: Mapped[list["BillingRecord"]] = relationship(back_populates="client", cascade="all, delete-orphan")  # type: ignore[name-defined]
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="client", cascade="all, delete-orphan")  # type: ignore[name-defined]


class ClientStageHistory(Base):
    __tablename__ = "client_stage_history"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(TEXT, ForeignKey("clients.id", ondelete="CASCADE"))
    from_stage: Mapped[str | None] = mapped_column(TEXT)
    to_stage: Mapped[str] = mapped_column(TEXT, nullable=False)
    note: Mapped[str | None] = mapped_column(TEXT)
    moved_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)

    client: Mapped["Client"] = relationship(back_populates="stage_history")


class ClientNote(Base):
    __tablename__ = "client_notes"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(TEXT, ForeignKey("clients.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)

    client: Mapped["Client"] = relationship(back_populates="notes")
