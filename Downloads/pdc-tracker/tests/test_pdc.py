"""
Phase 4 tests: PDC status transitions, reminder logic, overdue detection,
endpoint RBAC, WhatsApp sender (mocked).
"""
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from tests.conftest import auth_header


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_pdc(db, company, user, direction="received", status="pending",
             cheque_date=None, reminder_sent=False):
    from app.models.pdc import PDC
    if cheque_date is None:
        cheque_date = date.today() + timedelta(days=10)
    pdc = PDC(
        company_id=company.id,
        document_number=f"PDC-TEST-{id(cheque_date)}",
        party_name="Test Supplier LLC",
        document_date=date.today(),
        cheque_date=cheque_date,
        cheque_number="CHQ-001",
        bank_name="Emirates NBD",
        amount=500000,  # AED 5000 in fils
        pdc_direction=direction,
        pdc_status=status,
        reminder_sent=reminder_sent,
        created_by=user.id,
    )
    db.session.add(pdc)
    db.session.commit()
    return pdc


# ── PDC model ────────────────────────────────────────────────────────────────

class TestPDCModel:
    def test_to_dict_includes_phase4_fields(self, db, company, owner_user):
        pdc = make_pdc(db, company, owner_user)
        d = pdc.to_dict()
        assert d["pdc_direction"] == "received"
        assert d["reminder_sent"] is False
        assert d["reminder_sent_at"] is None
        assert d["cleared_at"] is None
        assert d["bounced_at"] is None
        assert d["submitted_at"] is None

    def test_amount_stored_as_integer_fils(self, db, company, owner_user):
        pdc = make_pdc(db, company, owner_user)
        assert isinstance(pdc.amount, int)
        assert pdc.amount == 500000

    def test_direction_defaults_to_received(self, db, company, owner_user):
        pdc = make_pdc(db, company, owner_user)
        assert pdc.pdc_direction == "received"

    def test_issued_direction(self, db, company, owner_user):
        pdc = make_pdc(db, company, owner_user, direction="issued")
        assert pdc.pdc_direction == "issued"


# ── Status machine ────────────────────────────────────────────────────────────

class TestPDCStatusMachine:
    def test_pending_to_submitted(self, db, company, owner_user):
        from app.services.pdc_service import mark_submitted
        pdc = make_pdc(db, company, owner_user, status="pending")
        updated = mark_submitted(pdc.id, owner_user.id, "127.0.0.1")
        assert updated.pdc_status == "submitted"
        assert updated.submitted_at is not None

    def test_submitted_to_cleared(self, db, company, owner_user):
        from app.services.pdc_service import mark_submitted, mark_cleared
        pdc = make_pdc(db, company, owner_user, status="pending")
        mark_submitted(pdc.id, owner_user.id, "127.0.0.1")
        updated = mark_cleared(pdc.id, owner_user.id, "127.0.0.1")
        assert updated.pdc_status == "cleared"
        assert updated.cleared_at is not None

    def test_submitted_to_bounced(self, db, company, owner_user):
        from app.services.pdc_service import mark_submitted, mark_bounced
        pdc = make_pdc(db, company, owner_user, status="pending")
        mark_submitted(pdc.id, owner_user.id, "127.0.0.1")
        updated = mark_bounced(pdc.id, owner_user.id, "127.0.0.1")
        assert updated.pdc_status == "bounced"
        assert updated.bounced_at is not None

    def test_pending_to_cancelled(self, db, company, owner_user):
        from app.services.pdc_service import mark_cancelled
        pdc = make_pdc(db, company, owner_user, status="pending")
        updated = mark_cancelled(pdc.id, owner_user.id, "127.0.0.1")
        assert updated.pdc_status == "cancelled"

    def test_cleared_cannot_transition(self, db, company, owner_user):
        from app.services.pdc_service import mark_submitted, mark_cleared, mark_bounced
        pdc = make_pdc(db, company, owner_user, status="pending")
        mark_submitted(pdc.id, owner_user.id, "127.0.0.1")
        mark_cleared(pdc.id, owner_user.id, "127.0.0.1")
        with pytest.raises(ValueError, match="Cannot transition"):
            mark_bounced(pdc.id, owner_user.id, "127.0.0.1")

    def test_bounced_cannot_transition_to_cleared(self, db, company, owner_user):
        from app.services.pdc_service import mark_submitted, mark_bounced, mark_cleared
        pdc = make_pdc(db, company, owner_user, status="pending")
        mark_submitted(pdc.id, owner_user.id, "127.0.0.1")
        mark_bounced(pdc.id, owner_user.id, "127.0.0.1")
        with pytest.raises(ValueError, match="Cannot transition"):
            mark_cleared(pdc.id, owner_user.id, "127.0.0.1")

    def test_pending_cannot_skip_to_cleared(self, db, company, owner_user):
        from app.services.pdc_service import mark_cleared
        pdc = make_pdc(db, company, owner_user, status="pending")
        with pytest.raises(ValueError, match="Cannot transition"):
            mark_cleared(pdc.id, owner_user.id, "127.0.0.1")

    def test_status_change_writes_audit_log(self, db, company, owner_user):
        from app.services.pdc_service import mark_submitted
        from app.models.audit_log import AuditLog
        pdc = make_pdc(db, company, owner_user, status="pending")
        mark_submitted(pdc.id, owner_user.id, "127.0.0.1")
        logs = AuditLog.query.filter_by(table_name="pdcs", record_id=pdc.id).all()
        assert len(logs) >= 1


