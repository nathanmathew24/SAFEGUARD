from app.extensions import db
from app.models.document_base import LockableMixin


class LPO(LockableMixin, db.Model):
    __tablename__ = "lpos"

    id = db.Column(db.Integer, primary_key=True)
    lpo_number = db.Column(db.String(50), nullable=False)
    # quote_id is nullable — LPO can be created directly without a prior Quote
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_trn = db.Column(db.String(50), nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    delivery_address = db.Column(db.Text, nullable=True)

    quote = db.relationship("Quote", back_populates="lpos")
    customer = db.relationship("Customer", lazy="joined")
    line_items = db.relationship("LineItem", foreign_keys="LineItem.lpo_id",
                                 backref="lpo", lazy="select", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", back_populates="lpo", lazy="dynamic")

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "lpo_number": self.lpo_number,
            "quote_id": self.quote_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_trn": self.customer_trn,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "delivery_address": self.delivery_address,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
