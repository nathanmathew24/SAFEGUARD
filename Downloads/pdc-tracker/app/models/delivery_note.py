from app.extensions import db
from app.models.document_base import DocumentMixin


class DeliveryNote(DocumentMixin, db.Model):
    __tablename__ = "delivery_notes"

    id = db.Column(db.Integer, primary_key=True)
    linked_invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    received_by = db.Column(db.String(255), nullable=True)
    items_description = db.Column(db.Text, nullable=True)

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "linked_invoice_id": self.linked_invoice_id,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "received_by": self.received_by,
            "items_description": self.items_description,
        })
        return d
