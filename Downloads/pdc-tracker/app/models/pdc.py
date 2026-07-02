from datetime import datetime, timezone
from app.extensions import db
from app.models.document_base import DocumentMixin


class PDC(DocumentMixin, db.Model):
    __tablename__ = "pdcs"

    id = db.Column(db.Integer, primary_key=True)
    cheque_number = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(255), nullable=False)
    cheque_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # fils — never float
    submission_reminder_days = db.Column(db.Integer, nullable=False, default=3)
    pdc_status = db.Column(
        db.Enum("pending", "submitted", "cleared", "bounced", "cancelled",
                name="pdcstatus"),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    # Phase 4 additions
    pdc_direction = db.Column(
        db.Enum("received", "issued", name="pdcdirection"),
        nullable=False,
        default="received",
        server_default="received",
    )
    reminder_sent = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cleared_at = db.Column(db.DateTime(timezone=True), nullable=True)
    bounced_at = db.Column(db.DateTime(timezone=True), nullable=True)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    linked_invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "cheque_number": self.cheque_number,
            "bank_name": self.bank_name,
            "cheque_date": self.cheque_date.isoformat() if self.cheque_date else None,
            "amount": self.amount,
            "submission_reminder_days": self.submission_reminder_days,
            "pdc_status": self.pdc_status,
            "pdc_direction": self.pdc_direction,
            "reminder_sent": self.reminder_sent,
            "reminder_sent_at": self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
            "cleared_at": self.cleared_at.isoformat() if self.cleared_at else None,
            "bounced_at": self.bounced_at.isoformat() if self.bounced_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "linked_invoice_id": self.linked_invoice_id,
        })
        return d
