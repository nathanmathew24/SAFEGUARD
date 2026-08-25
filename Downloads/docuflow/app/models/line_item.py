from app.extensions import db


class LineItem(db.Model):
    __tablename__ = "line_items"

    id = db.Column(db.Integer, primary_key=True)
    # Polymorphic: one of these will be set
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=True)
    lpo_id = db.Column(db.Integer, db.ForeignKey("lpos.id"), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    delivery_note_id = db.Column(db.Integer, db.ForeignKey("delivery_notes.id"), nullable=True)
    credit_note_id = db.Column(db.Integer, db.ForeignKey("credit_notes.id"), nullable=True)
    debit_note_id = db.Column(db.Integer, db.ForeignKey("debit_notes.id"), nullable=True)

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(20, 4), nullable=False)
    unit_price = db.Column(db.Numeric(20, 4), nullable=False)
    unit_of_measure = db.Column(db.String(50), nullable=True)
    line_total = db.Column(db.Numeric(20, 4), nullable=False)

    product = db.relationship("Product", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "description": self.description,
            "quantity": float(self.quantity),
            "unit_price": float(self.unit_price),
            "unit_of_measure": self.unit_of_measure,
            "line_total": float(self.line_total),
        }
