from datetime import datetime, timezone
from app.extensions import db


class GeneratedPDF(db.Model):
    __tablename__ = "generated_pdfs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)
    doc_id = db.Column(db.Integer, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    file_path = db.Column(db.String(500), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    generated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.Index("ix_generated_pdfs_doc", "doc_type", "doc_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "doc_type": self.doc_type,
            "doc_id": self.doc_id,
            "version": self.version,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat(),
        }
