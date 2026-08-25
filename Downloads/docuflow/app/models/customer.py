from datetime import datetime, timezone
from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    trn = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    whatsapp_number = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    company = db.relationship("Company", back_populates="customers")

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "trn": self.trn,
            "email": self.email,
            "whatsapp_number": self.whatsapp_number,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
