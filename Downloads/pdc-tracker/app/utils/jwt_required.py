from functools import wraps
from flask import request, g
from app.utils.errors import error_response


def jwt_required(f):
    """
    Decorator: extracts Bearer token from Authorization header,
    verifies it, sets g.current_user. Returns 401 on any failure.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("UNAUTHORIZED", "Bearer token required", 401)

        token = auth_header[len("Bearer "):]

        from app.services.auth_service import get_user_from_token
        user = get_user_from_token(token)
        if user is None:
            return error_response("UNAUTHORIZED", "Invalid or expired token", 401)

        g.current_user = user
        return f(*args, **kwargs)
    return wrapped
