from app.extensions import db
from app.models.document_base import LockableMixin


class Quote(LockableMixin, db.Model):
    __tablename__ = "quotes"

    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_trn = db.Column(db.String(50), nullable=True)
    valid_until = db.Column(db.Date, nullable=True)

    customer = db.relationship("Customer", lazy="joined")
    line_items = db.relationship("LineItem", foreign_keys="LineItem.quote_id",
                                 backref="quote", lazy="select", cascade="all, delete-orphan")
    lpos = db.relationship("LPO", back_populates="quote", lazy="dynamic")
    invoices = db.relationship("Invoice", back_populates="quote", lazy="dynamic")

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "quote_number": self.quote_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_trn": self.customer_trn,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
