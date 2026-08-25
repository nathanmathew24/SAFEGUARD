"""
ExtractionJob — tracks one raw-input → Claude-extraction → human-confirmation cycle.

Status flow:
  queued → processing → awaiting_confirmation → confirmed | failed

Nothing becomes a real document automatically. The job sits at awaiting_confirmation
until a human explicitly confirms every line. There is no confidence-threshold
auto-acceptance anywhere in this flow — hard product requirement.
"""
from datetime import datetime, timezone
from app.extensions import db


class ExtractionJob(db.Model):
    __tablename__ = "extraction_jobs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    source_channel = db.Column(
        db.Enum("web", "email", "whatsapp", name="channel_enum"),
        nullable=False, default="web",
    )
    raw_input_type = db.Column(
        db.Enum("text", "image", "pdf", name="input_type_enum"),
        nullable=False, default="text",
    )
    raw_input_ref = db.Column(db.String(500), nullable=True)   # file path or inline text

    status = db.Column(
        db.Enum("queued", "processing", "awaiting_confirmation", "confirmed", "failed",
                name="extraction_status_enum"),
        nullable=False, default="queued", server_default="queued",
    )
    error_message = db.Column(db.Text, nullable=True)

    # Raw Claude output
    extracted_payload = db.Column(db.JSON, nullable=True)
    # After catalog fuzzy-matching: list of {description, qty, unit_price, product_id, confidence, confirmed}
    matched_lines = db.Column(db.JSON, nullable=True)

    target_document_type = db.Column(
        db.Enum("quote", "lpo", "invoice", name="target_doc_enum"),
        nullable=True,
    )
    resulting_document_id = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "source_channel": self.source_channel,
            "raw_input_type": self.raw_input_type,
            "raw_input_ref": self.raw_input_ref,
            "status": self.status,
            "error_message": self.error_message,
            "extracted_payload": self.extracted_payload,
            "matched_lines": self.matched_lines,
            "target_document_type": self.target_document_type,
            "resulting_document_id": self.resulting_document_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
