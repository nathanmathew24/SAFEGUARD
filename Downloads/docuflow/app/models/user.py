from datetime import datetime, timezone
from app.extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(
        db.Enum("owner", "staff", "accountant", name="user_role_enum"),
        nullable=False, default="staff",
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    password_reset_token = db.Column(db.String(128), nullable=True)
    password_reset_expires = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    company = db.relationship("Company", back_populates="users")

    def set_password(self, plaintext: str):
        self.password_hash = bcrypt.generate_password_hash(plaintext).decode("utf-8")

    def check_password(self, plaintext: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, plaintext)

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
