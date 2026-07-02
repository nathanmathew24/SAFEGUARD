from datetime import datetime, timezone
from app.extensions import db


class UploadedFile(db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)  # UUID-based
    file_size = db.Column(db.Integer, nullable=False)            # bytes
    mime_type = db.Column(db.String(100), nullable=False)
    storage_path = db.Column(db.Text, nullable=False)
    is_encrypted = db.Column(db.Boolean, nullable=False, default=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    extraction_status = db.Column(
        db.Enum("pending", "processing", "completed", "failed",
                name="extractionstatus"),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "extraction_status": self.extraction_status,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
