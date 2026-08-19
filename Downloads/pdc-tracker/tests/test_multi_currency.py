"""
Multi-currency tests — currency and exchange_rate_to_aed on documents.
AED is the default; non-AED documents carry an exchange rate for reporting.
"""
import pytest
from datetime import date
from tests.conftest import auth_header


def _make_invoice(client, user, company, currency="AED", exchange_rate=1.0, amount=100000):
    payload = {
        "company_id": company.id,
        "party_name": "Acme Trading LLC",
        "document_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
        "invoice_type": "tax_invoice",
        "line_items": [{
            "description": "Service",
            "quantity": 1,
            "unit_price": amount,
            "discount_amount": 0,
            "tax_rate_bp": 500,
        }],
        "currency": currency,
        "exchange_rate_to_aed": exchange_rate,
    }
    rv = client.post("/api/invoices", json=payload, headers=auth_header(user))
    assert rv.status_code == 201, rv.get_json()
    return rv.get_json()


# ─── Default currency ─────────────────────────────────────────────────────────

def test_invoice_defaults_to_aed(client, owner_user, company):
    """Invoice created without currency fields defaults to AED / rate 1.0."""
    rv = client.post("/api/invoices", json={
        "company_id": company.id,
        "party_name": "Test Party",
        "document_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
        "invoice_type": "tax_invoice",
        "line_items": [{"description": "Item", "quantity": 1, "unit_price": 50000,
                        "discount_amount": 0, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["currency"] == "AED"
    assert data["exchange_rate_to_aed"] == 1.0


# ─── Non-AED currencies ───────────────────────────────────────────────────────

def test_usd_invoice_stores_currency(client, owner_user, company):
    data = _make_invoice(client, owner_user, company, currency="USD", exchange_rate=3.672)
    assert data["currency"] == "USD"
    assert abs(data["exchange_rate_to_aed"] - 3.672) < 0.001


def test_eur_invoice_stores_currency(client, owner_user, company):
    data = _make_invoice(client, owner_user, company, currency="EUR", exchange_rate=4.01)
    assert data["currency"] == "EUR"
    assert abs(data["exchange_rate_to_aed"] - 4.01) < 0.001


def test_gbp_invoice_stores_currency(client, owner_user, company):
    data = _make_invoice(client, owner_user, company, currency="GBP", exchange_rate=4.72)
    assert data["currency"] == "GBP"


# ─── Currency persists through GET ───────────────────────────────────────────

def test_currency_persists_on_get(client, owner_user, company):
    created = _make_invoice(client, owner_user, company, currency="USD", exchange_rate=3.672)
    rv = client.get(f"/api/invoices/{created['id']}", headers=auth_header(owner_user))
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["currency"] == "USD"
    assert abs(data["exchange_rate_to_aed"] - 3.672) < 0.001


# ─── Currency persists through confirm ───────────────────────────────────────

def test_currency_persists_after_confirm(client, owner_user, company):
    created = _make_invoice(client, owner_user, company, currency="USD", exchange_rate=3.672)
    client.post(f"/api/invoices/{created['id']}/confirm", headers=auth_header(owner_user))
    rv = client.get(f"/api/invoices/{created['id']}", headers=auth_header(owner_user))
    data = rv.get_json()
    assert data["currency"] == "USD"
    assert data["status"] == "confirmed"


# ─── List includes currency ───────────────────────────────────────────────────

def test_list_invoices_includes_currency(client, owner_user, company):
    _make_invoice(client, owner_user, company, currency="EUR", exchange_rate=4.01)
    rv = client.get(f"/api/invoices?company_id={company.id}", headers=auth_header(owner_user))
    assert rv.status_code == 200
    items = rv.get_json()["data"]
    assert any(item["currency"] == "EUR" for item in items)


# ─── Other document types support currency ───────────────────────────────────

def test_lpo_supports_currency(client, owner_user, company):
    rv = client.post("/api/lpos", json={
        "company_id": company.id,
        "party_name": "Supplier Co",
        "document_date": date.today().isoformat(),
        "currency": "USD",
        "exchange_rate_to_aed": 3.672,
        "line_items": [{"description": "Goods", "quantity": 2, "unit_price": 25000,
                        "discount_amount": 0, "tax_rate_bp": 500}],
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["currency"] == "USD"


def test_delivery_note_supports_currency(client, owner_user, company):
    rv = client.post("/api/delivery-notes", json={
        "company_id": company.id,
        "party_name": "Buyer Ltd",
        "document_date": date.today().isoformat(),
        "currency": "EUR",
        "exchange_rate_to_aed": 4.01,
    }, headers=auth_header(owner_user))
    assert rv.status_code == 201
    assert rv.get_json()["currency"] == "EUR"


# ─── AED invoices unaffected (backward compat) ───────────────────────────────

def test_existing_aed_workflow_unchanged(client, owner_user, company):
    """Full AED create → confirm → list flow works identically after currency addition."""
    inv = _make_invoice(client, owner_user, company)
    assert inv["currency"] == "AED"
    assert inv["exchange_rate_to_aed"] == 1.0

    client.post(f"/api/invoices/{inv['id']}/confirm", headers=auth_header(owner_user))
    rv = client.get(f"/api/invoices?company_id={company.id}", headers=auth_header(owner_user))
    assert rv.status_code == 200
