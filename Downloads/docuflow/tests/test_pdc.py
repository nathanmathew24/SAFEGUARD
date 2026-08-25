"""
PDC state machine tests.

Verifies:
- Valid transitions succeed
- Illegal transitions raise 400 (ValueError → error handler)
- bounced → pending_deposit (re-presentation) works
- JSON history is appended per transition
"""
import pytest
from tests.conftest import register_and_login


def _create_pdc(client, headers):
    r = client.post("/api/pdcs", json={
        "cheque_number": "CHQ-TEST-001",
        "bank_name": "Abu Dhabi Commercial Bank",
        "cheque_date": "2026-06-30",
        "amount": "10000.00",
        "currency": "AED",
        "drawer_name": "Acme Trading LLC",
    }, headers=headers)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["id"]


def test_pdc_initial_state_is_received(client):
    headers, _ = register_and_login(client, "PDC Co 1", "pdc1@test.com")
    pdc_id = _create_pdc(client, headers)
    r = client.get(f"/api/pdcs/{pdc_id}", headers=headers)
    assert r.get_json()["pdc_status"] == "received"


def test_pdc_valid_transition_chain(client):
    headers, _ = register_and_login(client, "PDC Co 2", "pdc2@test.com")
    pdc_id = _create_pdc(client, headers)

    def transition(to):
        r = client.post(f"/api/pdcs/{pdc_id}/transition",
                        json={"to_status": to, "note": f"moving to {to}"},
                        headers=headers)
        assert r.status_code == 200, f"transition to {to} failed: {r.get_json()}"
        return r.get_json()

    data = transition("pending_deposit")
    assert data["pdc_status"] == "pending_deposit"
    assert len(data["history"]) == 1

    data = transition("deposited")
    assert data["pdc_status"] == "deposited"
    assert len(data["history"]) == 2

    data = transition("cleared")
    assert data["pdc_status"] == "cleared"
    assert len(data["history"]) == 3


def test_pdc_bounce_and_re_present(client):
    headers, _ = register_and_login(client, "PDC Co 3", "pdc3@test.com")
    pdc_id = _create_pdc(client, headers)

    def t(to):
        r = client.post(f"/api/pdcs/{pdc_id}/transition",
                        json={"to_status": to}, headers=headers)
        assert r.status_code == 200, r.get_json()
        return r.get_json()

    t("pending_deposit")
    t("deposited")
    t("bounced")

    data = t("pending_deposit")  # re-presentation after bounce
    assert data["pdc_status"] == "pending_deposit"
    assert len(data["history"]) == 4


def test_pdc_illegal_transition_returns_400(client):
    headers, _ = register_and_login(client, "PDC Co 4", "pdc4@test.com")
    pdc_id = _create_pdc(client, headers)

    # Cannot go received → cleared (must go through pending_deposit first)
    r = client.post(f"/api/pdcs/{pdc_id}/transition",
                    json={"to_status": "cleared"}, headers=headers)
    assert r.status_code == 400


def test_pdc_cleared_is_terminal(client):
    headers, _ = register_and_login(client, "PDC Co 5", "pdc5@test.com")
    pdc_id = _create_pdc(client, headers)

    for s in ("pending_deposit", "deposited", "cleared"):
        client.post(f"/api/pdcs/{pdc_id}/transition",
                    json={"to_status": s}, headers=headers)

    # cleared is terminal
    r = client.post(f"/api/pdcs/{pdc_id}/transition",
                    json={"to_status": "bounced"}, headers=headers)
    assert r.status_code == 400


def test_pdc_history_records_transitions(client):
    headers, _ = register_and_login(client, "PDC Co 6", "pdc6@test.com")
    pdc_id = _create_pdc(client, headers)

    client.post(f"/api/pdcs/{pdc_id}/transition",
                json={"to_status": "pending_deposit", "note": "bank ready"}, headers=headers)

    r = client.get(f"/api/pdcs/{pdc_id}", headers=headers)
    history = r.get_json()["history"]
    assert len(history) == 1
    assert history[0]["from"] == "received"
    assert history[0]["to"] == "pending_deposit"
    assert history[0]["note"] == "bank ready"
    assert "at" in history[0]
    assert "by" in history[0]
