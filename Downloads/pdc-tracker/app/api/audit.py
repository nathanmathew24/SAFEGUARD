from flask import Blueprint, jsonify, request

from app.models.audit_log import AuditLog
from app.models.user import UserRole
from app.utils.jwt_required import jwt_required
from app.utils.rbac import require_role

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/audit", methods=["GET"])
@jwt_required
@require_role(UserRole.owner)
def list_audit_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)

    pagination = (
        AuditLog.query
        .order_by(AuditLog.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "audit_logs": [entry.to_dict() for entry in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }), 200
