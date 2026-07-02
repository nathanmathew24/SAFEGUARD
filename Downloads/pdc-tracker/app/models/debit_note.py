from app.extensions import db
from app.models.document_base import DocumentMixin
from app.models.line_item import LineItem


class DebitNote(DocumentMixin, db.Model):
    __tablename__ = "debit_notes"

    id = db.Column(db.Integer, primary_key=True)
    linked_invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False, default=0)  # fils

    @property
    def line_items(self):
        return LineItem.query.filter_by(
            document_type="debit_note", document_id=self.id
        ).order_by(LineItem.sort_order).all()

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "linked_invoice_id": self.linked_invoice_id,
            "reason": self.reason,
            "total_amount": self.total_amount,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
