"""
Phase 0 security verification tests.

These tests MUST pass before anything else is considered done.
They prove that the cross-tenant access vulnerability is fixed.

Run against real PostgreSQL:
  TEST_DATABASE_URL=postgresql://docuflow:changeme@localhost:5432/docuflow_test pytest tests/test_phase0_security.py -v
"""
import pytest
from tests.conftest import register_and_login


# ── Cross-tenant isolation ────────────────────────────────────────────────────

def test_cross_tenant_read_returns_404(client):
    """Company B cannot read Company A's invoice — gets 404, not 403."""
    headers_a, cid_a = register_and_login(client, "Company A", "a@example.com")
    headers_b, cid_b = register_and_login(client, "Company B", "b@example.com")

    # Company A creates an invoice
    r = client.post("/api/invoices", json={
        "invoice_number": "INV-001",
        "customer_name": "Customer X",
        "document_date": "2026-01-01",
    }, headers=headers_a)
    assert r.status_code == 201
    invoice_id = r.get_json()["id"]

    # Company B tries to read it — must get 404 (not 403, not the invoice)
    r2 = client.get(f"/api/invoices/{invoice_id}", headers=headers_b)
    assert r2.status_code == 404, f"Expected 404, got {r2.status_code}: {r2.get_json()}"


def test_cross_tenant_finalize_returns_404(client):
    """Company B cannot finalize Company A's invoice."""
    headers_a, _ = register_and_login(client, "Company A2", "a2@example.com")
    headers_b, _ = register_and_login(client, "Company B2", "b2@example.com")

    r = client.post("/api/invoices", json={
        "invoice_number": "INV-002",
        "customer_name": "Customer Y",
        "document_date": "2026-01-01",
    }, headers=headers_a)
    invoice_id = r.get_json()["id"]

    r2 = client.post(f"/api/invoices/{invoice_id}/finalize", headers=headers_b)
    assert r2.status_code == 404


def test_cross_tenant_quote_read_returns_404(client):
    headers_a, _ = register_and_login(client, "Company A3", "a3@example.com")
    headers_b, _ = register_and_login(client, "Company B3", "b3@example.com")

    r = client.post("/api/quotes", json={
        "quote_number": "Q-001",
        "customer_name": "Customer Z",
        "document_date": "2026-01-01",
    }, headers=headers_a)
    quote_id = r.get_json()["id"]

    assert client.get(f"/api/quotes/{quote_id}", headers=headers_b).status_code == 404


def test_cross_tenant_pdc_read_returns_404(client):
    headers_a, _ = register_and_login(client, "Company A4", "a4@example.com")
    headers_b, _ = register_and_login(client, "Company B4", "b4@example.com")

    r = client.post("/api/pdcs", json={
        "cheque_number": "CHQ001",
        "bank_name": "Emirates NBD",
        "cheque_date": "2026-06-01",
        "amount": "5000.00",
    }, headers=headers_a)
    assert r.status_code == 201
    pdc_id = r.get_json()["id"]

    assert client.get(f"/api/pdcs/{pdc_id}", headers=headers_b).status_code == 404


# ── Locking ────────────────────────────────────────────────────────────────────

def test_locked_document_returns_423(client):
    """Editing a finalized document must return 423 Locked."""
    headers, _ = register_and_login(client, "Lock Test Co", "lock@example.com")

    r = client.post("/api/invoices", json={
        "invoice_number": "INV-LOCK",
        "customer_name": "Lock Customer",
        "document_date": "2026-01-01",
    }, headers=headers)
    inv_id = r.get_json()["id"]

    # Finalize it
    assert client.post(f"/api/invoices/{inv_id}/finalize", headers=headers).status_code == 200

    # Now try to edit — must get 423
    r3 = client.patch(f"/api/invoices/{inv_id}", json={"notes": "attempt edit"}, headers=headers)
    assert r3.status_code == 423, f"Expected 423, got {r3.status_code}: {r3.get_json()}"


def test_credit_note_requires_locked_invoice(client):
    """Cannot create a CreditNote against an unlocked invoice."""
    headers, _ = register_and_login(client, "CN Test Co", "cn@example.com")

    r = client.post("/api/invoices", json={
        "invoice_number": "INV-CN",
        "customer_name": "CN Customer",
        "document_date": "2026-01-01",
    }, headers=headers)
    inv_id = r.get_json()["id"]

    # Try to create credit note without finalizing first
    r2 = client.post("/api/credit-notes", json={
        "invoice_id": inv_id,
        "credit_note_number": "CN-001",
        "customer_name": "CN Customer",
    }, headers=headers)
    assert r2.status_code == 422
    assert "not locked" in r2.get_json().get("message", "").lower() or \
           "finalized" in r2.get_json().get("message", "").lower()


# ── Auth ───────────────────────────────────────────────────────────────────────

def test_unauthenticated_access_returns_401(client):
    assert client.get("/api/invoices").status_code == 401


def test_login_with_wrong_password_returns_401(client):
    register_and_login(client, "Auth Test Co", "auth@example.com")
    r = client.post("/api/auth/login", json={
        "email": "auth@example.com",
        "password": "WrongPassword!",
    })
    assert r.status_code == 401


# ── Document chain ─────────────────────────────────────────────────────────────

def test_full_document_chain(client):
    """Quote → LPO → Invoice → Finalize → DeliveryNote — full happy path."""
    headers, _ = register_and_login(client, "Chain Co", "chain@example.com")

    # Create Quote
    r = client.post("/api/quotes", json={
        "quote_number": "Q-CHAIN-001",
        "customer_name": "Chain Customer",
        "document_date": "2026-01-01",
        "line_items": [{"description": "Widget A", "quantity": 10, "unit_price": 50}],
    }, headers=headers)
    assert r.status_code == 201
    quote_id = r.get_json()["id"]

    # Create LPO from Quote
    r2 = client.post("/api/lpos", json={
        "lpo_number": "LPO-CHAIN-001",
        "quote_id": quote_id,
        "customer_name": "Chain Customer",
        "document_date": "2026-01-02",
        "line_items": [{"description": "Widget A", "quantity": 10, "unit_price": 50}],
    }, headers=headers)
    assert r2.status_code == 201
    lpo_id = r2.get_json()["id"]

    # Create Invoice from LPO
    r3 = client.post("/api/invoices", json={
        "invoice_number": "INV-CHAIN-001",
        "lpo_id": lpo_id,
        "customer_name": "Chain Customer",
        "document_date": "2026-01-05",
        "due_date": "2026-02-05",
        "line_items": [{"description": "Widget A", "quantity": 10, "unit_price": 50}],
    }, headers=headers)
    assert r3.status_code == 201
    inv_id = r3.get_json()["id"]
    assert r3.get_json()["total"] == 500.0

    # Finalize Invoice
    r4 = client.post(f"/api/invoices/{inv_id}/finalize", headers=headers)
    assert r4.status_code == 200
    assert r4.get_json()["status"] == "finalized"
    assert r4.get_json()["locked_at"] is not None

    # Create Delivery Note
    r5 = client.post("/api/delivery-notes", json={
        "delivery_note_number": "DN-CHAIN-001",
        "invoice_id": inv_id,
        "customer_name": "Chain Customer",
        "document_date": "2026-01-06",
        "line_items": [{"description": "Widget A", "quantity": 10, "unit_price": 50}],
    }, headers=headers)
    assert r5.status_code == 201
