"""
AnomalyFlag — polymorphic, points at any document type via document_type + document_id.

Categories (see services/anomaly_service.py for detection logic):
  price_deviation, quantity_outlier, duplicate_document,
  missing_fields, total_mismatch
"""
from datetime import datetime, timezone
from app.extensions import db


class AnomalyFlag(db.Model):
    __tablename__ = "anomaly_flags"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    # Polymorphic reference — not per-type FKs so any document type can be flagged
    document_type = db.Column(db.String(50), nullable=False)  # e.g. "invoice", "quote"
    document_id = db.Column(db.Integer, nullable=False)

    category = db.Column(
        db.Enum(
            "price_deviation", "quantity_outlier", "duplicate_document",
            "missing_fields", "total_mismatch",
            name="anomaly_category_enum",
        ),
        nullable=False,
    )
    severity = db.Column(
        db.Enum("low", "medium", "high", name="anomaly_severity_enum"),
        nullable=False, default="medium",
    )
    message = db.Column(db.String(500), nullable=False)
    details = db.Column(db.JSON, nullable=True)

    resolved = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.Index("ix_anomaly_doc", "company_id", "document_type", "document_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "document_type": self.document_type,
            "document_id": self.document_id,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
