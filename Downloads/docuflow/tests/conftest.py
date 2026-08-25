"""
Test configuration.

Tests run against real PostgreSQL (not SQLite) to catch trigger behaviour,
UUID handling, and enum column issues that SQLite silently ignores.

Set TEST_DATABASE_URL in the environment before running:
  export TEST_DATABASE_URL=postgresql://docuflow:changeme@localhost:5432/docuflow_test

Run:
  pytest tests/ -v
"""
import os
import pytest
from app import create_app
from app.extensions import db as _db
from config import TestingConfig


class _TestConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://docuflow:changeme@localhost:5432/docuflow_test",
    )
    SECRET_KEY = "test-secret-key-not-for-production"
    JWT_SECRET_KEY = "test-jwt-secret-not-for-production"


@pytest.fixture(scope="session")
def app():
    _app = create_app(_TestConfig)
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def clean_db(app):
    """Roll back after each test for isolation."""
    with app.app_context():
        yield
        _db.session.rollback()
        # Truncate all tables except alembic version
        for table in reversed(_db.metadata.sorted_tables):
            if table.name != "alembic_version":
                _db.session.execute(table.delete())
        _db.session.commit()


def register_and_login(client, company_name="Test Co", email="test@example.com", password="P@ssw0rd!"):
    """Helper: register a company, log in, return auth header and IDs."""
    r = client.post("/api/auth/register", json={
        "company_name": company_name,
        "email": email,
        "password": password,
    })
    assert r.status_code == 201, r.get_json()
    data = r.get_json()
    company_id = data["company"]["id"]

    r2 = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200, r2.get_json()
    token = r2.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, company_id
