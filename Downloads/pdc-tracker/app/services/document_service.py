from datetime import datetime, timezone

from app.extensions import db
from app.models.line_item import LineItem
from app.models.document_sequence import next_document_number
from app.models.audit_log import AuditAction
from app.services import audit_service

# Maps url-slug → (ModelClass, doc_type_key, has_line_items)
_REGISTRY = {}


def register_doc_type(slug, model_cls, doc_type_key, has_line_items=True):
    _REGISTRY[slug] = (model_cls, doc_type_key, has_line_items)


def _get_reg(slug):
    entry = _REGISTRY.get(slug)
    if entry is None:
        raise KeyError(f"Unknown document type: {slug}")
    return entry


# ---------- Line item helpers ----------

def _build_line_items(lines_data, doc_type_key, document_id):
    items = []
    for i, ld in enumerate(lines_data):
        qty = int(ld["quantity"])
        unit_price = int(ld["unit_price"])
        discount = int(ld.get("discount_amount", 0))
        tax_bp = int(ld.get("tax_rate_bp", 500))
        total = LineItem.compute_total(qty, unit_price, discount, tax_bp)
        li = LineItem(
            document_id=document_id,
            document_type=doc_type_key,
            description=ld["description"],
            quantity=qty,
            unit_price=unit_price,
            discount_amount=discount,
            tax_rate_bp=tax_bp,
            line_total=total,
            sort_order=i,
        )
        items.append(li)
    return items


def _compute_totals(line_items):
    """Return (subtotal_fils, tax_fils, total_fils) from a list of LineItem objects."""
    total = sum(li.line_total for li in line_items)
    # tax portion: line_total includes tax; back-calculate
    # subtotal = sum of (qty*unit_price - discount), tax = sum of tax portions
    subtotal = 0
    tax = 0
    for li in line_items:
        base = li.quantity * li.unit_price - li.discount_amount
        t = base * li.tax_rate_bp // 10000
        subtotal += base
        tax += t
    return subtotal, tax, total


def _delete_line_items(doc_type_key, document_id):
    LineItem.query.filter_by(
        document_type=doc_type_key, document_id=document_id
    ).delete(synchronize_session=False)


# ---------- Public API ----------

def create_document(slug, data, user_id, ip):
    model_cls, doc_type_key, has_lines = _get_reg(slug)

    doc = model_cls()
    doc.company_id = int(data["company_id"])
    doc.party_name = data["party_name"].strip()
    doc.party_trn = data.get("party_trn")
    doc.document_date = data["document_date"]
    doc.due_date = data.get("due_date")
    doc.reference_number = data.get("reference_number")
    doc.notes = data.get("notes")
    doc.status = "draft"
    doc.is_voided = False
    doc.created_by = user_id
    doc.created_at = datetime.now(timezone.utc)
    doc.updated_at = datetime.now(timezone.utc)

    _apply_extra_fields(doc, data)

    # Generate document number before flush — column is NOT NULL
    doc.document_number = next_document_number(doc.company_id, doc_type_key)

    db.session.add(doc)
    db.session.flush()  # get doc.id

    line_items = []
    if has_lines and data.get("line_items"):
        line_items = _build_line_items(data["line_items"], doc_type_key, doc.id)
        for li in line_items:
            db.session.add(li)
        db.session.flush()
        _apply_totals(doc, line_items)

    db.session.flush()

    audit_service.log_event(
        action=AuditAction.CREATE,
        table_name=model_cls.__tablename__,
        record_id=doc.id,
        new_values=doc.to_dict(),
        user_id=user_id,
        ip_address=ip,
    )
    db.session.commit()
    return doc


def get_document(slug, doc_id):
    model_cls, _, _ = _get_reg(slug)
    return db.session.get(model_cls, doc_id)


