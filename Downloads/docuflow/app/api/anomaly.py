from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from app.extensions import db
from app.models.anomaly_flag import AnomalyFlag
from app.utils.auth import current_user_id, current_company_id
from app.utils.scoping import get_scoped_or_404

anomaly_bp = Blueprint("anomaly", __name__, url_prefix="/api/anomalies")


@anomaly_bp.get("")
@jwt_required()
def list_anomalies():
    cid = current_company_id()
    resolved = request.args.get("resolved", "false").lower() == "true"
    flags = (
        AnomalyFlag.query
        .filter_by(company_id=cid, resolved=resolved)
        .order_by(AnomalyFlag.created_at.desc())
        .all()
    )
    return jsonify([f.to_dict() for f in flags])


@anomaly_bp.post("/<int:flag_id>/resolve")
@jwt_required()
def resolve_anomaly(flag_id):
    flag = get_scoped_or_404(AnomalyFlag, flag_id, current_company_id())
    flag.resolved = True
    flag.resolved_by = current_user_id()
    flag.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(flag.to_dict())
