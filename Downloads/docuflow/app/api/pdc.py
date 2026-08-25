from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.pdc import PDC
from app.models.invoice import Invoice
from app.models.audit_log import AuditLog
from app.utils.auth import current_user_id, current_company_id
from app.utils.scoping import get_scoped_or_404
from app.utils.errors import error_response

pdc_bp = Blueprint("pdc", __name__, url_prefix="/api/pdcs")


def _log(action, record_id, detail=None):
    db.session.add(AuditLog(
        company_id=current_company_id(),
        user_id=current_user_id(),
        action=action,
        table_name="pdcs",
        record_id=record_id,
        ip_address=request.remote_addr or "",
        detail=detail,
    ))


@pdc_bp.get("")
@jwt_required()
def list_pdcs():
    cid = current_company_id()
    pdcs = PDC.query.filter_by(company_id=cid).order_by(PDC.cheque_date.asc()).all()
    return jsonify([p.to_dict() for p in pdcs])


@pdc_bp.post("")
@jwt_required()
def create_pdc():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    required = ("cheque_number", "bank_name", "cheque_date", "amount")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response("MISSING_FIELDS", f"Required: {', '.join(missing)}", 400)

    invoice_id = data.get("invoice_id")
    if invoice_id:
        get_scoped_or_404(Invoice, invoice_id, cid)

    pdc = PDC(
        company_id=cid,
        created_by=uid,
        invoice_id=invoice_id,
        customer_id=data.get("customer_id"),
        cheque_number=data["cheque_number"],
        bank_name=data["bank_name"],
        cheque_date=data["cheque_date"],
        amount=data["amount"],
        currency=data.get("currency", "AED"),
        drawer_name=data.get("drawer_name"),
        history=[],
    )
    db.session.add(pdc)
    db.session.flush()
    _log("CREATE", pdc.id)
    db.session.commit()
    return jsonify(pdc.to_dict()), 201


@pdc_bp.get("/<int:pdc_id>")
@jwt_required()
def get_pdc(pdc_id):
    return jsonify(get_scoped_or_404(PDC, pdc_id, current_company_id()).to_dict())


@pdc_bp.post("/<int:pdc_id>/transition")
@jwt_required()
def transition_pdc(pdc_id):
    pdc = get_scoped_or_404(PDC, pdc_id, current_company_id())
    data = request.get_json(silent=True) or {}
    to_status = data.get("to_status", "")
    note = data.get("note", "")

    # ValueError on illegal transition → caught by global error handler → 400
    pdc.transition(to_status, current_user_id(), note)

    _log("TRANSITION", pdc.id, {"to": to_status})
    db.session.commit()
    return jsonify(pdc.to_dict())
