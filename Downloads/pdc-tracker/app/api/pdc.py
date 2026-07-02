"""
Phase 4 PDC endpoints.
Status transitions enforce the state machine in pdc_service.
Every mutation writes to AuditLog.
"""
from datetime import date

from flask import Blueprint, jsonify, g

from app.extensions import db
from app.models.pdc import PDC
from app.models.invoice import Invoice
from app.models.purchase_invoice import PurchaseInvoice
from app.models.user import UserRole
from app.services import pdc_service
from app.utils.errors import error_response
from app.utils.ip import get_client_ip
from app.utils.jwt_required import jwt_required
from app.utils.rbac import require_role

pdc_bp = Blueprint("pdc", __name__, url_prefix="/api/pdc")


@pdc_bp.route("/received", methods=["GET"])
@jwt_required
def list_received():
    pdcs = PDC.query.filter_by(pdc_direction="received").order_by(PDC.cheque_date).all()
    return jsonify({"data": [p.to_dict() for p in pdcs]}), 200


@pdc_bp.route("/issued", methods=["GET"])
@jwt_required
def list_issued():
    pdcs = PDC.query.filter_by(pdc_direction="issued").order_by(PDC.cheque_date).all()
    return jsonify({"data": [p.to_dict() for p in pdcs]}), 200


@pdc_bp.route("/<int:pdc_id>/mark-submitted", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def mark_submitted(pdc_id):
    try:
        pdc = pdc_service.mark_submitted(pdc_id, g.current_user.id, get_client_ip())
    except ValueError as exc:
        return error_response("INVALID_TRANSITION", str(exc), 422)
    return jsonify({"data": pdc.to_dict()}), 200


@pdc_bp.route("/<int:pdc_id>/mark-cleared", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def mark_cleared(pdc_id):
    try:
        pdc = pdc_service.mark_cleared(pdc_id, g.current_user.id, get_client_ip())
    except ValueError as exc:
        return error_response("INVALID_TRANSITION", str(exc), 422)
    return jsonify({"data": pdc.to_dict()}), 200


@pdc_bp.route("/<int:pdc_id>/mark-bounced", methods=["POST"])
@jwt_required
@require_role(UserRole.owner)
def mark_bounced(pdc_id):
    try:
        pdc = pdc_service.mark_bounced(pdc_id, g.current_user.id, get_client_ip())
    except ValueError as exc:
        return error_response("INVALID_TRANSITION", str(exc), 422)
    return jsonify({"data": pdc.to_dict()}), 200


@pdc_bp.route("/<int:pdc_id>/mark-cancelled", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def mark_cancelled(pdc_id):
    try:
        pdc = pdc_service.mark_cancelled(pdc_id, g.current_user.id, get_client_ip())
    except ValueError as exc:
        return error_response("INVALID_TRANSITION", str(exc), 422)
    return jsonify({"data": pdc.to_dict()}), 200


@pdc_bp.route("/payments/overdue", methods=["GET"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def list_overdue():
    """
    Returns invoices and purchase invoices past due_date that are still unpaid.
    Also returns PDCs past cheque_date that are still pending.
    """
    today = date.today()
    results = []

    invoices = Invoice.query.filter(
        Invoice.due_date < today,
        Invoice.status == "confirmed",
        Invoice.is_voided.is_(False),
        Invoice.payment_status == "unpaid",
    ).all()
    for inv in invoices:
        d = inv.to_dict()
        d["overdue_type"] = "invoice"
        d["days_overdue"] = (today - inv.due_date).days
        results.append(d)

    purchase_invoices = PurchaseInvoice.query.filter(
        PurchaseInvoice.due_date < today,
        PurchaseInvoice.status == "confirmed",
        PurchaseInvoice.is_voided.is_(False),
        PurchaseInvoice.payment_status == "unpaid",
    ).all()
    for inv in purchase_invoices:
        d = inv.to_dict()
        d["overdue_type"] = "purchase_invoice"
        d["days_overdue"] = (today - inv.due_date).days
        results.append(d)

    pending_pdcs = PDC.query.filter(
        PDC.cheque_date < today,
        PDC.pdc_status == "pending",
        PDC.is_voided.is_(False),
    ).all()
    for pdc in pending_pdcs:
        d = pdc.to_dict()
        d["overdue_type"] = "pdc"
        d["days_overdue"] = (today - pdc.cheque_date).days
        results.append(d)

    results.sort(key=lambda x: x["days_overdue"], reverse=True)
    return jsonify({"data": results, "total": len(results)}), 200
