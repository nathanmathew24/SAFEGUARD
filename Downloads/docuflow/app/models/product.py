from datetime import datetime, timezone
from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    sku = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit_price = db.Column(db.Numeric(20, 4), nullable=False, default=0)
    unit_of_measure = db.Column(db.String(50), nullable=False, default="EA")
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("company_id", "sku", name="uq_product_company_sku"),
    )

    company = db.relationship("Company", back_populates="products")

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0,
            "unit_of_measure": self.unit_of_measure,
            "is_active": self.is_active,
        }