def list_documents(slug, company_id, status=None, page=1, per_page=20):
    model_cls, _, _ = _get_reg(slug)
    q = model_cls.query.filter_by(company_id=company_id)
    if status:
        q = q.filter_by(status=status)
    q = q.order_by(model_cls.id.desc())
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def update_document(slug, doc_id, data, user_id, ip):
    model_cls, doc_type_key, has_lines = _get_reg(slug)
    doc = db.session.get(model_cls, doc_id)

    if doc is None:
        return None, "not_found"
    if doc.status == "confirmed":
        return None, "immutable"
    if doc.is_voided:
        return None, "voided"

    old_values = doc.to_dict()

    for field in ("party_name", "party_trn", "document_date", "due_date",
                  "reference_number", "notes"):
        if field in data:
            v = data[field]
            if field == "party_name" and v:
                v = v.strip()
            setattr(doc, field, v)

    _apply_extra_fields(doc, data)
    doc.updated_at = datetime.now(timezone.utc)

    if has_lines and "line_items" in data:
        _delete_line_items(doc_type_key, doc.id)
        line_items = _build_line_items(data["line_items"], doc_type_key, doc.id)
        for li in line_items:
            db.session.add(li)
        db.session.flush()
        _apply_totals(doc, line_items)

    db.session.flush()

    audit_service.log_event(
        action=AuditAction.UPDATE,
        table_name=model_cls.__tablename__,
        record_id=doc.id,
        old_values=old_values,
        new_values=doc.to_dict(),
        user_id=user_id,
        ip_address=ip,
    )
    db.session.commit()
    return doc, None


def confirm_document(slug, doc_id, user_id, ip):
    model_cls, _, _ = _get_reg(slug)
    doc = db.session.get(model_cls, doc_id)

    if doc is None:
        return None, "not_found"
    if doc.is_voided:
        return None, "voided"
    if doc.status == "confirmed":
        return None, "already_confirmed"

    old_status = doc.status
    doc.status = "confirmed"
    doc.updated_at = datetime.now(timezone.utc)
    db.session.flush()

    audit_service.log_event(
        action=AuditAction.UPDATE,
        table_name=model_cls.__tablename__,
        record_id=doc.id,
        old_values={"status": old_status},
        new_values={"status": "confirmed"},
        user_id=user_id,
        ip_address=ip,
    )
    db.session.commit()
    return doc, None


def void_document(slug, doc_id, reason, user_id, ip):
    model_cls, _, _ = _get_reg(slug)
    doc = db.session.get(model_cls, doc_id)

    if doc is None:
        return None, "not_found"
    if doc.is_voided:
        return None, "already_voided"

    old_values = doc.to_dict()
    doc.is_voided = True
    doc.void_reason = reason
    doc.voided_by = user_id
    doc.voided_at = datetime.now(timezone.utc)
    doc.status = "voided"
    doc.updated_at = datetime.now(timezone.utc)
    db.session.flush()

    audit_service.log_event(
        action=AuditAction.VOID,
        table_name=model_cls.__tablename__,
        record_id=doc.id,
        old_values=old_values,
        new_values={"is_voided": True, "void_reason": reason, "status": "voided"},
        user_id=user_id,
        ip_address=ip,
    )
    db.session.commit()
    return doc, None


# ---------- Field helpers ----------

def _apply_extra_fields(doc, data):
    """Copy document-type-specific fields from data dict onto model."""
    extra = {
        "invoice_type", "subtotal_amount", "tax_amount", "total_amount",
        "payment_method", "payment_status", "amount_paid",
        "supplier_invoice_number",
        "delivery_expected_date",
        "valid_until", "converted_to_invoice_id",
        "linked_invoice_id", "reason",
        "delivery_date", "received_by", "items_description",
        "cheque_number", "bank_name", "cheque_date", "amount",
        "submission_reminder_days", "pdc_status",
        "received_from", "bank_reference",
        "currency", "exchange_rate_to_aed",
    }
    for field in extra:
        if field in data and hasattr(doc, field):
            setattr(doc, field, data[field])


def _apply_totals(doc, line_items):
    """Set subtotal/tax/total on models that have those fields."""
    subtotal, tax, total = _compute_totals(line_items)
    if hasattr(doc, "subtotal_amount"):
        doc.subtotal_amount = subtotal
    if hasattr(doc, "tax_amount"):
        doc.tax_amount = tax
    if hasattr(doc, "total_amount"):
        doc.total_amount = total
    elif hasattr(doc, "amount"):
        doc.amount = total
