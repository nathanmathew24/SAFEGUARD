"""
Phase 5 PDF generation endpoints.
POST /api/<doc_type>/<id>/generate-pdf  — Finance Manager + Owner
GET  /api/pdf/download/<token>          — all authenticated roles
"""
from flask import Blueprint, jsonify, g, current_app, send_file
import io

from app.extensions import db
from app.models.company import Company
from app.models.generated_pdf import GeneratedPDF
from app.models.audit_log import AuditAction
from app.models.user import UserRole
from app.services.audit_service import log_event
from app.services.document_service import _REGISTRY
from app.utils.errors import error_response
from app.utils.ip import get_client_ip
from app.utils.jwt_required import jwt_required
from app.utils.rbac import require_role
from app.utils.pdf_generator import (
    render_pdf, save_pdf, load_pdf,
    generate_signed_token, verify_signed_token,
    _TEMPLATES,
)

pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/api/<doc_type>/<int:doc_id>/generate-pdf", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def generate(doc_type, doc_id):
    if doc_type not in _TEMPLATES:
        return error_response("NOT_FOUND", f"PDF generation not supported for '{doc_type}'", 404)

    reg = _REGISTRY.get(doc_type)
    if reg is None:
        return error_response("NOT_FOUND", "Document type not registered", 404)

    model_cls, _, _ = reg
    doc = model_cls.query.get_or_404(doc_id)

    company = Company.query.get(doc.company_id)
    if company is None:
        return error_response("NOT_FOUND", "Company not found", 404)

    # Determine next version number
    last = (
        GeneratedPDF.query
        .filter_by(doc_type=doc_type, doc_id=doc_id)
        .order_by(GeneratedPDF.version.desc())
        .first()
    )
    version = (last.version + 1) if last else 1

    pdf_bytes = render_pdf(doc, doc_type, company, current_app._get_current_object())
    file_path = save_pdf(pdf_bytes, doc_type, doc_id, version,
                         current_app._get_current_object())

    record = GeneratedPDF(
        company_id=doc.company_id,
        doc_type=doc_type,
        doc_id=doc_id,
        version=version,
        file_path=file_path,
        generated_by=g.current_user.id,
    )
    db.session.add(record)
    db.session.flush()

    log_event(
        action=AuditAction.CREATE,
        table_name="generated_pdfs",
        record_id=record.id,
        user_id=g.current_user.id,
        ip_address=get_client_ip(),
        new_values={"doc_type": doc_type, "doc_id": doc_id, "version": version},
    )

    token = generate_signed_token(record.id, current_app._get_current_object())
    return jsonify({
        "data": {
            **record.to_dict(),
            "download_token": token,
        }
    }), 201


@pdf_bp.route("/api/pdf/download/<token>", methods=["GET"])
@jwt_required
def download(token):
    pdf_id = verify_signed_token(token, current_app._get_current_object())
    if pdf_id is None:
        return error_response("INVALID_TOKEN", "Download link is invalid or has expired", 403)

    record = GeneratedPDF.query.get_or_404(pdf_id)
    pdf_bytes = load_pdf(record.file_path, current_app._get_current_object())

    log_event(
        action=AuditAction.UPDATE,
        table_name="generated_pdfs",
        record_id=record.id,
        user_id=g.current_user.id,
        ip_address=get_client_ip(),
        new_values={"event": "downloaded"},
    )

    filename = f"{record.doc_type}_{record.doc_id}_v{record.version}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@pdf_bp.route("/api/<doc_type>/<int:doc_id>/download", methods=["GET"])
@jwt_required
def get_download_token(doc_type, doc_id):
    """Return a fresh signed token for the latest PDF version of a document."""
    record = (
        GeneratedPDF.query
        .filter_by(doc_type=doc_type, doc_id=doc_id)
        .order_by(GeneratedPDF.version.desc())
        .first()
    )
    if record is None:
        return error_response("NOT_FOUND", "No PDF has been generated for this document", 404)

    token = generate_signed_token(record.id, current_app._get_current_object())
    return jsonify({"data": {"download_token": token, **record.to_dict()}}), 200
