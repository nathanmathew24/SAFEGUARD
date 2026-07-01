import hashlib
import os
import secrets
from datetime import datetime, timezone

import jwt
from flask import current_app

from app.extensions import db, bcrypt
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.models.audit_log import AuditAction
from app.services import audit_service


# ---------- Password ----------

def hash_password(plaintext: str) -> str:
    return bcrypt.generate_password_hash(plaintext).decode("utf-8")


def check_password(plaintext: str, hashed: str) -> bool:
    return bcrypt.check_password_hash(hashed, plaintext)


# ---------- JWT ----------

def _jwt_secret() -> str:
    return current_app.config["JWT_SECRET"]


def issue_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    expires = now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "company_id": user.company_id,
        "iat": now,
        "exp": expires,
        "type": "access",
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Decode and verify. Raises jwt.PyJWTError on any failure."""
    payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"],
                         options={"require": ["sub", "exp", "type"]})
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


# ---------- Refresh Tokens ----------

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def issue_refresh_token(user: User) -> str:
    raw = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw)
    expires_at = datetime.now(timezone.utc) + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]

    rt = RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.session.add(rt)
    db.session.commit()
    return raw


def rotate_refresh_token(raw_token: str) -> tuple[str, str]:
    """
    Validate the incoming refresh token, revoke it, issue a new pair.
    Returns (new_access_token, new_refresh_token).
    Raises ValueError on any invalid/expired/revoked token.
    """
    token_hash = _hash_token(raw_token)

    # Select-for-update prevents race condition on concurrent rotation attempts
    rt = (
        RefreshToken.query
        .filter_by(token_hash=token_hash)
        .with_for_update()
        .first()
    )

    if rt is None:
        raise ValueError("Invalid refresh token")
    if not rt.is_valid:
        raise ValueError("Refresh token is expired or revoked")

    user = rt.user
    if not user.is_active or user.is_deleted:
        raise ValueError("User account is inactive")

    # Revoke old token
    rt.revoke()

    # Issue new pair
    new_raw_refresh = secrets.token_urlsafe(48)
    new_hash = _hash_token(new_raw_refresh)
    expires_at = datetime.now(timezone.utc) + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    new_rt = RefreshToken(user_id=user.id, token_hash=new_hash, expires_at=expires_at)
    db.session.add(new_rt)
    db.session.flush()  # get new_rt.id

    rt.replaced_by = new_rt.id
    db.session.commit()

    new_access = issue_access_token(user)
    return new_access, new_raw_refresh


def revoke_refresh_token(raw_token: str) -> None:
    token_hash = _hash_token(raw_token)
    rt = RefreshToken.query.filter_by(token_hash=token_hash).first()
    if rt and rt.revoked_at is None:
        rt.revoke()
        db.session.commit()


# ---------- JWT middleware helper ----------

def get_user_from_token(token: str) -> User | None:
    """Decode access token and return the User, or None if invalid."""
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        return None

    user = db.session.get(User, payload["sub"])
    if user is None or not user.is_active or user.is_deleted:
        return None
    # Verify role in DB matches token claim (token may be stale after role change)
    if user.role.value != payload.get("role"):
        return None
    return user


# ---------- Registration ----------

PASSWORD_MIN = 8
PASSWORD_MAX = 128
EMAIL_MAX = 254


def validate_registration_input(email: str, password: str) -> list[str]:
    errors = []
    if not email or len(email) > EMAIL_MAX or "@" not in email:
        errors.append("Valid email is required (max 254 chars)")
    if not password or len(password) < PASSWORD_MIN:
        errors.append(f"Password must be at least {PASSWORD_MIN} characters")
    if len(password) > PASSWORD_MAX:
        errors.append(f"Password must be at most {PASSWORD_MAX} characters")
    return errors


def register_user(email: str, password: str, role: str, company_id: int,
                  actor_id: int | None, ip: str) -> User:
    """Create user, hash password, write audit log. Raises ValueError on duplicate."""
    email = email.lower().strip()
    errors = validate_registration_input(email, password)
    if errors:
        raise ValueError(errors[0])

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise ValueError("Email already registered")

    try:
        role_enum = UserRole[role]
    except KeyError:
        raise ValueError(f"Invalid role '{role}'")

    pw_hash = hash_password(password)
    user = User(
        company_id=company_id,
        email=email,
        password_hash=pw_hash,
        role=role_enum,
    )
    db.session.add(user)
    db.session.flush()

    audit_service.log_event(
        action=AuditAction.CREATE,
        table_name="users",
        record_id=user.id,
        new_values={"email": user.email, "role": user.role.value},
        user_id=actor_id,
        ip_address=ip,
    )
    return user
