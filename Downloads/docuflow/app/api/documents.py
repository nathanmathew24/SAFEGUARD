"""
Document chain routes: Quote, LPO, Invoice, DeliveryNote, CreditNote, DebitNote.

Every read and write uses get_scoped_or_404 — the fix for cross-tenant access.
Every edit calls doc.ensure_editable() before touching any field.
Credit/Debit Notes reject creation against an unlocked Invoice.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from app.extensions import db, limiter
from app.models.audit_log import AuditLog
from app.models.quote import Quote
from app.models.lpo import LPO
from app.models.invoice import Invoice
from app.models.delivery_note import DeliveryNote
from app.models.credit_note import CreditNote
from app.models.debit_note import DebitNote
from app.models.line_item import LineItem
from app.utils.auth import current_user_id, current_company_id
from app.utils.scoping import get_scoped_or_404
from app.utils.errors import error_response
from app.services.anomaly_service import check_invoice, check_delivery_note

docs_bp = Blueprint("documents", __name__)


# ── helpers ────────────────────────────────────────────────────────────────────

def _log(action, table, record_id):
    db.session.add(AuditLog(
        company_id=current_company_id(),
        user_id=current_user_id(),
        action=action,
        table_name=table,
        record_id=record_id,
        ip_address=request.remote_addr or "",
    ))


def _build_lines(doc, items: list):
    fk_map = {
        Quote: "quote_id", LPO: "lpo_id", Invoice: "invoice_id",
        DeliveryNote: "delivery_note_id", CreditNote: "credit_note_id",
        DebitNote: "debit_note_id",
    }
    fk = fk_map[type(doc)]
    lines = []
    total = 0.0
    for item in items:
        qty = float(item.get("quantity", 0))
        price = float(item.get("unit_price", 0))
        li = LineItem(
            **{fk: doc.id},
            product_id=item.get("product_id"),
            description=item.get("description", ""),
            quantity=qty,
            unit_price=price,
            unit_of_measure=item.get("unit_of_measure", "EA"),
            line_total=round(qty * price, 4),
        )
        total += li.line_total
        lines.append(li)
    doc.subtotal = round(total, 4)
    doc.total = round(total, 4)   # TODO: add VAT logic
    return lines


# ── Quotes ─────────────────────────────────────────────────────────────────────

@docs_bp.get("/api/quotes")
@jwt_required()
def list_quotes():
    cid = current_company_id()
    quotes = Quote.query.filter_by(company_id=cid).order_by(Quote.created_at.desc()).all()
    return jsonify([q.to_dict(include_lines=False) for q in quotes])


@docs_bp.post("/api/quotes")
@jwt_required()
def create_quote():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    q = Quote(
        company_id=cid,
        created_by=uid,
        quote_number=data.get("quote_number", ""),
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name", ""),
        customer_trn=data.get("customer_trn"),
        document_date=data.get("document_date"),
        due_date=data.get("due_date"),
        valid_until=data.get("valid_until"),
        notes=data.get("notes"),
        currency=data.get("currency", "AED"),
    )
    db.session.add(q)
    db.session.flush()

    lines = _build_lines(q, data.get("line_items", []))
    db.session.add_all(lines)
    _log("CREATE", "quotes", q.id)
    db.session.commit()
    return jsonify(q.to_dict()), 201


@docs_bp.get("/api/quotes/<int:doc_id>")
@jwt_required()
def get_quote(doc_id):
    q = get_scoped_or_404(Quote, doc_id, current_company_id())
    return jsonify(q.to_dict())


@docs_bp.patch("/api/quotes/<int:doc_id>")
@jwt_required()
def update_quote(doc_id):
    q = get_scoped_or_404(Quote, doc_id, current_company_id())
    q.ensure_editable()
    data = request.get_json(silent=True) or {}
    for field in ("customer_name", "customer_trn", "notes", "document_date",
                  "due_date", "valid_until", "currency"):
        if field in data:
            setattr(q, field, data[field])
    if "line_items" in data:
        for li in list(q.line_items):
            db.session.delete(li)
        db.session.flush()
        db.session.add_all(_build_lines(q, data["line_items"]))
    _log("UPDATE", "quotes", q.id)
    db.session.commit()
    return jsonify(q.to_dict())


@docs_bp.post("/api/quotes/<int:doc_id>/finalize")
@jwt_required()
def finalize_quote(doc_id):
    q = get_scoped_or_404(Quote, doc_id, current_company_id())
    q.finalize(current_user_id())
    _log("FINALIZE", "quotes", q.id)
    db.session.commit()
    return jsonify(q.to_dict())


# ── LPOs ───────────────────────────────────────────────────────────────────────

@docs_bp.get("/api/lpos")
@jwt_required()
def list_lpos():
    lpos = LPO.query.filter_by(company_id=current_company_id()).order_by(LPO.created_at.desc()).all()
    return jsonify([l.to_dict(include_lines=False) for l in lpos])


@docs_bp.post("/api/lpos")
@jwt_required()
def create_lpo():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    # Optional: validate quote belongs to same company
    quote_id = data.get("quote_id")
    if quote_id:
        get_scoped_or_404(Quote, quote_id, cid)

    lpo = LPO(
        company_id=cid,
        created_by=uid,
        lpo_number=data.get("lpo_number", ""),
        quote_id=quote_id,
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name", ""),
        customer_trn=data.get("customer_trn"),
        document_date=data.get("document_date"),
        due_date=data.get("due_date"),
        delivery_date=data.get("delivery_date"),
        delivery_address=data.get("delivery_address"),
        notes=data.get("notes"),
        currency=data.get("currency", "AED"),
    )
    db.session.add(lpo)
    db.session.flush()
    db.session.add_all(_build_lines(lpo, data.get("line_items", [])))
    _log("CREATE", "lpos", lpo.id)
    db.session.commit()
    return jsonify(lpo.to_dict()), 201


@docs_bp.get("/api/lpos/<int:doc_id>")
@jwt_required()
def get_lpo(doc_id):
    return jsonify(get_scoped_or_404(LPO, doc_id, current_company_id()).to_dict())


@docs_bp.patch("/api/lpos/<int:doc_id>")
@jwt_required()
def update_lpo(doc_id):
    lpo = get_scoped_or_404(LPO, doc_id, current_company_id())
    lpo.ensure_editable()
    data = request.get_json(silent=True) or {}
    for field in ("customer_name", "customer_trn", "notes", "document_date",
                  "due_date", "delivery_date", "delivery_address", "currency"):
        if field in data:
            setattr(lpo, field, data[field])
    if "line_items" in data:
        for li in list(lpo.line_items):
            db.session.delete(li)
        db.session.flush()
        db.session.add_all(_build_lines(lpo, data["line_items"]))
    _log("UPDATE", "lpos", lpo.id)
    db.session.commit()
    return jsonify(lpo.to_dict())


@docs_bp.post("/api/lpos/<int:doc_id>/finalize")
@jwt_required()
def finalize_lpo(doc_id):
    lpo = get_scoped_or_404(LPO, doc_id, current_company_id())
    lpo.finalize(current_user_id())
    _log("FINALIZE", "lpos", lpo.id)
    db.session.commit()
    return jsonify(lpo.to_dict())


# ── Invoices ───────────────────────────────────────────────────────────────────

@docs_bp.get("/api/invoices")
@jwt_required()
def list_invoices():
    invs = Invoice.query.filter_by(company_id=current_company_id()).order_by(Invoice.created_at.desc()).all()
    return jsonify([i.to_dict(include_lines=False) for i in invs])


@docs_bp.post("/api/invoices")
@jwt_required()
def create_invoice():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    lpo_id = data.get("lpo_id")
    quote_id = data.get("quote_id")
    if lpo_id:
        get_scoped_or_404(LPO, lpo_id, cid)
    if quote_id:
        get_scoped_or_404(Quote, quote_id, cid)

    inv = Invoice(
        company_id=cid,
        created_by=uid,
        invoice_number=data.get("invoice_number", ""),
        lpo_id=lpo_id,
        quote_id=quote_id,
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name", ""),
        customer_trn=data.get("customer_trn"),
        document_date=data.get("document_date"),
        due_date=data.get("due_date"),
        payment_terms=data.get("payment_terms"),
        notes=data.get("notes"),
        currency=data.get("currency", "AED"),
        buyer_vat_number=data.get("buyer_vat_number"),
        supply_type=data.get("supply_type", "B2B"),
        invoice_type_code=data.get("invoice_type_code", "388"),
    )
    db.session.add(inv)
    db.session.flush()
    db.session.add_all(_build_lines(inv, data.get("line_items", [])))
    db.session.flush()

    # Anomaly detection
    check_invoice(inv)

    _log("CREATE", "invoices", inv.id)
    db.session.commit()
    return jsonify(inv.to_dict()), 201


@docs_bp.get("/api/invoices/<int:doc_id>")
@jwt_required()
def get_invoice(doc_id):
    return jsonify(get_scoped_or_404(Invoice, doc_id, current_company_id()).to_dict())


@docs_bp.patch("/api/invoices/<int:doc_id>")
@jwt_required()
def update_invoice(doc_id):
    inv = get_scoped_or_404(Invoice, doc_id, current_company_id())
    inv.ensure_editable()
    data = request.get_json(silent=True) or {}
    for field in ("customer_name", "customer_trn", "notes", "document_date",
                  "due_date", "payment_terms", "currency", "buyer_vat_number"):
        if field in data:
            setattr(inv, field, data[field])
    if "line_items" in data:
        for li in list(inv.line_items):
            db.session.delete(li)
        db.session.flush()
        db.session.add_all(_build_lines(inv, data["line_items"]))
    _log("UPDATE", "invoices", inv.id)
    db.session.commit()
    return jsonify(inv.to_dict())


@docs_bp.post("/api/invoices/<int:doc_id>/finalize")
@jwt_required()
def finalize_invoice(doc_id):
    inv = get_scoped_or_404(Invoice, doc_id, current_company_id())
    inv.finalize(current_user_id())
    _log("FINALIZE", "invoices", inv.id)
    db.session.commit()
    return jsonify(inv.to_dict())


# ── Delivery Notes ──────────────────────────────────────────────────────────────

@docs_bp.get("/api/delivery-notes")
@jwt_required()
def list_delivery_notes():
    dns = DeliveryNote.query.filter_by(company_id=current_company_id()).order_by(DeliveryNote.created_at.desc()).all()
    return jsonify([d.to_dict(include_lines=False) for d in dns])


@docs_bp.post("/api/delivery-notes")
@jwt_required()
def create_delivery_note():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return error_response("MISSING_FIELDS", "invoice_id is required for a Delivery Note", 400)
    get_scoped_or_404(Invoice, invoice_id, cid)

    dn = DeliveryNote(
        company_id=cid,
        created_by=uid,
        delivery_note_number=data.get("delivery_note_number", ""),
        invoice_id=invoice_id,
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name", ""),
        document_date=data.get("document_date"),
        delivery_date=data.get("delivery_date"),
        delivery_address=data.get("delivery_address"),
        notes=data.get("notes"),
        currency=data.get("currency", "AED"),
    )
    db.session.add(dn)
    db.session.flush()
    db.session.add_all(_build_lines(dn, data.get("line_items", [])))
    db.session.flush()

    # Anomaly: check total vs invoice total
    check_delivery_note(dn)

    _log("CREATE", "delivery_notes", dn.id)
    db.session.commit()
    return jsonify(dn.to_dict()), 201


@docs_bp.get("/api/delivery-notes/<int:doc_id>")
@jwt_required()
def get_delivery_note(doc_id):
    return jsonify(get_scoped_or_404(DeliveryNote, doc_id, current_company_id()).to_dict())


@docs_bp.post("/api/delivery-notes/<int:doc_id>/finalize")
@jwt_required()
def finalize_delivery_note(doc_id):
    dn = get_scoped_or_404(DeliveryNote, doc_id, current_company_id())
    dn.finalize(current_user_id())
    _log("FINALIZE", "delivery_notes", dn.id)
    db.session.commit()
    return jsonify(dn.to_dict())


# ── Credit Notes ────────────────────────────────────────────────────────────────

@docs_bp.post("/api/credit-notes")
@jwt_required()
def create_credit_note():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return error_response("MISSING_FIELDS", "invoice_id is required", 400)

    inv = get_scoped_or_404(Invoice, invoice_id, cid)
    if inv.locked_at is None:
        return error_response(
            "INVOICE_NOT_LOCKED",
            "Credit notes can only be created against a finalized invoice",
            422,
        )

    cn = CreditNote(
        company_id=cid,
        created_by=uid,
        credit_note_number=data.get("credit_note_number", ""),
        invoice_id=invoice_id,
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name", inv.customer_name),
        reason=data.get("reason"),
        is_full_reversal=data.get("is_full_reversal", False),
        document_date=data.get("document_date"),
        notes=data.get("notes"),
        currency=inv.currency,
    )
    db.session.add(cn)
    db.session.flush()
    db.session.add_all(_build_lines(cn, data.get("line_items", [])))
    _log("CREATE", "credit_notes", cn.id)
    db.session.commit()
    return jsonify(cn.to_dict()), 201


@docs_bp.get("/api/credit-notes/<int:doc_id>")
@jwt_required()
def get_credit_note(doc_id):
    return jsonify(get_scoped_or_404(CreditNote, doc_id, current_company_id()).to_dict())


# ── Debit Notes ─────────────────────────────────────────────────────────────────

@docs_bp.post("/api/debit-notes")
@jwt_required()
def create_debit_note():
    cid = current_company_id()
    uid = current_user_id()
    data = request.get_json(silent=True) or {}

    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return error_response("MISSING_FIELDS", "invoice_id is required", 400)

    inv = get_scoped_or_404(Invoice, invoice_id, cid)
    if inv.locked_at is None:
        return error_response(
            "INVOICE_NOT_LOCKED",
            "Debit notes can only be created against a finalized invoice",
            422,
        )

    dn = DebitNote(
        company_id=cid,
        created_by=uid,
        debit_note_number=data.get("debit_note_number", ""),
        invoice_id=invoice_id,
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name", inv.customer_name),
        reason=data.get("reason"),
        is_full_reversal=data.get("is_full_reversal", False),
        document_date=data.get("document_date"),
        notes=data.get("notes"),
        currency=inv.currency,
    )
    db.session.add(dn)
    db.session.flush()
    db.session.add_all(_build_lines(dn, data.get("line_items", [])))
    _log("CREATE", "debit_notes", dn.id)
    db.session.commit()
    return jsonify(dn.to_dict()), 201


@docs_bp.get("/api/debit-notes/<int:doc_id>")
@jwt_required()
def get_debit_note(doc_id):
    return jsonify(get_scoped_or_404(DebitNote, doc_id, current_company_id()).to_dict())
