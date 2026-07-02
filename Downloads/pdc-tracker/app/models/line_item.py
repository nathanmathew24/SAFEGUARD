from app.extensions import db


class LineItem(db.Model):
    __tablename__ = "line_items"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)          # whole units
    unit_price = db.Column(db.Integer, nullable=False)        # fils (AED × 100)
    discount_amount = db.Column(db.Integer, nullable=False, default=0)   # fils
    tax_rate_bp = db.Column(db.Integer, nullable=False, default=500)     # basis points (500=5%)
    line_total = db.Column(db.Integer, nullable=False)        # fils, computed on write
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.Index("ix_line_items_doc", "document_type", "document_id"),
    )

    @staticmethod
    def compute_total(quantity: int, unit_price: int,
                      discount_amount: int, tax_rate_bp: int) -> int:
        subtotal = quantity * unit_price - discount_amount
        tax = subtotal * tax_rate_bp // 10000
        return subtotal + tax

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount_amount": self.discount_amount,
            "tax_rate_bp": self.tax_rate_bp,
            "line_total": self.line_total,
            "sort_order": self.sort_order,
        }
