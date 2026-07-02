"""
Orchestrates: upload → OCR → classify → extract → validate → create/review.
"""
from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models.uploaded_file import UploadedFile
from app.models.extraction_review import ExtractionReview
from app.utils import file_store
from app.utils.ocr import extract_text, validate_file
from app.agents import classifier, document_extractor
from app.agents.validator import validate_fields, flatten_values
from app.services import document_service as doc_svc


# ---- Upload ----

def handle_upload(
    file_bytes: bytes,
    original_filename: str,
    mime_type: str,
    company_id: int,
    user_id: int,
) -> UploadedFile:
    """Encrypt and store file; create UploadedFile record."""
    storage_path, stored_name = file_store.save_file(file_bytes, original_filename, company_id)

    uf = UploadedFile(
        company_id=company_id,
        original_filename=original_filename,
        stored_filename=stored_name,
        file_size=len(file_bytes),
        mime_type=mime_type,
        storage_path=storage_path,
        is_encrypted=True,
        uploaded_by=user_id,
        uploaded_at=datetime.now(timezone.utc),
        extraction_status="pending",
    )
    db.session.add(uf)
    db.session.commit()
    return uf


# ---- Extraction pipeline ----

def run_extraction(upload_id: int, company_id: int, user_id: int) -> dict:
    """
    Full pipeline: load → OCR → classify → extract → validate → create/review.
    Returns {"status": "created"|"pending_review", ...}.
    """
    uf = db.session.get(UploadedFile, upload_id)
    if uf is None:
        raise ValueError("Upload not found")
    if uf.company_id != company_id:
        raise ValueError("Upload does not belong to this company")

    uf.extraction_status = "processing"
    db.session.flush()

    try:
        # 1. Load and decrypt
        file_bytes = file_store.load_file(uf.storage_path)

        # 2. OCR / text extraction
        text = extract_text(file_bytes, uf.mime_type)
        if not text.strip():
            raise ValueError("Could not extract text from document")

        # 3. Classify
        classify_result = classifier.classify(text, upload_id)
        doc_type = classify_result["document_type"]
        if doc_type == "unknown":
            raise ValueError("Could not classify document type")

        # 4. Extract fields
        extract_result = document_extractor.extract(text, doc_type, upload_id)
        fields = extract_result["fields"]
        low_conf = extract_result["low_confidence_fields"]

        # 5. Validate field values
        valid, errors = validate_fields(fields, doc_type)
        if not valid:
            raise ValueError(f"Extracted data invalid: {'; '.join(errors)}")

        # 6. Route: auto-create or human review
        if low_conf:
            result = _create_review(
                upload_id, company_id, doc_type, text, fields, low_conf
            )
        else:
            document_id = _auto_create_document(
                doc_type, fields, company_id, user_id
            )
            result = {"status": "created", "document_id": document_id,
                      "document_type": doc_type}

        uf.extraction_status = "completed"
        db.session.commit()
        return result

    except Exception:
        uf.extraction_status = "failed"
        db.session.commit()
        raise


def _create_review(
    upload_id, company_id, doc_type, raw_text, fields, low_conf
) -> dict:
    review = ExtractionReview(
        upload_id=upload_id,
        company_id=company_id,
        document_type=doc_type,
        raw_text=raw_text[:10000],
        extracted_fields=fields,
        low_confidence_fields=low_conf,
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.session.add(review)
    db.session.flush()
    return {
        "status": "pending_review",
        "review_id": review.id,
        "document_type": doc_type,
        "low_confidence_fields": low_conf,
    }


def _auto_create_document(doc_type, fields, company_id, user_id) -> int:
    """Create a Phase 2 document from extracted fields."""
    from app.utils.ip import get_client_ip
    values = flatten_values(fields)
    values["company_id"] = company_id

    # Map extracted field names to document_service expected names
    _ensure_date(values, "document_date")
    _ensure_date(values, "due_date")
    _ensure_date(values, "cheque_date")
    _ensure_date(values, "delivery_date")
    _ensure_date(values, "valid_until")
    _ensure_date(values, "delivery_expected_date")

    # Ensure required minimum fields
    if "party_name" not in values and "received_from" in values:
        values["party_name"] = values["received_from"]
    if "party_name" not in values:
        values["party_name"] = "Unknown"
    if "document_date" not in values or not values["document_date"]:
        from datetime import date
        values["document_date"] = date.today()

    # credit_note and debit_note require reason
    if doc_type in ("credit_note", "debit_note") and not values.get("reason"):
        values["reason"] = "Extracted from document"

    doc = doc_svc.create_document(doc_type, values, user_id, "extraction-agent")
    return doc.id


def _ensure_date(values, field):
    from datetime import date
    val = values.get(field)
    if val and isinstance(val, str):
        try:
            values[field] = date.fromisoformat(val)
        except ValueError:
            values.pop(field, None)


# ---- Review queue ----

def list_pending_reviews(company_id: int, page: int, per_page: int):
    q = ExtractionReview.query.filter_by(
        company_id=company_id, status="pending"
    ).order_by(ExtractionReview.id.desc())
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_review(review_id: int) -> ExtractionReview | None:
    return db.session.get(ExtractionReview, review_id)


def approve_review(review_id: int, corrected_fields: dict, user_id: int, company_id: int) -> int:
    """Apply corrections, create document, mark review approved."""
    review = db.session.get(ExtractionReview, review_id)
    if review is None:
        raise ValueError("Review not found")
    if review.company_id != company_id:
        raise ValueError("Review does not belong to this company")
    if review.status != "pending":
        raise ValueError("Review is not pending")

    # Merge: start with extracted, apply corrections on top
    base_fields = flatten_values(review.extracted_fields or {})
    base_fields.update(corrected_fields)
    base_fields["company_id"] = company_id

    _ensure_date(base_fields, "document_date")
    _ensure_date(base_fields, "due_date")
    _ensure_date(base_fields, "cheque_date")
    _ensure_date(base_fields, "delivery_date")
    _ensure_date(base_fields, "valid_until")
    _ensure_date(base_fields, "delivery_expected_date")

    if "party_name" not in base_fields and "received_from" in base_fields:
        base_fields["party_name"] = base_fields["received_from"]
    if not base_fields.get("party_name"):
        base_fields["party_name"] = "Unknown"
    if not base_fields.get("document_date"):
        from datetime import date
        base_fields["document_date"] = date.today()
    if review.document_type in ("credit_note", "debit_note") and not base_fields.get("reason"):
        base_fields["reason"] = "Approved by reviewer"

    doc = doc_svc.create_document(review.document_type, base_fields, user_id, "review-approval")
    doc_id = doc.id

    review.status = "approved"
    review.reviewed_by = user_id
    review.reviewed_at = datetime.now(timezone.utc)
    review.created_document_id = doc_id
    review.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return doc_id


def reject_review(review_id: int, reason: str, user_id: int, company_id: int) -> None:
    review = db.session.get(ExtractionReview, review_id)
    if review is None:
        raise ValueError("Review not found")
    if review.company_id != company_id:
        raise ValueError("Review does not belong to this company")
    if review.status != "pending":
        raise ValueError("Review is not pending")

    review.status = "rejected"
    review.reviewed_by = user_id
    review.reviewed_at = datetime.now(timezone.utc)
    review.rejection_reason = reason
    review.updated_at = datetime.now(timezone.utc)
    db.session.commit()