# ── Reminder logic ────────────────────────────────────────────────────────────

class TestPDCReminderLogic:
    @patch("app.services.pdc_service.send_whatsapp")
    def test_send_pdc_reminder_received(self, mock_send, db, company, owner_user):
        from app.services.pdc_service import send_pdc_reminder
        pdc = make_pdc(db, company, owner_user,
                       cheque_date=date.today() + timedelta(days=2))
        send_pdc_reminder(pdc, company)
        assert pdc.reminder_sent is True
        assert pdc.reminder_sent_at is not None
        assert mock_send.call_count >= 1
        # verify finance and owner both notified
        recipients = [call.args[0] for call in mock_send.call_args_list]
        assert company.finance_whatsapp in recipients
        assert company.owner_whatsapp in recipients

    @patch("app.services.pdc_service.send_whatsapp")
    def test_send_pdc_reminder_issued_only_owner(self, mock_send, db, company, owner_user):
        from app.services.pdc_service import send_pdc_reminder
        pdc = make_pdc(db, company, owner_user, direction="issued",
                       cheque_date=date.today() + timedelta(days=3))
        send_pdc_reminder(pdc, company)
        recipients = [call.args[0] for call in mock_send.call_args_list]
        assert company.owner_whatsapp in recipients
        assert company.finance_whatsapp not in recipients

    @patch("app.services.pdc_service.send_whatsapp")
    def test_send_pdc_escalation(self, mock_send, db, company, owner_user):
        from app.services.pdc_service import send_pdc_escalation
        pdc = make_pdc(db, company, owner_user,
                       cheque_date=date.today() - timedelta(days=3))
        send_pdc_escalation(pdc, company)
        assert mock_send.call_count == 1
        assert mock_send.call_args.args[0] == company.owner_whatsapp
        assert "URGENT" in mock_send.call_args.args[1]

    @patch("app.services.pdc_service.send_whatsapp")
    def test_no_send_when_whatsapp_not_configured(self, mock_send, db, company, owner_user):
        from app.services.pdc_service import send_pdc_reminder
        pdc = make_pdc(db, company, owner_user,
                       cheque_date=date.today() + timedelta(days=2))
        # Clear phone numbers
        company.owner_whatsapp = None
        company.finance_whatsapp = None
        send_pdc_reminder(pdc, company)
        mock_send.assert_not_called()


# ── WhatsApp sender unit tests ────────────────────────────────────────────────

