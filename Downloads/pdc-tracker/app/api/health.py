from datetime import datetime, timezone
from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    db_status = "ok"
    http_status = 200
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        http_status = 503

    return jsonify({
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), http_status
