from functools import wraps
from flask import g
from app.utils.errors import error_response
from app.models.user import UserRole


def require_role(*roles: UserRole):
    """
    Decorator that enforces both JWT authentication and role authorization.
    Must be used AFTER @jwt_required (which sets g.current_user).
    Usage: @require_role(UserRole.owner, UserRole.finance_manager)
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not hasattr(g, "current_user") or g.current_user is None:
                return error_response("UNAUTHORIZED", "Authentication required", 401)

            if g.current_user.role not in roles:
                return error_response(
                    "FORBIDDEN",
                    f"Role '{g.current_user.role.value}' is not permitted to perform this action",
                    403,
                )
            return f(*args, **kwargs)
        return wrapped
    return decorator
