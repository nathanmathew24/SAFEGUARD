from datetime import datetime, timezone
from app.extensions import db


class ExtractionLog(db.Model):
    __tablename__ = "extraction_logs"

    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=False)
    agent_step = db.Column(db.String(50), nullable=False)    # 'classify' | 'extract'
    model_used = db.Column(db.String(100), nullable=False)
    input_tokens = db.Column(db.Integer, nullable=True)
    output_tokens = db.Column(db.Integer, nullable=True)
    truncated_input = db.Column(db.Text, nullable=True)      # first 500 chars only
    truncated_output = db.Column(db.Text, nullable=True)     # first 500 chars only
    duration_ms = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "upload_id": self.upload_id,
            "agent_step": self.agent_step,
            "model_used": self.model_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
