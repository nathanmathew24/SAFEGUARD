"""
Phase 2 — Document model tests.
Tests CRUD, RBAC, void semantics, audit trail, integer amounts, pagination.
"""
from datetime import date
from tests.conftest import auth_header


# ---- Helpers ----

def _invoice_payload(company_id, **overrides):
    base = {
        "company_id": company_id,
        "party_name": "Acme Trading LLC",
        "document_date": "2026-07-01",
        "due_date": "2026-07-31",
        "invoice_type": "tax_invoice",
        "line_items": [
            {
                "description": "Steel pipes 6m",
                "quantity": 10,
                "unit_price": 50000,   # 500 AED in fils
                "discount_amount": 0,
                "tax_rate_bp": 500,    # 5% VAT
            }
        ],
    }
    base.update(overrides)
    return base


def _pdc_payload(company_id, **overrides):
    base = {
        "company_id": company_id,
        "party_name": "Customer Corp",
        "document_date": "2026-07-01",
        "cheque_number": "CHQ-001",
        "bank_name": "Emirates NBD",
        "cheque_date": "2026-09-01",
        "amount": 1000000,  # 10,000 AED in fils
    }
    base.update(overrides)
    return base


# ---- Create ----

def test_create_invoice(client, owner_user, company):
    rv = client.post("/api/invoices",
                     json=_invoice_payload(company.id),
                     headers=auth_header(owner_user))
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["document_number"].startswith("INV-")
    assert data["status"] == "draft"
    assert data["party_name"] == "Acme Trading LLC"
    assert len(data["line_items"]) == 1


def test_invoice_amounts_are_integer_fils(client, owner_user, company):
    rv = client.post("/api/invoices",
                     json=_invoice_payload(company.id),
                     headers=auth_header(owner_user))
    data = rv.get_json()
    # 10 × 50000 fils = 500000 fils subtotal, tax = 25000, total = 525000
    assert data["subtotal_amount"] == 500000
    assert data["tax_amount"] == 25000
    assert data["total_amount"] == 525000
    assert isinstance(data["total_amount"], int)
    assert "." not in str(data["total_amount"])


def test_document_number_unique_per_company(client, owner_user, company):
    rv1 = client.post("/api/invoices",
                      json=_invoice_payload(company.id),
                      headers=auth_header(owner_user))
    rv2 = client.post("/api/invoices",
                      json=_invoice_payload(company.id),
                      headers=auth_header(owner_user))
    n1 = rv1.get_json()["document_number"]
    n2 = rv2.get_json()["document_number"]
    assert n1 != n2
    assert n1 == "INV-2026-0001"
    assert n2 == "INV-2026-0002"


def test_create_pdc(client, owner_user, company):
    rv = client.post("/api/pdcs",
                     json=_pdc_payload(company.id),
                     headers=auth_header(owner_user))
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["document_number"].startswith("PDC-")
    assert data["pdc_status"] == "pending"
    assert data["amount"] == 1000000


def test_create_requires_party_name(client, owner_user, company):
    payload = _invoice_payload(company.id)
    del payload["party_name"]
    rv = client.post("/api/invoices", json=payload, headers=auth_header(owner_user))
    assert rv.status_code == 422


def test_create_requires_document_date(client, owner_user, company):
    payload = _invoice_payload(company.id)
    del payload["document_date"]
    rv = client.post("/api/invoices", json=payload, headers=auth_header(owner_user))
    assert rv.status_code == 422


# ---- Read ----

def test_get_invoice(client, owner_user, company):
    create_rv = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = create_rv.get_json()["id"]
    rv = client.get(f"/api/invoices/{doc_id}", headers=auth_header(owner_user))
    assert rv.status_code == 200
    assert rv.get_json()["id"] == doc_id


def test_get_nonexistent_returns_404(client, owner_user):
    rv = client.get("/api/invoices/99999", headers=auth_header(owner_user))
    assert rv.status_code == 404


def test_list_invoices_pagination(client, owner_user, company):
    for _ in range(3):
        client.post("/api/invoices",
                    json=_invoice_payload(company.id),
                    headers=auth_header(owner_user))
    rv = client.get(f"/api/invoices?company_id={company.id}&page=1&per_page=2",
                    headers=auth_header(owner_user))
    data = rv.get_json()
    assert data["total"] == 3
    assert len(data["data"]) == 2
    assert data["page"] == 1


