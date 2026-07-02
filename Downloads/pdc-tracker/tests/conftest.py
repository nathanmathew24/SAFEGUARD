import os
import pytest

# Set env vars before any app import
os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "postgresql://docflow:password@localhost:5432/docflow_test"))
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-not-real")
os.environ.setdefault("ENCRYPTION_KEY", "m-lW27FJeq-X-JRYz80HIdvVHyGb_19X7X05P_xLES4=")  # valid Fernet key
os.environ.setdefault("FLASK_ENV", "testing")

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from config import TestingConfig  # noqa: E402


@pytest.fixture(scope="session")
def app():
    """Session-scoped app with a single pushed app context."""
    application = create_app(TestingConfig)
    ctx = application.app_context()
    ctx.push()
    # Drop everything first so enum types and tables are always recreated clean
    _db.session.execute(_db.text("""
        DROP TABLE IF EXISTS
            extraction_logs, extraction_reviews, uploaded_files,
            line_items, receipt_vouchers, pdcs, delivery_notes,
            debit_notes, credit_notes, quotations, lpos,
            purchase_invoices, invoices, document_sequences,
            audit_logs, refresh_tokens, users, companies
        CASCADE
    """))
    _db.session.execute(_db.text(
        "DROP TYPE IF EXISTS auditaction, userrole, docstatus, invoicetype, "
        "paymentmethod, paymentstatus, pdcstatus, rvpaymentmethod, "
        "extractionstatus, reviewstatus CASCADE"
    ))
    _db.session.commit()
    _db.create_all()
    yield application
    # Raw SQL teardown — CASCADE handles FK dependencies
    _db.session.execute(_db.text("""
        DROP TABLE IF EXISTS
            extraction_logs, extraction_reviews, uploaded_files,
            line_items, receipt_vouchers, pdcs, delivery_notes,
            debit_notes, credit_notes, quotations, lpos,
            purchase_invoices, invoices, document_sequences,
            audit_logs, refresh_tokens, users, companies
        CASCADE
    """))
    _db.session.execute(_db.text(
        "DROP TYPE IF EXISTS auditaction, userrole, docstatus, invoicetype, "
        "paymentmethod, paymentstatus, pdcstatus, rvpaymentmethod, "
        "extractionstatus, reviewstatus CASCADE"
    ))
    _db.session.commit()
    ctx.pop()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Yield the db instance — no new app context needed (session context is active)."""
    yield _db


@pytest.fixture(scope="function", autouse=True)
def db_cleanup(app):
    """Truncate all tables after each test for clean isolation."""
    yield
    _db.session.remove()
    _db.session.execute(_db.text("""
        TRUNCATE TABLE
            extraction_logs, extraction_reviews, uploaded_files,
            line_items, receipt_vouchers, pdcs, delivery_notes,
            debit_notes, credit_notes, quotations, lpos,
            purchase_invoices, invoices, document_sequences,
            audit_logs, refresh_tokens, users, companies
        RESTART IDENTITY CASCADE
    """))
    _db.session.commit()


@pytest.fixture(scope="function")
def company(db):
    from app.models.company import Company
    from datetime import datetime, timezone
    c = Company(
        name="Test Trading LLC",
        trade_license_no="TL-001",
        trn="100123456700003",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture(scope="function")
def owner_user(db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(
        company_id=company.id,
        email="owner@test.com",
        password_hash=hash_password("SecurePass1!"),
        role=UserRole.owner,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture(scope="function")
def finance_user(db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(
        company_id=company.id,
        email="finance@test.com",
        password_hash=hash_password("SecurePass1!"),
        role=UserRole.finance_manager,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture(scope="function")
def ops_user(db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(
        company_id=company.id,
        email="ops@test.com",
        password_hash=hash_password("SecurePass1!"),
        role=UserRole.operations_staff,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture(scope="function")
def viewer_user(db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from datetime import datetime, timezone
    u = User(
        company_id=company.id,
        email="viewer@test.com",
        password_hash=hash_password("SecurePass1!"),
        role=UserRole.viewer,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(u)
    db.session.commit()
    return u


def make_access_token(user):
    from app.services.auth_service import issue_access_token
    return issue_access_token(user)


def auth_header(user):
    return {"Authorization": f"Bearer {make_access_token(user)}"}
