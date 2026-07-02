from app.extensions import db
from app.models.document_base import DocumentMixin
from app.models.line_item import LineItem


class PurchaseInvoice(DocumentMixin, db.Model):
    __tablename__ = "purchase_invoices"

    id = db.Column(db.Integer, primary_key=True)
    supplier_invoice_number = db.Column(db.String(100), nullable=True)
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
            document_type="purchase_invoice", document_id=self.id
        ).order_by(LineItem.sort_order).all()

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "supplier_invoice_number": self.supplier_invoice_number,
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