def test_list_filter_by_status(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(owner_user))

    rv = client.get(f"/api/invoices?company_id={company.id}&status=confirmed",
                    headers=auth_header(owner_user))
    data = rv.get_json()
    assert data["total"] == 1
    assert data["data"][0]["status"] == "confirmed"


# ---- Update ----

def test_update_draft_invoice(client, owner_user, company, db):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]

    rv = client.put(f"/api/invoices/{doc_id}",
                    json={"party_name": "Updated Corp", "notes": "Updated note"},
                    headers=auth_header(owner_user))
    assert rv.status_code == 200
    assert rv.get_json()["party_name"] == "Updated Corp"


def test_cannot_update_confirmed_document(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(owner_user))

    rv = client.put(f"/api/invoices/{doc_id}",
                    json={"notes": "should fail"},
                    headers=auth_header(owner_user))
    assert rv.status_code == 409
    assert rv.get_json()["error"]["code"] == "IMMUTABLE"


# ---- Confirm ----

def test_confirm_invoice(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]

    rv = client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(owner_user))
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "confirmed"


def test_confirm_already_confirmed_returns_409(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(owner_user))
    rv = client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(owner_user))
    assert rv.status_code == 409


# ---- Void ----

def test_void_invoice(client, owner_user, company, db):
    from app.models.audit_log import AuditLog, AuditAction
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]

    rv = client.post(f"/api/invoices/{doc_id}/void",
                     json={"reason": "Duplicate entry"},
                     headers=auth_header(owner_user))
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["is_voided"] is True
    assert data["status"] == "voided"
    assert data["void_reason"] == "Duplicate entry"

    db.session.expire_all()
    entry = AuditLog.query.filter_by(
        action=AuditAction.VOID
    ).order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.record_id == doc_id


