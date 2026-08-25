import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.models.user import User
from app.models.company import Company
from app.models.audit_log import AuditLog


class AuthError(Exception):
    pass


def register_company(company_name: str, email: str, password: str) -> tuple[Company, User]:
    if User.query.filter_by(email=email).first():
        raise AuthError("Email already registered")

    company = Company(name=company_name)
    db.session.add(company)
    db.session.flush()  # get company.id before adding user

    user = User(company_id=company.id, email=email, role="owner")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return company, user


def login(email: str, password: str, ip: str) -> dict:
    user = User.query.filter_by(email=email, is_active=True).first()
    if user is None or not user.check_password(password):
        raise AuthError("Invalid credentials")

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"company_id": user.company_id},
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"company_id": user.company_id},
    )

    log = AuditLog(
        company_id=user.company_id,
        user_id=user.id,
        action="LOGIN",
        table_name="users",
        record_id=user.id,
        ip_address=ip,
    )
    db.session.add(log)
    db.session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }


def refresh_tokens(user_id: int, company_id: int) -> dict:
    access_token = create_access_token(
        identity=str(user_id),
        additional_claims={"company_id": company_id},
    )
    return {"access_token": access_token}


def initiate_password_reset(email: str) -> str | None:
    user = User.query.filter_by(email=email, is_active=True).first()
    if user is None:
        return None  # don't reveal whether email exists
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=2)
    db.session.commit()
    return token


def complete_password_reset(token: str, new_password: str):
    user = User.query.filter_by(password_reset_token=token).first()
    if user is None:
        raise AuthError("Invalid or expired reset token")
    if user.password_reset_expires < datetime.now(timezone.utc):
        raise AuthError("Reset token has expired")
    user.set_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.session.commit()
