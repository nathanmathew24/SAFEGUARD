import sys
from datetime import datetime, timezone

from app.extensions import db
from app.models.audit_log import AuditLog, AuditAction


def log_event(
    action: AuditAction,
    table_name: str,
    record_id: int | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Append an entry to the audit log. This is a write-only operation.
    If the write fails we raise — audit failures must never be silently swallowed.
    """
    entry = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        user_id=user_id,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    try:
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f"[AUDIT CRITICAL] Failed to write audit log: {exc}", file=sys.stderr)
        raise
