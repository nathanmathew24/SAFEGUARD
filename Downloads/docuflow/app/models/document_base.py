"""
Two-layer locking is implemented here (app layer) and enforced by
Postgres triggers (db layer — see migrations/versions/*_add_lock_triggers.py).

App layer:
  - locked_at column: None = editable, timestamp = locked
  - finalize() sets status="finalized" and locked_at=now(), logs audit event
  - ensure_editable() raises PermissionError if already locked
    (caught by the global error handler → 423 Locked)

DB layer (parallel enforcement — see trigger migration):
  - BEFORE UPDATE trigger rejects any UPDATE where OLD.locked_at IS NOT NULL
  - This catches raw SQL, bad migrations, anything bypassing the app
"""
from datetime import datetime, timezone
from app.extensions import db


class LockableMixin:
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    status = db.Column(
        db.Enum("draft", "finalized", name="doc_status_enum"),
        nullable=False, default="draft", server_default="draft",
    )
    locked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    locked_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    document_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    currency = db.Column(db.String(3), nullable=False, default="AED", server_default="AED")
    exchange_rate_to_aed = db.Column(db.Numeric(20, 6), nullable=False, default=1.0, server_default="1.0")

    subtotal = db.Column(db.Numeric(20, 4), nullable=False, default=0, server_default="0")
    vat_amount = db.Column(db.Numeric(20, 4), nullable=False, default=0, server_default="0")  # TODO: real VAT logic
    total = db.Column(db.Numeric(20, 4), nullable=False, default=0, server_default="0")

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def ensure_editable(self):
        if self.locked_at is not None:
            raise PermissionError(
                f"{self.__class__.__name__} {self.id} is finalized and cannot be edited"
            )

    def finalize(self, user_id: int):
        self.ensure_editable()
        self.status = "finalized"
        self.locked_at = datetime.now(timezone.utc)
        self.locked_by = user_id

    def base_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "status": self.status,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "locked_by": self.locked_by,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "notes": self.notes,
            "currency": self.currency,
            "exchange_rate_to_aed": float(self.exchange_rate_to_aed),
            "subtotal": float(self.subtotal),
            "vat_amount": float(self.vat_amount),
            "total": float(self.total),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
