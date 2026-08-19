from datetime import datetime, timezone
from app.extensions import db


class DocumentMixin:
    """Shared fields and behaviour for all document models."""

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    document_number = db.Column(db.String(50), nullable=False)
    status = db.Column(
        db.Enum("draft", "confirmed", "voided", name="docstatus"),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    party_name = db.Column(db.String(255), nullable=False)
    party_trn = db.Column(db.String(50), nullable=True)
    document_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    is_voided = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    void_reason = db.Column(db.Text, nullable=True)
    voided_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    voided_at = db.Column(db.DateTime(timezone=True), nullable=True)

    currency = db.Column(db.String(3), nullable=False, default="AED", server_default="AED")
    exchange_rate_to_aed = db.Column(
        db.Numeric(20, 6), nullable=False, default=1.0, server_default="1.0"
    )

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def base_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "document_number": self.document_number,
            "status": self.status,
            "party_name": self.party_name,
            "party_trn": self.party_trn,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "is_voided": self.is_voided,
            "void_reason": self.void_reason,
            "voided_by": self.voided_by,
            "voided_at": self.voided_at.isoformat() if self.voided_at else None,
            "currency": self.currency,
            "exchange_rate_to_aed": float(self.exchange_rate_to_aed) if self.exchange_rate_to_aed is not None else 1.0,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