class TestWhatsAppSender:
    @patch("app.utils.whatsapp_sender.requests.post")
    def test_send_success(self, mock_post):
        from app.utils.whatsapp_sender import _send_once
        mock_post.return_value = MagicMock(status_code=200)
        result = _send_once("tok", "1234", "+971500000000", "test message")
        assert result is True
        assert mock_post.called

    @patch("app.utils.whatsapp_sender.requests.post")
    def test_send_failure_returns_false(self, mock_post):
        from app.utils.whatsapp_sender import _send_once
        mock_post.return_value = MagicMock(status_code=400)
        result = _send_once("tok", "1234", "+971500000000", "test message")
        assert result is False

    @patch("app.utils.whatsapp_sender.requests.post")
    def test_send_exception_returns_false(self, mock_post):
        import requests as req_lib
        from app.utils.whatsapp_sender import _send_once
        mock_post.side_effect = req_lib.RequestException("timeout")
        result = _send_once("tok", "1234", "+971500000000", "test message")
        assert result is False

    def test_send_whatsapp_no_config_skips_silently(self):
        import os
        from app.utils.whatsapp_sender import send_whatsapp
        # Env vars are empty in test config
        # Should not raise — just logs a warning
        send_whatsapp("+971500000000", "hello", "test")


# ── API endpoints ─────────────────────────────────────────────────────────────

class TestPDCEndpoints:
    def test_list_received_requires_auth(self, client):
        resp = client.get("/api/pdc/received")
        assert resp.status_code == 401

    def test_list_received(self, client, db, company, owner_user):
        make_pdc(db, company, owner_user, direction="received")
        resp = client.get("/api/pdc/received",
                          headers=auth_header(owner_user))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) == 1
        assert data[0]["pdc_direction"] == "received"

    def test_list_issued(self, client, db, company, owner_user):
        make_pdc(db, company, owner_user, direction="issued")
        make_pdc(db, company, owner_user, direction="received")
        resp = client.get("/api/pdc/issued",
                          headers=auth_header(owner_user))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert all(d["pdc_direction"] == "issued" for d in data)

    def test_mark_submitted_finance_manager(self, client, db, company,
                                            finance_user):
        pdc = make_pdc(db, company, finance_user)
        resp = client.post(f"/api/pdc/{pdc.id}/mark-submitted",
                           headers=auth_header(finance_user))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["pdc_status"] == "submitted"

    def test_mark_submitted_viewer_forbidden(self, client, db, company,
                                              owner_user, viewer_user):
        pdc = make_pdc(db, company, owner_user)
        resp = client.post(f"/api/pdc/{pdc.id}/mark-submitted",
                           headers=auth_header(viewer_user))
        assert resp.status_code == 403

    def test_mark_cleared_finance_manager(self, client, db, company, finance_user):
        pdc = make_pdc(db, company, finance_user, status="submitted")
        resp = client.post(f"/api/pdc/{pdc.id}/mark-cleared",
                           headers=auth_header(finance_user))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["pdc_status"] == "cleared"

    def test_mark_bounced_owner_only(self, client, db, company,
                                     owner_user, finance_user):
        pdc = make_pdc(db, company, owner_user, status="submitted")
        # Finance manager cannot bounce
        resp = client.post(f"/api/pdc/{pdc.id}/mark-bounced",
                           headers=auth_header(finance_user))
        assert resp.status_code == 403
        # Owner can bounce
        resp = client.post(f"/api/pdc/{pdc.id}/mark-bounced",
                           headers=auth_header(owner_user))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["pdc_status"] == "bounced"

    def test_mark_submitted_invalid_transition(self, client, db, company, owner_user):
        pdc = make_pdc(db, company, owner_user, status="cleared")
        resp = client.post(f"/api/pdc/{pdc.id}/mark-submitted",
                           headers=auth_header(owner_user))
        assert resp.status_code == 422

    def test_mark_cancelled_owner(self, client, db, company, owner_user):
        pdc = make_pdc(db, company, owner_user, status="pending")
        resp = client.post(f"/api/pdc/{pdc.id}/mark-cancelled",
                           headers=auth_header(owner_user))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["pdc_status"] == "cancelled"


