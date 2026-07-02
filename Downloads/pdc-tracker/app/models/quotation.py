from app.extensions import db
from app.models.document_base import DocumentMixin
from app.models.line_item import LineItem


class Quotation(DocumentMixin, db.Model):
    __tablename__ = "quotations"

    id = db.Column(db.Integer, primary_key=True)
    valid_until = db.Column(db.Date, nullable=True)
    subtotal_amount = db.Column(db.Integer, nullable=False, default=0)  # fils
    tax_amount = db.Column(db.Integer, nullable=False, default=0)       # fils
    total_amount = db.Column(db.Integer, nullable=False, default=0)     # fils
    converted_to_invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoices.id"), nullable=True
    )

    @property
    def line_items(self):
        return LineItem.query.filter_by(
            document_type="quotation", document_id=self.id
        ).order_by(LineItem.sort_order).all()

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "subtotal_amount": self.subtotal_amount,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
            "converted_to_invoice_id": self.converted_to_invoice_id,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
