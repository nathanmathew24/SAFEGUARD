"""
Extraction routes:
  POST /api/extraction/upload   — web file upload (core, always active)
  POST /api/extraction/text     — JSON text/email intake (core, always active)
  POST /api/extraction/<id>/confirm — human confirmation step
  GET  /api/extraction/<id>     — poll job status

WhatsApp intake is gated: source_channel="whatsapp" requires whatsapp_addon_enabled.
"""
import os
import uuid
from pathlib import Path

import filetype
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from app.extensions import db, limiter
from app.models.extraction_job import ExtractionJob
from app.models.company import Company
from app.models.quote import Quote
from app.models.lpo import LPO
from app.models.invoice import Invoice
from app.models.line_item import LineItem
from app.utils.auth import current_user_id, current_company_id
from app.utils.scoping import get_scoped_or_404
from app.utils.errors import error_response
from app.services.extraction_service import confirm_job, ExtractionError

extraction_bp = Blueprint("extraction", __name__, url_prefix="/api/extraction")

_ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
}


@extraction_bp.post("/upload")
@jwt_required()
@limiter.limit("30 per minute")
def upload_and_extract():
    """Web file upload — primary order-capture path (core, always active)."""
    cid = current_company_id()
    uid = current_user_id()

    if "file" not in request.files:
        return error_response("MISSING_FILE", "Multipart field 'file' required", 400)

    f = request.files["file"]
    raw_bytes = f.read(current_app.config["UPLOAD_MAX_BYTES"] + 1)
    if len(raw_bytes) > current_app.config["UPLOAD_MAX_BYTES"]:
        return error_response("FILE_TOO_LARGE", "File exceeds 10 MB limit", 413)

    kind = filetype.guess(raw_bytes)
    if kind is None or kind.mime not in _ALLOWED_MIME:
        return error_response(
            "UNSUPPORTED_FILE_TYPE",
            f"Allowed types: {', '.join(sorted(_ALLOWED_MIME))}",
            415,
        )

    upload_dir = Path(current_app.config["UPLOAD_DIR"]) / str(cid)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{kind.extension}"
    dest = upload_dir / filename
    dest.write_bytes(raw_bytes)

    input_type = "image" if kind.mime.startswith("image/") else "pdf"
    job = ExtractionJob(
        company_id=cid,
        created_by=uid,
        source_channel="web",
        raw_input_type=input_type,
        raw_input_ref=str(dest),
        target_document_type=request.form.get("target_document_type", "invoice"),
    )
    db.session.add(job)
    db.session.commit()

    from app.tasks.extraction_tasks import extract_document_task
    extract_document_task.delay(job.id)

    return jsonify({"job_id": job.id, "status": job.status}), 202


@extraction_bp.post("/text")
@jwt_required()
@limiter.limit("30 per minute")
def text_extract():
    """JSON text or email intake."""
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    source_channel = data.get("source_channel", "email")

    # WhatsApp channel gate
    if source_channel == "whatsapp":
        company = db.session.get(Company, cid)
        if not company or not company.whatsapp_addon_enabled:
            return error_response(
                "ADDON_NOT_ENABLED",
                "WhatsApp intake requires the WhatsApp add-on. Contact support to enable it.",
                403,
            )

    text_content = data.get("text", "")
    if not text_content.strip():
        return error_response("MISSING_FIELDS", "text is required", 400)

    job = ExtractionJob(
        company_id=cid,
        created_by=uid,
        source_channel=source_channel,
        raw_input_type="text",
        raw_input_ref=text_content[:10000],
        target_document_type=data.get("target_document_type", "invoice"),
    )
    db.session.add(job)
    db.session.commit()

    from app.tasks.extraction_tasks import extract_document_task
    extract_document_task.delay(job.id)

    return jsonify({"job_id": job.id, "status": job.status}), 202


@extraction_bp.get("/<int:job_id>")
@jwt_required()
def get_job(job_id):
    job = get_scoped_or_404(ExtractionJob, job_id, current_company_id())
    return jsonify(job.to_dict())


@extraction_bp.post("/<int:job_id>/confirm")
@jwt_required()
def confirm_extraction(job_id):
    """
    Human confirmation step. Every line must have confirmed=true before a
    document can be created from this job. No threshold-based auto-acceptance.
    """
    cid = current_company_id()
    uid = current_user_id()
    job = get_scoped_or_404(ExtractionJob, job_id, cid)
    data = request.get_json(silent=True) or {}
    confirmations = data.get("lines", [])

    try:
        confirm_job(job, confirmations)
    except ExtractionError as exc:
        return error_response("CONFIRMATION_FAILED", str(exc), 422)

    # Optionally create the target document from confirmed lines
    target_type = data.get("create_document")
    if target_type and job.status == "confirmed":
        doc_id = _create_document_from_job(job, target_type, cid, uid, data)
        job.resulting_document_id = doc_id

    db.session.commit()
    return jsonify(job.to_dict())


def _create_document_from_job(job: ExtractionJob, target_type: str, cid: int, uid: int, data: dict) -> int:
    lines_data = [
        {
            "description": l["description"],
            "quantity": l["quantity"],
            "unit_price": l["unit_price"],
            "product_id": l.get("matched_product_id"),
        }
        for l in (job.matched_lines or [])
    ]

    from app.api.documents import _build_lines

    if target_type == "quote":
        doc = Quote(
            company_id=cid, created_by=uid,
            quote_number=data.get("document_number", ""),
            customer_name=data.get("customer_name", ""),
            currency=data.get("currency", "AED"),
        )
    elif target_type == "lpo":
        doc = LPO(
            company_id=cid, created_by=uid,
            lpo_number=data.get("document_number", ""),
            customer_name=data.get("customer_name", ""),
            currency=data.get("currency", "AED"),
        )
    else:  # invoice default
        doc = Invoice(
            company_id=cid, created_by=uid,
            invoice_number=data.get("document_number", ""),
            customer_name=data.get("customer_name", ""),
            currency=data.get("currency", "AED"),
        )

    db.session.add(doc)
    db.session.flush()
    db.session.add_all(_build_lines(doc, lines_data))
    db.session.flush()
    return doc.id
