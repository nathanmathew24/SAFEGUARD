import enum
from datetime import datetime, timezone
from app.extensions import db


class AuditAction(enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    VOID = "VOID"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False, index=True)
    record_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.Enum(AuditAction), nullable=False, index=True)

    # JSON snapshots — nullable for LOGIN/LOGOUT events
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # supports IPv6
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False,
                          default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "action": self.action.value,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
        }
