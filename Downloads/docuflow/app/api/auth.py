from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import limiter
from app.services import auth_service
from app.utils.auth import current_user_id, current_company_id
from app.utils.errors import error_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ("company_name", "email", "password")
    if not all(data.get(k) for k in required):
        return error_response("MISSING_FIELDS", f"Required: {', '.join(required)}", 400)

    try:
        company, user = auth_service.register_company(
            data["company_name"], data["email"], data["password"]
        )
    except auth_service.AuthError as exc:
        return error_response("REGISTRATION_FAILED", str(exc), 409)

    return jsonify({"company": company.to_dict(), "user": user.to_dict()}), 201


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    if not data.get("email") or not data.get("password"):
        return error_response("MISSING_FIELDS", "email and password required", 400)

    try:
        result = auth_service.login(
            data["email"], data["password"],
            ip=request.remote_addr or ""
        )
    except auth_service.AuthError as exc:
        return error_response("INVALID_CREDENTIALS", str(exc), 401)

    return jsonify(result)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    claims = get_jwt()
    tokens = auth_service.refresh_tokens(current_user_id(), int(claims["company_id"]))
    return jsonify(tokens)


@auth_bp.post("/password-reset/request")
@limiter.limit("5 per minute")
def request_password_reset():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    token = auth_service.initiate_password_reset(email)
    if token:
        from app.services.email_service import send_email
        try:
            send_email(
                email,
                "DocuFlow: password reset",
                f"<p>Your password reset token: <code>{token}</code> (expires in 2 hours)</p>",
                f"Your password reset token: {token} (expires in 2 hours)",
            )
        except Exception:
            pass  # don't reveal failures
    # Always 200 — don't reveal whether the email exists
    return jsonify({"message": "If that email is registered, a reset link has been sent."})


@auth_bp.post("/password-reset/confirm")
def confirm_password_reset():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    new_password = data.get("new_password", "")
    if not token or not new_password:
        return error_response("MISSING_FIELDS", "token and new_password required", 400)

    try:
        auth_service.complete_password_reset(token, new_password)
    except auth_service.AuthError as exc:
        return error_response("RESET_FAILED", str(exc), 400)

    return jsonify({"message": "Password updated successfully"})
