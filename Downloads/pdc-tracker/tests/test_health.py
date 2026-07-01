from unittest.mock import patch
from sqlalchemy.exc import OperationalError


def test_health_ok(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert "timestamp" in data


def test_health_no_auth_required(client):
    """Health endpoint must be publicly accessible."""
    rv = client.get("/health")
    assert rv.status_code != 401


def test_health_db_down(client, app):
    """When DB is unreachable, return 503 with degraded status."""
    with patch("app.api.health.db") as mock_db:
        mock_db.session.execute.side_effect = OperationalError("conn", {}, Exception("down"))
        rv = client.get("/health")
    assert rv.status_code == 503
    data = rv.get_json()
    assert data["status"] == "degraded"
    assert data["db"] == "error"
