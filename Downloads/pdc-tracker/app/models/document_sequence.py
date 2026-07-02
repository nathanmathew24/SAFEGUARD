from datetime import datetime, timezone
from app.extensions import db


class DocumentSequence(db.Model):
    __tablename__ = "document_sequences"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    doc_type = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    last_number = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint("company_id", "doc_type", "year", name="uq_doc_sequence"),
    )


_PREFIX = {
    "invoice": "INV",
    "purchase_invoice": "PINV",
    "lpo": "LPO",
    "quotation": "QTN",
    "credit_note": "CN",
    "debit_note": "DN",
    "delivery_note": "DLV",
    "pdc": "PDC",
    "receipt_voucher": "RV",
}


def next_document_number(company_id: int, doc_type: str) -> str:
    """
    Atomically increment sequence and return formatted document number.
    Uses SELECT FOR UPDATE to prevent duplicate numbers under concurrency.
    """
    year = datetime.now(timezone.utc).year
    seq = (
        DocumentSequence.query
        .filter_by(company_id=company_id, doc_type=doc_type, year=year)
        .with_for_update()
        .first()
    )
    if seq is None:
        seq = DocumentSequence(
            company_id=company_id, doc_type=doc_type, year=year, last_number=0
        )
        db.session.add(seq)
        db.session.flush()

    seq.last_number += 1
    prefix = _PREFIX.get(doc_type, doc_type.upper())
    return f"{prefix}-{year}-{seq.last_number:04d}"
