from flask import jsonify


def error_response(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return error_response("BAD_REQUEST", "Bad request", 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response("UNAUTHORIZED", "Authentication required", 401)

    @app.errorhandler(403)
    def forbidden(e):
        return error_response("FORBIDDEN", "Insufficient permissions", 403)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("NOT_FOUND", "Resource not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("METHOD_NOT_ALLOWED", "Method not allowed", 405)

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return error_response("RATE_LIMITED", "Too many requests", 429)

    @app.errorhandler(500)
    def internal_error(e):
        return error_response("INTERNAL_ERROR", "An internal error occurred", 500)
