from datetime import datetime, timezone
from app.extensions import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    trade_license_no = db.Column(db.String(100), unique=True, nullable=True)
    trn = db.Column(db.String(20), unique=True, nullable=True)  # UAE Tax Registration Number
    address = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Soft delete — financial records are never hard-deleted
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    users = db.relationship("User", foreign_keys="User.company_id", back_populates="company")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "trade_license_no": self.trade_license_no,
            "trn": self.trn,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
