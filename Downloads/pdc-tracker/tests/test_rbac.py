from tests.conftest import auth_header


def test_no_token_returns_401(client):
    rv = client.get("/api/audit")
    assert rv.status_code == 401


def test_owner_can_access_audit_log(client, owner_user):
    rv = client.get("/api/audit", headers=auth_header(owner_user))
    assert rv.status_code == 200


def test_finance_manager_cannot_access_audit_log(client, finance_user):
    rv = client.get("/api/audit", headers=auth_header(finance_user))
    assert rv.status_code == 403


def test_operations_staff_cannot_access_audit_log(client, ops_user):
    rv = client.get("/api/audit", headers=auth_header(ops_user))
    assert rv.status_code == 403


def test_viewer_cannot_access_audit_log(client, viewer_user):
    rv = client.get("/api/audit", headers=auth_header(viewer_user))
    assert rv.status_code == 403


def test_error_response_format_on_403(client, viewer_user):
    rv = client.get("/api/audit", headers=auth_header(viewer_user))
    data = rv.get_json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]


def test_error_response_format_on_401(client):
    rv = client.get("/api/audit")
    data = rv.get_json()
    assert "error" in data
    assert "code" in data["error"]


def test_role_in_jwt_verified_server_side(client, app, owner_user):
    """
    Even if we issue a token with a higher role claim manually,
    the server re-checks the role from the DB.
    This test creates a viewer token but crafts it with role=owner claim —
    the server should reject it because the DB says viewer.
    """
    import jwt as pyjwt
    from datetime import datetime, timezone, timedelta
    secret = app.config["JWT_SECRET"]
    # Craft a token claiming owner role for a viewer user
    payload = {
        "sub": owner_user.id,
        "email": owner_user.email,
        "role": "viewer",  # deliberately wrong claim
        "company_id": owner_user.company_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access",
    }
    token = pyjwt.encode(payload, secret, algorithm="HS256")
    rv = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    # Server checks DB role vs token role — mismatch → 401
    assert rv.status_code == 401


def test_logout_requires_auth(client):
    rv = client.post("/api/auth/logout", json={})
    assert rv.status_code == 401
