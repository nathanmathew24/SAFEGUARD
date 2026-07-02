from flask import Blueprint, request, g
from app.utils.errors import error_response
from app.utils.jwt_required import jwt_required
from app.utils.rbac import require_role
from app.utils.ip import get_client_ip
from app.models.user import UserRole
from app.services import document_service as svc
import re
from datetime import date


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return date.fromisoformat(val)


def _validate_create(data, required_extra=None):
    errors = []
    for field in ("company_id", "party_name", "document_date"):
        if not data.get(field):
            errors.append(f"{field} is required")
    if required_extra:
        for field in required_extra:
            if not data.get(field):
                errors.append(f"{field} is required")
    return errors


def make_document_blueprint(slug, url_prefix, required_extra=None):
    """
    Factory: creates a Flask Blueprint for one document type.
    slug        — key in document_service registry e.g. 'invoice'
    url_prefix  — e.g. '/api/invoices'
    required_extra — additional required fields beyond the shared set
    """
    name = slug.replace("-", "_")
    bp = Blueprint(f"doc_{name}", __name__)

    # ---- CREATE ----
    @bp.route(url_prefix, methods=["POST"])
    @jwt_required
    @require_role(UserRole.owner, UserRole.finance_manager, UserRole.operations_staff)
    def create():
        data = request.get_json(silent=True) or {}
        errors = _validate_create(data, required_extra)
        if errors:
            return error_response("VALIDATION_ERROR", "; ".join(errors), 422)

        try:
            data["document_date"] = _parse_date(data.get("document_date"))
            data["due_date"] = _parse_date(data.get("due_date"))
            if "cheque_date" in data:
                data["cheque_date"] = _parse_date(data.get("cheque_date"))
            if "delivery_date" in data:
                data["delivery_date"] = _parse_date(data.get("delivery_date"))
            if "valid_until" in data:
                data["valid_until"] = _parse_date(data.get("valid_until"))
            if "delivery_expected_date" in data:
                data["delivery_expected_date"] = _parse_date(data.get("delivery_expected_date"))
        except (ValueError, TypeError) as e:
            return error_response("VALIDATION_ERROR", f"Invalid date: {e}", 422)

        doc = svc.create_document(slug, data, g.current_user.id, get_client_ip())
        return doc.to_dict(), 201

    # ---- LIST ----
    @bp.route(url_prefix, methods=["GET"])
    @jwt_required
    @require_role(UserRole.owner, UserRole.finance_manager,
                  UserRole.operations_staff, UserRole.viewer)
    def list_docs():
        company_id = request.args.get("company_id", type=int)
        if not company_id:
            return error_response("VALIDATION_ERROR", "company_id query param required", 422)
        status = request.args.get("status")
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)

        items, total = svc.list_documents(slug, company_id, status=status,
                                          page=page, per_page=per_page)
        return {
            "data": [d.to_dict(include_lines=False) for d in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }, 200

    # ---- GET ONE ----
    @bp.route(f"{url_prefix}/<int:doc_id>", methods=["GET"])
    @jwt_required
    @require_role(UserRole.owner, UserRole.finance_manager,
                  UserRole.operations_staff, UserRole.viewer)
    def get_one(doc_id):
        doc = svc.get_document(slug, doc_id)
        if doc is None:
            return error_response("NOT_FOUND", "Document not found", 404)
        return doc.to_dict(), 200

    # ---- UPDATE ----
    @bp.route(f"{url_prefix}/<int:doc_id>", methods=["PUT"])
    @jwt_required
    @require_role(UserRole.owner, UserRole.finance_manager, UserRole.operations_staff)
    def update(doc_id):
        data = request.get_json(silent=True) or {}
        try:
            for df in ("document_date", "due_date", "cheque_date",
                       "delivery_date", "valid_until", "delivery_expected_date"):
                if df in data:
                    data[df] = _parse_date(data[df])
        except (ValueError, TypeError) as e:
            return error_response("VALIDATION_ERROR", f"Invalid date: {e}", 422)

        doc, err = svc.update_document(slug, doc_id, data, g.current_user.id, get_client_ip())
        if err == "not_found":
            return error_response("NOT_FOUND", "Document not found", 404)
        if err == "immutable":
            return error_response("IMMUTABLE", "Confirmed documents cannot be updated", 409)
        if err == "voided":
            return error_response("VOIDED", "Voided documents cannot be updated", 409)
        return doc.to_dict(), 200

    # ---- CONFIRM ----
    @bp.route(f"{url_prefix}/<int:doc_id>/confirm", methods=["POST"])
    @jwt_required
    @require_role(UserRole.owner, UserRole.finance_manager)
    def confirm(doc_id):
        doc, err = svc.confirm_document(slug, doc_id, g.current_user.id, get_client_ip())
        if err == "not_found":
            return error_response("NOT_FOUND", "Document not found", 404)
        if err == "already_confirmed":
            return error_response("ALREADY_CONFIRMED", "Document already confirmed", 409)
        if err == "voided":
            return error_response("VOIDED", "Cannot confirm a voided document", 409)
        return doc.to_dict(), 200

    # ---- VOID ----
    @bp.route(f"{url_prefix}/<int:doc_id>/void", methods=["POST"])
    @jwt_required
    @require_role(UserRole.owner, UserRole.finance_manager)
    def void(doc_id):
        data = request.get_json(silent=True) or {}
        reason = (data.get("reason") or "").strip()
        if not reason:
            return error_response("VALIDATION_ERROR", "void reason is required", 422)

        doc, err = svc.void_document(slug, doc_id, reason, g.current_user.id, get_client_ip())
        if err == "not_found":
            return error_response("NOT_FOUND", "Document not found", 404)
        if err == "already_voided":
            return error_response("ALREADY_VOIDED", "Document already voided", 409)
        return doc.to_dict(), 200

    return bp
