from flask import jsonify
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError


def error_response(code: str, message: str, status: int):
    return jsonify({"error": code, "message": message}), status


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return error_response("BAD_REQUEST", str(e), 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response("UNAUTHORIZED", "Authentication required", 401)

    @app.errorhandler(403)
    def forbidden(e):
        return error_response("FORBIDDEN", str(e), 403)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("NOT_FOUND", "Resource not found", 404)

    @app.errorhandler(413)
    def too_large(e):
        return error_response("PAYLOAD_TOO_LARGE", "File exceeds size limit", 413)

    @app.errorhandler(422)
    def unprocessable(e):
        return error_response("UNPROCESSABLE", str(e), 422)

    # Locked document — PermissionError raised by .ensure_editable()
    @app.errorhandler(PermissionError)
    def locked(e):
        return error_response("LOCKED", str(e), 423)

    @app.errorhandler(ValueError)
    def value_error(e):
        return error_response("INVALID_TRANSITION", str(e), 400)

    @app.errorhandler(JWTExtendedException)
    @app.errorhandler(PyJWTError)
    def jwt_error(e):
        return error_response("UNAUTHORIZED", str(e), 401)

    @app.errorhandler(429)
    def rate_limited(e):
        return error_response("RATE_LIMITED", "Too many requests", 429)

    @app.errorhandler(500)
    def internal(e):
        return error_response("INTERNAL_ERROR", "An unexpected error occurred", 500)

    # Security headers on every response
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )
        return response
