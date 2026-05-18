import uuid
from datetime import datetime, timezone

from sqlalchemy import TEXT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class CompanySettings(Base):
    """Single-row table — one record, always upserted by a fixed key."""
    __tablename__ = "company_settings"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    # Company identity
    company_name: Mapped[str] = mapped_column(TEXT, default="funoon.ai")
    tagline: Mapped[str | None] = mapped_column(TEXT, default="Operations, Automated")
    address_line1: Mapped[str | None] = mapped_column(TEXT, default="SRTIP, Sharjah")
    address_line2: Mapped[str | None] = mapped_column(TEXT, default="UAE")
    trn: Mapped[str | None] = mapped_column(TEXT)
    email: Mapped[str | None] = mapped_column(TEXT, default="farzeelfaz@gmail.com")
    phone: Mapped[str | None] = mapped_column(TEXT, default="+971 50 756 2833")
    website: Mapped[str | None] = mapped_column(TEXT, default="funoon.ai")
    # Bank / payment details
    bank_name: Mapped[str | None] = mapped_column(TEXT, default="Emirates NBD")
    bank_account_name: Mapped[str | None] = mapped_column(TEXT, default="Funoon FZC")
    bank_iban: Mapped[str | None] = mapped_column(TEXT, default="AE00 0000 0000 0000 0000 000")
    bank_account_number: Mapped[str | None] = mapped_column(TEXT)
    bank_swift: Mapped[str | None] = mapped_column(TEXT)
    bank_currency: Mapped[str] = mapped_column(TEXT, default="AED")
    # Invoice defaults
    invoice_payment_terms: Mapped[str | None] = mapped_column(TEXT, default="Payment due within 30 days of issue.")
    invoice_notes: Mapped[str | None] = mapped_column(TEXT)
    invoice_prefix: Mapped[str] = mapped_column(TEXT, default="INV")
    vat_rate: Mapped[int] = mapped_column(TEXT, default="5")
    letterhead_path: Mapped[str | None] = mapped_column(TEXT)
    signature_path: Mapped[str | None] = mapped_column(TEXT)
    stamp_path: Mapped[str | None] = mapped_column(TEXT)

    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=_now, onupdate=_now)
