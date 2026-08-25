"""
JWT identity helpers.

Flask-JWT-Extended requires `sub` to be a plain string.
We store user_id there and company_id in additional_claims.

All routes use current_user_id() / current_company_id() — never call
get_jwt_identity() or get_jwt() directly in route code.
"""
import uuid
from flask_jwt_extended import get_jwt_identity, get_jwt


def current_user_id() -> int:
    return int(get_jwt_identity())


def current_company_id() -> int:
    return int(get_jwt()["company_id"])
