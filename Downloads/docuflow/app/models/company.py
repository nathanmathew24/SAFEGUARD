from datetime import datetime, timezone
from app.extensions import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    trade_license_number = db.Column(db.String(100), unique=True, nullable=True)
    trn = db.Column(db.String(20), unique=True, nullable=True)
    address = db.Column(db.Text, nullable=True)

    subscription_tier = db.Column(
        db.Enum("starter", "growth", "pro", name="subscription_tier_enum"),
        nullable=False, default="starter", server_default="starter",
    )
    subscription_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")

    # Billing gate for the WhatsApp paid add-on — checked at every WhatsApp call site
    whatsapp_addon_enabled = db.Column(db.Boolean, nullable=False, default=False, server_default="false")

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    users = db.relationship("User", back_populates="company", lazy="dynamic")
    customers = db.relationship("Customer", back_populates="company", lazy="dynamic")
    products = db.relationship("Product", back_populates="company", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "trade_license_number": self.trade_license_number,
            "trn": self.trn,
            "address": self.address,
            "subscription_tier": self.subscription_tier,
            "subscription_active": self.subscription_active,
            "whatsapp_addon_enabled": self.whatsapp_addon_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