def test_void_requires_reason(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.post(f"/api/invoices/{doc_id}/void",
                     json={},
                     headers=auth_header(owner_user))
    assert rv.status_code == 422


def test_cannot_void_twice(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    client.post(f"/api/invoices/{doc_id}/void",
                json={"reason": "First void"},
                headers=auth_header(owner_user))
    rv = client.post(f"/api/invoices/{doc_id}/void",
                     json={"reason": "Second void"},
                     headers=auth_header(owner_user))
    assert rv.status_code == 409


def test_no_delete_endpoint(client, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.delete(f"/api/invoices/{doc_id}", headers=auth_header(owner_user))
    assert rv.status_code == 405


# ---- RBAC ----

def test_viewer_cannot_create(client, viewer_user, company):
    rv = client.post("/api/invoices",
                     json=_invoice_payload(company.id),
                     headers=auth_header(viewer_user))
    assert rv.status_code == 403


def test_viewer_can_read(client, viewer_user, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.get(f"/api/invoices/{doc_id}", headers=auth_header(viewer_user))
    assert rv.status_code == 200


def test_ops_staff_cannot_void(client, ops_user, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.post(f"/api/invoices/{doc_id}/void",
                     json={"reason": "test"},
                     headers=auth_header(ops_user))
    assert rv.status_code == 403


def test_ops_staff_cannot_confirm(client, ops_user, owner_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(ops_user))
    assert rv.status_code == 403


def test_finance_manager_can_confirm(client, finance_user, company):
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(finance_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.post(f"/api/invoices/{doc_id}/confirm", headers=auth_header(finance_user))
    assert rv.status_code == 200


def test_unauthenticated_returns_401(client, company):
    rv = client.get(f"/api/invoices?company_id={company.id}")
    assert rv.status_code == 401


# ---- Audit trail ----

def test_audit_trail_on_create(client, owner_user, company, db):
    from app.models.audit_log import AuditLog, AuditAction
    client.post("/api/invoices",
                json=_invoice_payload(company.id),
                headers=auth_header(owner_user))
    db.session.expire_all()
    entry = AuditLog.query.filter_by(
        table_name="invoices", action=AuditAction.CREATE
    ).order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.new_values is not None
    assert entry.new_values.get("party_name") == "Acme Trading LLC"


def test_audit_trail_on_update(client, owner_user, company, db):
    from app.models.audit_log import AuditLog, AuditAction
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    client.put(f"/api/invoices/{doc_id}",
               json={"notes": "Updated"},
               headers=auth_header(owner_user))
    db.session.expire_all()
    entry = AuditLog.query.filter_by(
        table_name="invoices", action=AuditAction.UPDATE
    ).order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.old_values is not None
    assert entry.new_values is not None


def test_audit_trail_on_void(client, owner_user, company, db):
    from app.models.audit_log import AuditLog, AuditAction
    rv_create = client.post("/api/invoices",
                            json=_invoice_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    client.post(f"/api/invoices/{doc_id}/void",
                json={"reason": "audit test"},
                headers=auth_header(owner_user))
    db.session.expire_all()
    entry = AuditLog.query.filter_by(
        action=AuditAction.VOID
    ).order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.new_values["void_reason"] == "audit test"


# ---- PDC status transitions ----

def test_pdc_status_pending_default(client, owner_user, company):
    rv = client.post("/api/pdcs",
                     json=_pdc_payload(company.id),
                     headers=auth_header(owner_user))
    assert rv.get_json()["pdc_status"] == "pending"


def test_pdc_update_status_to_submitted(client, owner_user, company):
    rv_create = client.post("/api/pdcs",
                            json=_pdc_payload(company.id),
                            headers=auth_header(owner_user))
    doc_id = rv_create.get_json()["id"]
    rv = client.put(f"/api/pdcs/{doc_id}",
                    json={"pdc_status": "submitted"},
                    headers=auth_header(owner_user))
    assert rv.status_code == 200
    assert rv.get_json()["pdc_status"] == "submitted"


# ---- All 9 document types create ----

def test_create_purchase_invoice(client, owner_user, company):
    rv = client.post("/api/purchase-invoices", json={
        "company_id": company.id,
        "party_name": "Al Futtaim Suppliers",
        "document_date": "2026-07-01",
        "supplier_invoice_number": "SUP-2026-099",
        "line_items": [{"description": "Cement bags", "quantity": 100,
                         "unit_price": 2000, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("PINV-")


def test_create_lpo(client, owner_user, company):
    rv = client.post("/api/lpos", json={
        "company_id": company.id,
        "party_name": "Gulf Supplies LLC",
        "document_date": "2026-07-01",
        "line_items": [{"description": "Valves", "quantity": 20,
                         "unit_price": 30000, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("LPO-")


def test_create_quotation(client, owner_user, company):
    rv = client.post("/api/quotations", json={
        "company_id": company.id,
        "party_name": "Prospective Client",
        "document_date": "2026-07-01",
        "valid_until": "2026-08-01",
        "line_items": [{"description": "Consulting", "quantity": 1,
                         "unit_price": 500000, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("QTN-")


def test_create_credit_note(client, owner_user, company):
    rv = client.post("/api/credit-notes", json={
        "company_id": company.id,
        "party_name": "Acme Trading LLC",
        "document_date": "2026-07-01",
        "reason": "Returned goods",
        "line_items": [{"description": "Returned pipes", "quantity": 2,
                         "unit_price": 50000, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("CN-")


def test_create_debit_note(client, owner_user, company):
    rv = client.post("/api/debit-notes", json={
        "company_id": company.id,
        "party_name": "Acme Trading LLC",
        "document_date": "2026-07-01",
        "reason": "Price adjustment",
        "line_items": [{"description": "Surcharge", "quantity": 1,
                         "unit_price": 10000, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("DN-")


def test_create_delivery_note(client, owner_user, company):
    rv = client.post("/api/delivery-notes", json={
        "company_id": company.id,
        "party_name": "Acme Trading LLC",
        "document_date": "2026-07-01",
        "delivery_date": "2026-07-03",
        "received_by": "John Smith",
        "items_description": "10 boxes of steel pipes",
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("DLV-")


def test_create_receipt_voucher(client, owner_user, company):
    rv = client.post("/api/receipt-vouchers", json={
        "company_id": company.id,
        "party_name": "Acme Trading LLC",
        "document_date": "2026-07-01",
        "received_from": "Acme Trading LLC",
        "amount": 525000,
        "payment_method": "bank_transfer",
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["document_number"].startswith("RV-")
