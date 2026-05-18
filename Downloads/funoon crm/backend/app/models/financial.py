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


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(TEXT, ForeignKey("clients.id", ondelete="CASCADE"))
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    cycle: Mapped[str] = mapped_column(TEXT, default="monthly")
    status: Mapped[str] = mapped_column(TEXT, default="active")  # active | paused | churned
    started_at: Mapped[str | None] = mapped_column(TEXT)
    ended_at: Mapped[str | None] = mapped_column(TEXT)
    notes: Mapped[str | None] = mapped_column(TEXT)

    client: Mapped["Client"] = relationship(back_populates="billing_records")  # type: ignore[name-defined]


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    client_id: Mapped[str | None] = mapped_column(TEXT, ForeignKey("clients.id"))
    number: Mapped[str | None] = mapped_column(TEXT, unique=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_date: Mapped[str | None] = mapped_column(TEXT)
    due_date: Mapped[str | None] = mapped_column(TEXT)
    paid_date: Mapped[str | None] = mapped_column(TEXT)
    status: Mapped[str] = mapped_column(TEXT, default="draft")   # draft | sent | paid | overdue
    doc_type: Mapped[str] = mapped_column(TEXT, default="invoice")  # invoice | receipt | quote
    notes: Mapped[str | None] = mapped_column(TEXT)
    line_items: Mapped[list | None] = mapped_column(JSON, default=list)

    client: Mapped["Client | None"] = relationship(back_populates="invoices")  # type: ignore[name-defined]


class InfraCost(Base):
    __tablename__ = "infra_costs"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(TEXT, ForeignKey("projects.id"))
    service: Mapped[str] = mapped_column(TEXT, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[str] = mapped_column(TEXT, nullable=False)
    notes: Mapped[str | None] = mapped_column(TEXT)

    project: Mapped["Project | None"] = relationship(back_populates="infra_costs")  # type: ignore[name-defined]


class Expense(Base):
    """Non-infra operating expenses: salaries, tools, subscriptions, travel, etc."""
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    category: Mapped[str] = mapped_column(TEXT, nullable=False)  # salary | tool | subscription | travel | other
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # AED
    month: Mapped[str] = mapped_column(TEXT, nullable=False)      # YYYY-MM-01
    recurring: Mapped[bool] = mapped_column(Integer, default=0)   # SQLite uses int for bool
    notes: Mapped[str | None] = mapped_column(TEXT)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now)
