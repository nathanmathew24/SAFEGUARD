from app.extensions import db
from app.models.document_base import DocumentMixin
from app.models.line_item import LineItem


class Invoice(DocumentMixin, db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_type = db.Column(
        db.Enum("standard", "proforma", "tax_invoice", name="invoicetype"),
        nullable=False,
        default="tax_invoice",
        server_default="tax_invoice",
    )
    subtotal_amount = db.Column(db.Integer, nullable=False, default=0)  # fils
    tax_amount = db.Column(db.Integer, nullable=False, default=0)       # fils
    total_amount = db.Column(db.Integer, nullable=False, default=0)     # fils
    payment_method = db.Column(
        db.Enum("cash", "bank_transfer", "cheque", "pdc", name="paymentmethod"),
        nullable=True,
    )
    payment_status = db.Column(
        db.Enum("unpaid", "partial", "paid", name="paymentstatus"),
        nullable=False,
        default="unpaid",
        server_default="unpaid",
    )
    amount_paid = db.Column(db.Integer, nullable=False, default=0)  # fils

    @property
    def line_items(self):
        return LineItem.query.filter_by(
            document_type="invoice", document_id=self.id
        ).order_by(LineItem.sort_order).all()

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "invoice_type": self.invoice_type,
            "subtotal_amount": self.subtotal_amount,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "amount_paid": self.amount_paid,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
