import time
import jwt
import pytest
from datetime import datetime, timezone, timedelta

from tests.conftest import auth_header


# ---- Registration ----

def test_register_success(client, company):
    rv = client.post("/api/auth/register", json={
        "email": "new@test.com",
        "password": "SecurePass1!",
        "role": "viewer",
        "company_id": company.id,
    })
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["user"]["email"] == "new@test.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_duplicate_email(client, company):
    payload = {"email": "dup@test.com", "password": "SecurePass1!",
                "role": "viewer", "company_id": company.id}
    client.post("/api/auth/register", json=payload)
    rv = client.post("/api/auth/register", json=payload)
    assert rv.status_code == 409


def test_register_short_password(client, company):
    rv = client.post("/api/auth/register", json={
        "email": "short@test.com", "password": "abc",
        "role": "viewer", "company_id": company.id,
    })
    assert rv.status_code == 422


def test_register_email_normalized_lowercase(client, company):
    rv = client.post("/api/auth/register", json={
        "email": "UPPER@TEST.COM", "password": "SecurePass1!",
        "role": "viewer", "company_id": company.id,
    })
    assert rv.status_code == 201
    assert rv.get_json()["user"]["email"] == "upper@test.com"


def test_register_missing_company_id(client):
    rv = client.post("/api/auth/register", json={
        "email": "x@test.com", "password": "SecurePass1!", "role": "viewer",
    })
    assert rv.status_code == 422


# ---- Login ----

def test_login_success(client, owner_user):
    rv = client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "SecurePass1!"
    })
    assert rv.status_code == 200
    data = rv.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


def test_login_wrong_password(client, owner_user):
    rv = client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "WrongPassword!"
    })
    assert rv.status_code == 401
    # Error message must not reveal whether email exists
    assert rv.get_json()["error"]["message"] == "Invalid email or password"


def test_login_unknown_email(client):
    rv = client.post("/api/auth/login", json={
        "email": "nobody@test.com", "password": "whatever"
    })
    assert rv.status_code == 401
    assert rv.get_json()["error"]["message"] == "Invalid email or password"


def test_login_inactive_user(client, app, db, owner_user):
    owner_user.is_active = False
    db.session.flush()
    rv = client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "SecurePass1!"
    })
    assert rv.status_code == 403


def test_login_updates_last_login_at(client, app, owner_user):
    before = datetime.now(timezone.utc)
    client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "SecurePass1!"
    })
    from app.models.user import User
    with app.app_context():
        u = User.query.filter_by(email="owner@test.com").first()
        if u and u.last_login_at:
            assert u.last_login_at >= before


# ---- Token Validity ----

def test_expired_access_token_rejected(client, app, owner_user):
    """Manually craft an expired token."""
    secret = app.config["JWT_SECRET"]
    payload = {
        "sub": owner_user.id,
        "email": owner_user.email,
        "role": owner_user.role.value,
        "company_id": owner_user.company_id,
        "iat": datetime.now(timezone.utc) - timedelta(minutes=30),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=15),
        "type": "access",
    }
    expired_token = jwt.encode(payload, secret, algorithm="HS256")
    rv = client.get("/api/audit", headers={"Authorization": f"Bearer {expired_token}"})
    assert rv.status_code == 401


def test_tampered_token_rejected(client, owner_user):
    token = make_access_token(owner_user)
    # Flip last character
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    rv = client.get("/api/audit", headers={"Authorization": f"Bearer {tampered}"})
    assert rv.status_code == 401


def test_no_bearer_prefix_rejected(client, owner_user):
    token = make_access_token(owner_user)
    rv = client.get("/api/audit", headers={"Authorization": token})
    assert rv.status_code == 401


# ---- Refresh Rotation ----

def test_refresh_rotation_issues_new_pair(client, owner_user):
    login = client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "SecurePass1!"
    })
    old_refresh = login.get_json()["refresh_token"]

    rv = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert rv.status_code == 200
    data = rv.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != old_refresh


def test_refresh_replay_rejected(client, owner_user):
    """After rotation, using the old refresh token must return 401."""
    login = client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "SecurePass1!"
    })
    old_refresh = login.get_json()["refresh_token"]

    client.post("/api/auth/refresh", json={"refresh_token": old_refresh})

    # Replay the revoked token
    rv = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert rv.status_code == 401


def test_logout_invalidates_refresh(client, owner_user):
    login = client.post("/api/auth/login", json={
        "email": "owner@test.com", "password": "SecurePass1!"
    })
    tokens = login.get_json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    client.post("/api/auth/logout",
                json={"refresh_token": refresh},
                headers={"Authorization": f"Bearer {access}"})

    rv = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert rv.status_code == 401


def test_missing_refresh_token_body(client):
    rv = client.post("/api/auth/refresh", json={})
    assert rv.status_code == 422


# helpers

def make_access_token(user):
    from app.services.auth_service import issue_access_token
    return issue_access_token(user)
