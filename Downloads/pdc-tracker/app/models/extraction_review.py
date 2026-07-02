from datetime import datetime, timezone
from app.extensions import db


class ExtractionReview(db.Model):
    __tablename__ = "extraction_reviews"

    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    raw_text = db.Column(db.Text, nullable=True)           # sanitized OCR/PDF text
    extracted_fields = db.Column(db.JSON, nullable=True)   # {field: {value, confidence}}
    low_confidence_fields = db.Column(db.JSON, nullable=True)  # [field_name, ...]
    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="reviewstatus"),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    created_document_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "upload_id": self.upload_id,
            "company_id": self.company_id,
            "document_type": self.document_type,
            "extracted_fields": self.extracted_fields,
            "low_confidence_fields": self.low_confidence_fields,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "rejection_reason": self.rejection_reason,
            "created_document_id": self.created_document_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
