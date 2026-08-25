from app.extensions import db
from app.models.document_base import LockableMixin


class CreditNote(LockableMixin, db.Model):
    __tablename__ = "credit_notes"

    id = db.Column(db.Integer, primary_key=True)
    credit_note_number = db.Column(db.String(50), nullable=False)
    # Must reference a LOCKED invoice — enforced in the route before creation
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    # is_full_reversal: True = full invoice reversal; False = partial (future: full schema)
    is_full_reversal = db.Column(db.Boolean, nullable=False, default=False)

    invoice = db.relationship("Invoice", back_populates="credit_notes")
    customer = db.relationship("Customer", lazy="joined")
    line_items = db.relationship("LineItem", foreign_keys="LineItem.credit_note_id",
                                 backref="credit_note", lazy="select", cascade="all, delete-orphan")

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "credit_note_number": self.credit_note_number,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "reason": self.reason,
            "is_full_reversal": self.is_full_reversal,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
