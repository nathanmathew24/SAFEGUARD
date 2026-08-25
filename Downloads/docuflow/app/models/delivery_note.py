from app.extensions import db
from app.models.document_base import LockableMixin


class DeliveryNote(LockableMixin, db.Model):
    __tablename__ = "delivery_notes"

    id = db.Column(db.Integer, primary_key=True)
    delivery_note_number = db.Column(db.String(50), nullable=False)
    # invoice_id is required — DeliveryNote always references an Invoice
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(255), nullable=False)
    delivery_address = db.Column(db.Text, nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)

    invoice = db.relationship("Invoice", back_populates="delivery_notes")
    customer = db.relationship("Customer", lazy="joined")
    line_items = db.relationship("LineItem", foreign_keys="LineItem.delivery_note_id",
                                 backref="delivery_note", lazy="select", cascade="all, delete-orphan")

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "delivery_note_number": self.delivery_note_number,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "delivery_address": self.delivery_address,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
