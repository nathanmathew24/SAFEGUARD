import os
import pytest

# Set env vars before any app import
os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "postgresql://docflow:password@localhost:5432/docflow_test"))
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-not-real")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-bytes-ok!")
os.environ.setdefault("FLASK_ENV", "testing")

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from config import TestingConfig  # noqa: E402


@pytest.fixture(scope="session")
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def db_cleanup(app):
    """Wrap each test in a transaction and roll back after."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection
        yield
        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def company(app, db):
    from app.models.company import Company
    from datetime import datetime, timezone
    c = Company(name="Test Trading LLC", trade_license_no="TL-001", trn="100123456700003",
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db.session.add(c)
    db.session.flush()
    return c


@pytest.fixture
def owner_user(app, db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(company_id=company.id, email="owner@test.com",
             password_hash=hash_password("SecurePass1!"),
             role=UserRole.owner,
             created_at=datetime.now(timezone.utc),
             updated_at=datetime.now(timezone.utc))
    db.session.add(u)
    db.session.flush()
    return u


@pytest.fixture
def finance_user(app, db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(company_id=company.id, email="finance@test.com",
             password_hash=hash_password("SecurePass1!"),
             role=UserRole.finance_manager,
             created_at=datetime.now(timezone.utc),
             updated_at=datetime.now(timezone.utc))
    db.session.add(u)
    db.session.flush()
    return u


@pytest.fixture
def ops_user(app, db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(company_id=company.id, email="ops@test.com",
             password_hash=hash_password("SecurePass1!"),
             role=UserRole.operations_staff,
             created_at=datetime.now(timezone.utc),
             updated_at=datetime.now(timezone.utc))
    db.session.add(u)
    db.session.flush()
    return u


@pytest.fixture
def viewer_user(app, db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(company_id=company.id, email="viewer@test.com",
             password_hash=hash_password("SecurePass1!"),
             role=UserRole.viewer,
             created_at=datetime.now(timezone.utc),
             updated_at=datetime.now(timezone.utc))
    db.session.add(u)
    db.session.flush()
    return u


def make_access_token(user):
    from app.services.auth_service import issue_access_token
    return issue_access_token(user)


def auth_header(user):
    return {"Authorization": f"Bearer {make_access_token(user)}"}
