from datetime import datetime, timezone
from app.extensions import db


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Store SHA-256 hash of the token — never the raw value
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)

    issued_at = db.Column(db.DateTime(timezone=True), nullable=False,
                          default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Points to the token that replaced this one (rotation chain)
    replaced_by = db.Column(db.Integer, db.ForeignKey("refresh_tokens.id"), nullable=True)

    user = db.relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self):
        now = datetime.now(timezone.utc)
        return self.revoked_at is None and self.expires_at > now

    def revoke(self):
        self.revoked_at = datetime.now(timezone.utc)
