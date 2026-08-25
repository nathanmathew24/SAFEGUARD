from app.extensions import db
from app.models.document_base import LockableMixin


class Invoice(LockableMixin, db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False)
    # Both nullable: invoice can come from an LPO, from a Quote, or be created directly
    lpo_id = db.Column(db.Integer, db.ForeignKey("lpos.id"), nullable=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_trn = db.Column(db.String(50), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)

    # UAE FTA e-invoicing groundwork (PINT AE representative subset — not a full 51-field mapping)
    buyer_vat_number = db.Column(db.String(20), nullable=True)
    supply_type = db.Column(db.String(10), nullable=True, default="B2B")
    invoice_type_code = db.Column(db.String(10), nullable=True, default="388")

    lpo = db.relationship("LPO", back_populates="invoices")
    quote = db.relationship("Quote", back_populates="invoices")
    customer = db.relationship("Customer", lazy="joined")
    line_items = db.relationship("LineItem", foreign_keys="LineItem.invoice_id",
                                 backref="invoice", lazy="select", cascade="all, delete-orphan")
    delivery_notes = db.relationship("DeliveryNote", back_populates="invoice", lazy="dynamic")
    credit_notes = db.relationship("CreditNote", back_populates="invoice", lazy="dynamic")
    debit_notes = db.relationship("DebitNote", back_populates="invoice", lazy="dynamic")
    pdcs = db.relationship("PDC", back_populates="invoice", lazy="dynamic")

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "invoice_number": self.invoice_number,
            "lpo_id": self.lpo_id,
            "quote_id": self.quote_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_trn": self.customer_trn,
            "payment_terms": self.payment_terms,
            "buyer_vat_number": self.buyer_vat_number,
            "supply_type": self.supply_type,
            "invoice_type_code": self.invoice_type_code,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
