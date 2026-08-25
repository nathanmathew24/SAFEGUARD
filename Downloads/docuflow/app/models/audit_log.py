from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)    # e.g. FINALIZE, CREATE, UPDATE
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    detail = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "action": self.action,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "ip_address": self.ip_address,
            "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
