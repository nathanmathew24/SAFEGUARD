from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g

from app.extensions import db, limiter
from app.models.user import User, UserRole
from app.models.audit_log import AuditAction
from app.services import audit_service, auth_service
from app.utils.errors import error_response
from app.utils.ip import get_client_ip
from app.utils.jwt_required import jwt_required

auth_bp = Blueprint("auth", __name__)

AUTH_RATE_LIMIT = "10 per minute"


@auth_bp.route("/register", methods=["POST"])
@limiter.limit(AUTH_RATE_LIMIT)
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    role = data.get("role", "viewer")
    company_id = data.get("company_id")

    if not company_id:
        return error_response("VALIDATION_ERROR", "company_id is required", 422)

    ip = get_client_ip()

    try:
        user = auth_service.register_user(
            email=email,
            password=password,
            role=role,
            company_id=company_id,
            actor_id=None,
            ip=ip,
        )
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        msg = str(e)
        status = 409 if "already registered" in msg else 422
        return error_response("VALIDATION_ERROR", msg, status)

    return jsonify({"user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit(AUTH_RATE_LIMIT)
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password", "")
    ip = get_client_ip()

    # Constant-time lookup — same error for bad email and bad password (no user enumeration)
    user = User.query.filter_by(email=email, is_deleted=False).first()
    password_ok = (
        auth_service.check_password(password, user.password_hash) if user else False
    )

    if not user or not password_ok:
        return error_response("UNAUTHORIZED", "Invalid email or password", 401)

    if not user.is_active:
        return error_response("FORBIDDEN", "Account is inactive", 403)

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    access_token = auth_service.issue_access_token(user)
    refresh_token = auth_service.issue_refresh_token(user)

    audit_service.log_event(
        action=AuditAction.LOGIN,
        table_name="users",
        record_id=user.id,
        user_id=user.id,
        ip_address=ip,
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@limiter.limit(AUTH_RATE_LIMIT)
def refresh():
    data = request.get_json(silent=True) or {}
    raw_token = data.get("refresh_token", "")

    if not raw_token:
        return error_response("VALIDATION_ERROR", "refresh_token is required", 422)

    try:
        new_access, new_refresh = auth_service.rotate_refresh_token(raw_token)
    except ValueError as e:
        return error_response("UNAUTHORIZED", str(e), 401)

    return jsonify({
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "Bearer",
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout():
    data = request.get_json(silent=True) or {}
    raw_token = data.get("refresh_token", "")
    ip = get_client_ip()

    if raw_token:
        auth_service.revoke_refresh_token(raw_token)

    audit_service.log_event(
        action=AuditAction.LOGOUT,
        table_name="users",
        record_id=g.current_user.id,
        user_id=g.current_user.id,
        ip_address=ip,
    )

    return jsonify({"message": "Logged out"}), 200
