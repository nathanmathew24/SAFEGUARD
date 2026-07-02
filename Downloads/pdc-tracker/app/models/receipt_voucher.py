from app.extensions import db
from app.models.document_base import DocumentMixin


class ReceiptVoucher(DocumentMixin, db.Model):
    __tablename__ = "receipt_vouchers"

    id = db.Column(db.Integer, primary_key=True)
    received_from = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # fils
    payment_method = db.Column(
        db.Enum("cash", "bank_transfer", "cheque", name="rvpaymentmethod"),
        nullable=False,
    )
    linked_invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    bank_reference = db.Column(db.String(100), nullable=True)

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "received_from": self.received_from,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "linked_invoice_id": self.linked_invoice_id,
            "bank_reference": self.bank_reference,
        })
        return d