# ── Overdue endpoint ──────────────────────────────────────────────────────────

class TestOverdueEndpoint:
    def test_overdue_requires_auth(self, client):
        resp = client.get("/api/pdc/payments/overdue")
        assert resp.status_code == 401

    def test_overdue_viewer_forbidden(self, client, viewer_user):
        resp = client.get("/api/pdc/payments/overdue",
                          headers=auth_header(viewer_user))
        assert resp.status_code == 403

    def test_overdue_returns_past_due_pdcs(self, client, db, company, owner_user):
        # PDC past cheque_date still pending
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() - timedelta(days=5),
                 status="pending")
        resp = client.get("/api/pdc/payments/overdue",
                          headers=auth_header(owner_user))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) == 1
        assert data[0]["overdue_type"] == "pdc"
        assert data[0]["days_overdue"] == 5

    def test_overdue_excludes_future_pdcs(self, client, db, company, owner_user):
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() + timedelta(days=5))
        resp = client.get("/api/pdc/payments/overdue",
                          headers=auth_header(owner_user))
        assert resp.status_code == 200
        assert len(resp.get_json()["data"]) == 0

    def test_overdue_excludes_cleared_pdcs(self, client, db, company, owner_user):
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() - timedelta(days=5),
                 status="cleared")
        resp = client.get("/api/pdc/payments/overdue",
                          headers=auth_header(owner_user))
        assert resp.status_code == 200
        assert len(resp.get_json()["data"]) == 0

    def test_overdue_sorted_by_days_descending(self, client, db, company, owner_user):
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() - timedelta(days=2))
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() - timedelta(days=10))
        resp = client.get("/api/pdc/payments/overdue",
                          headers=auth_header(owner_user))
        data = resp.get_json()["data"]
        assert data[0]["days_overdue"] >= data[1]["days_overdue"]


# ── Scheduler jobs (unit, no HTTP) ────────────────────────────────────────────

class TestSchedulerJobs:
    @patch("app.services.pdc_service.send_whatsapp")
    def test_pdc_reminder_job_sends_reminder(self, mock_send, app, db, company, owner_user):
        from app.services.scheduler_service import _pdc_reminder_job
        # PDC due in 2 days — within 3-day reminder window
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() + timedelta(days=2))
        _pdc_reminder_job(app)
        assert mock_send.called

    @patch("app.services.pdc_service.send_whatsapp")
    def test_pdc_reminder_job_skips_already_reminded(self, mock_send, app, db, company, owner_user):
        from app.services.scheduler_service import _pdc_reminder_job
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() + timedelta(days=2),
                 reminder_sent=True)
        _pdc_reminder_job(app)
        mock_send.assert_not_called()

    @patch("app.services.pdc_service.send_whatsapp")
    def test_pdc_reminder_job_escalates_overdue(self, mock_send, app, db, company, owner_user):
        from app.services.scheduler_service import _pdc_reminder_job
        make_pdc(db, company, owner_user,
                 cheque_date=date.today() - timedelta(days=2),
                 reminder_sent=False)
        _pdc_reminder_job(app)
        # escalation message contains URGENT
        call_bodies = [c.args[1] for c in mock_send.call_args_list]
        assert any("URGENT" in b for b in call_bodies)

    def test_overdue_scan_job_logs_audit(self, app, db, company, owner_user):
        from app.services.scheduler_service import _overdue_scan_job
        from app.models.invoice import Invoice
        from app.models.audit_log import AuditLog
        # Confirmed invoice past due_date
        inv = Invoice(
            company_id=company.id,
            document_number="INV-OVRD-001",
            party_name="Test Buyer",
            document_date=date.today() - timedelta(days=30),
            due_date=date.today() - timedelta(days=10),
            invoice_type="tax_invoice",
            status="confirmed",
            payment_status="unpaid",
            created_by=owner_user.id,
        )
        db.session.add(inv)
        db.session.commit()
        before = AuditLog.query.count()
        _overdue_scan_job(app)
        after = AuditLog.query.count()
        assert after > before
