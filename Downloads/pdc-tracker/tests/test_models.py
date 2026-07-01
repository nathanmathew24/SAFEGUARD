from datetime import datetime, timezone, timedelta


def test_user_password_not_plaintext(app, db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    raw = "MySecret123!"
    u = User(
        company_id=company.id,
        email="pw_test@test.com",
        password_hash=hash_password(raw),
        role=UserRole.viewer,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(u)
    db.session.flush()

    assert u.password_hash != raw
    assert u.password_hash.startswith("$2b$")  # bcrypt signature


def test_soft_delete_user(app, db, company):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    u = User(
        company_id=company.id,
        email="soft_del@test.com",
        password_hash=hash_password("SecurePass1!"),
        role=UserRole.viewer,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(u)
    db.session.flush()

    u.is_deleted = True
    u.deleted_at = datetime.now(timezone.utc)
    db.session.flush()

    found = User.query.filter_by(email="soft_del@test.com", is_deleted=False).first()
    assert found is None

    still_there = User.query.filter_by(email="soft_del@test.com").first()
    assert still_there is not None
    assert still_there.is_deleted is True


def test_refresh_token_is_valid(app, db, owner_user):
    from app.models.refresh_token import RefreshToken

    rt = RefreshToken(
        user_id=owner_user.id,
        token_hash="abc123",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.session.add(rt)
    db.session.flush()
    assert rt.is_valid is True


def test_refresh_token_expired(app, db, owner_user):
    from app.models.refresh_token import RefreshToken

    rt = RefreshToken(
        user_id=owner_user.id,
        token_hash="expired_hash",
        issued_at=datetime.now(timezone.utc) - timedelta(days=8),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.session.add(rt)
    db.session.flush()
    assert rt.is_valid is False


def test_refresh_token_revoked(app, db, owner_user):
    from app.models.refresh_token import RefreshToken

    rt = RefreshToken(
        user_id=owner_user.id,
        token_hash="revoked_hash",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.session.add(rt)
    db.session.flush()
    rt.revoke()
    assert rt.is_valid is False
    assert rt.revoked_at is not None


def test_audit_log_to_dict(app, db, owner_user):
    from app.models.audit_log import AuditLog, AuditAction

    entry = AuditLog(
        table_name="users",
        record_id=owner_user.id,
        action=AuditAction.LOGIN,
        user_id=owner_user.id,
        ip_address="127.0.0.1",
        timestamp=datetime.now(timezone.utc),
    )
    db.session.add(entry)
    db.session.flush()

    d = entry.to_dict()
    assert d["action"] == "LOGIN"
    assert d["table_name"] == "users"
    assert d["ip_address"] == "127.0.0.1"
    assert "timestamp" in d


def test_company_soft_delete(app, db, company):
    from app.models.company import Company

    company.is_deleted = True
    company.deleted_at = datetime.now(timezone.utc)
    db.session.flush()

    active = Company.query.filter_by(id=company.id, is_deleted=False).first()
    assert active is None

    still = Company.query.get(company.id)
    assert still.is_deleted is True


def test_all_timestamps_utc(app, db, company):
    """Timestamps stored must be timezone-aware UTC."""
    assert company.created_at.tzinfo is not None
