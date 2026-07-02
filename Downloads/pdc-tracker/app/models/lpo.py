from app.extensions import db
from app.models.document_base import DocumentMixin
from app.models.line_item import LineItem


class LPO(DocumentMixin, db.Model):
    __tablename__ = "lpos"

    id = db.Column(db.Integer, primary_key=True)
    delivery_expected_date = db.Column(db.Date, nullable=True)
    subtotal_amount = db.Column(db.Integer, nullable=False, default=0)  # fils
    total_amount = db.Column(db.Integer, nullable=False, default=0)     # fils

    @property
    def line_items(self):
        return LineItem.query.filter_by(
            document_type="lpo", document_id=self.id
        ).order_by(LineItem.sort_order).all()

    def to_dict(self, include_lines=True):
        d = self.base_dict()
        d.update({
            "delivery_expected_date": (
                self.delivery_expected_date.isoformat()
                if self.delivery_expected_date else None
            ),
            "subtotal_amount": self.subtotal_amount,
            "total_amount": self.total_amount,
        })
        if include_lines:
            d["line_items"] = [li.to_dict() for li in self.line_items]
        return d
