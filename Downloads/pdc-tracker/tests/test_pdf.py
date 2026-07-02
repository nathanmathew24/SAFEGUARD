"""
Phase 5 tests: PDF generation, signed URL, RBAC, content injection prevention.
WeasyPrint is mocked — tests verify routing, encryption, auth, and token logic.
"""
import time
from datetime import date, datetime, timezone
from unittest.mock import patch, MagicMock

from tests.conftest import auth_header


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_invoice(db, company, user):
    from app.models.invoice import Invoice
    inv = Invoice(
        company_id=company.id,
        document_number="INV-PDF-001",
        party_name="Test Buyer LLC",
        document_date=date.today(),
        due_date=date.today(),
        invoice_type="tax_invoice",
        status="confirmed",
        payment_status="unpaid",
        subtotal_amount=100000,
        tax_amount=5000,
        total_amount=105000,
        created_by=user.id,
    )
    db.session.add(inv)
    db.session.commit()
    return inv


def make_receipt_voucher(db, company, user):
    from app.models.receipt_voucher import ReceiptVoucher
    rv = ReceiptVoucher(
        company_id=company.id,
        document_number="RV-PDF-001",
        party_name="Test Payer",
        document_date=date.today(),
        received_from="Test Payer LLC",
        amount=105000,
        payment_method="cash",
        created_by=user.id,
    )
    db.session.add(rv)
    db.session.commit()
    return rv


FAKE_PDF = b"%PDF-1.4 fake pdf content"


# ── Signed URL token logic ────────────────────────────────────────────────────

class TestSignedToken:
    def test_generate_and_verify(self, app):
        from app.utils.pdf_generator import generate_signed_token, verify_signed_token
        token = generate_signed_token(42, app)
        assert verify_signed_token(token, app) == 42

    def test_tampered_token_rejected(self, app):
        from app.utils.pdf_generator import generate_signed_token, verify_signed_token
        token = generate_signed_token(42, app)
        parts = token.split(":")
        parts[2] = "badsig" + "x" * 58
        tampered = ":".join(parts)
        assert verify_signed_token(tampered, app) is None

    def test_expired_token_rejected(self, app):
        from app.utils.pdf_generator import verify_signed_token
        import hashlib, hmac
        secret = app.config["JWT_SECRET"]
        expires = int(time.time()) - 10  # already expired
        payload = f"99:{expires}"
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        token = f"99:{expires}:{sig}"
        assert verify_signed_token(token, app) is None

    def test_malformed_token_rejected(self, app):
        from app.utils.pdf_generator import verify_signed_token
        assert verify_signed_token("notavalidtoken", app) is None
        assert verify_signed_token("", app) is None
        assert verify_signed_token("a:b", app) is None


# ── PDF renderer unit ─────────────────────────────────────────────────────────

class TestPDFRenderer:
    @patch("weasyprint.HTML")
    def test_render_invoice(self, mock_html, app, db, company, owner_user):
        from app.utils.pdf_generator import render_pdf
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        result = render_pdf(inv, "invoice", company, app)
        assert result == FAKE_PDF
        assert mock_html.called

    @patch("weasyprint.HTML")
    def test_render_receipt_voucher_no_line_items(self, mock_html, app, db, company, owner_user):
        from app.utils.pdf_generator import render_pdf
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        rv = make_receipt_voucher(db, company, owner_user)
        result = render_pdf(rv, "receipt_voucher", company, app)
        assert result == FAKE_PDF

    @patch("weasyprint.HTML")
    def test_autoescape_prevents_xss(self, mock_html, app, db, company, owner_user):
        """Party name with <script> tag must be escaped in rendered HTML."""
        from app.utils.pdf_generator import _jinja_env
        from app.models.invoice import Invoice
        inv = Invoice(
            company_id=company.id,
            document_number="INV-XSS-001",
            party_name='<script>alert("xss")</script>',
            document_date=date.today(),
            invoice_type="tax_invoice",
            status="draft",
            payment_status="unpaid",
            subtotal_amount=0, tax_amount=0, total_amount=0,
            created_by=owner_user.id,
        )
        db.session.add(inv)
        db.session.commit()

        env = _jinja_env(app)
        tmpl = env.get_template("pdf/invoice.html")
        html = tmpl.render(
            doc=inv,
            company=company,
            generated_at="2026-07-02 12:00 UTC",
            line_items=[],
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    @patch("weasyprint.HTML")
    def test_save_and_load_pdf_roundtrip(self, mock_html, app, tmp_path):
        from app.utils.pdf_generator import save_pdf, load_pdf
        import os
        app.config["UPLOAD_DIR"] = str(tmp_path)
        path = save_pdf(FAKE_PDF, "invoice", 1, 1, app)
        assert os.path.exists(path)
        # File on disk must be encrypted (not raw PDF)
        with open(path, "rb") as f:
            on_disk = f.read()
        assert on_disk != FAKE_PDF
        # Decrypted must match original
        recovered = load_pdf(path, app)
        assert recovered == FAKE_PDF


# ── API endpoints ─────────────────────────────────────────────────────────────

class TestPDFEndpoints:
    @patch("weasyprint.HTML")
    def test_generate_pdf_owner(self, mock_html, client, db, company,
                                owner_user, tmp_path, app):
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        resp = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                           headers=auth_header(owner_user))
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["doc_type"] == "invoice"
        assert data["version"] == 1
        assert "download_token" in data

    @patch("weasyprint.HTML")
    def test_generate_pdf_finance_manager(self, mock_html, client, db, company,
                                          finance_user, tmp_path, app):
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, finance_user)
        resp = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                           headers=auth_header(finance_user))
        assert resp.status_code == 201

    def test_generate_pdf_viewer_forbidden(self, client, db, company,
                                           owner_user, viewer_user):
        inv = make_invoice(db, company, owner_user)
        resp = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                           headers=auth_header(viewer_user))
        assert resp.status_code == 403

    def test_generate_pdf_unauthenticated(self, client, db, company, owner_user):
        inv = make_invoice(db, company, owner_user)
        resp = client.post(f"/api/invoice/{inv.id}/generate-pdf")
        assert resp.status_code == 401

    def test_generate_pdf_unknown_doc_type(self, client, owner_user):
        resp = client.post("/api/unknown_type/1/generate-pdf",
                           headers=auth_header(owner_user))
        assert resp.status_code == 404

    @patch("weasyprint.HTML")
    def test_versions_increment(self, mock_html, client, db, company,
                                owner_user, tmp_path, app):
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        r1 = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                         headers=auth_header(owner_user))
        r2 = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                         headers=auth_header(owner_user))
        assert r1.get_json()["data"]["version"] == 1
        assert r2.get_json()["data"]["version"] == 2

    @patch("weasyprint.HTML")
    def test_download_via_signed_token(self, mock_html, client, db, company,
                                       owner_user, tmp_path, app):
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        gen_resp = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                               headers=auth_header(owner_user))
        token = gen_resp.get_json()["data"]["download_token"]

        dl_resp = client.get(f"/api/pdf/download/{token}",
                             headers=auth_header(owner_user))
        assert dl_resp.status_code == 200
        assert dl_resp.content_type == "application/pdf"
        assert dl_resp.data == FAKE_PDF

    def test_download_invalid_token(self, client, owner_user):
        resp = client.get("/api/pdf/download/badtoken123",
                          headers=auth_header(owner_user))
        assert resp.status_code == 403

    def test_download_requires_auth(self, client):
        resp = client.get("/api/pdf/download/sometoken")
        assert resp.status_code == 401

    @patch("weasyprint.HTML")
    def test_get_download_token_returns_latest(self, mock_html, client, db,
                                               company, owner_user, tmp_path, app):
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        # Generate twice
        client.post(f"/api/invoice/{inv.id}/generate-pdf",
                    headers=auth_header(owner_user))
        client.post(f"/api/invoice/{inv.id}/generate-pdf",
                    headers=auth_header(owner_user))

        resp = client.get(f"/api/invoice/{inv.id}/download",
                          headers=auth_header(owner_user))
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["version"] == 2
        assert "download_token" in data

    def test_get_download_token_no_pdf_yet(self, client, db, company, owner_user):
        inv = make_invoice(db, company, owner_user)
        resp = client.get(f"/api/invoice/{inv.id}/download",
                          headers=auth_header(owner_user))
        assert resp.status_code == 404

    @patch("weasyprint.HTML")
    def test_generate_pdf_writes_audit_log(self, mock_html, client, db, company,
                                           owner_user, tmp_path, app):
        from app.models.audit_log import AuditLog
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        before = AuditLog.query.count()
        client.post(f"/api/invoice/{inv.id}/generate-pdf",
                    headers=auth_header(owner_user))
        assert AuditLog.query.count() > before

    @patch("weasyprint.HTML")
    def test_download_writes_audit_log(self, mock_html, client, db, company,
                                       owner_user, tmp_path, app):
        from app.models.audit_log import AuditLog
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        inv = make_invoice(db, company, owner_user)
        gen_resp = client.post(f"/api/invoice/{inv.id}/generate-pdf",
                               headers=auth_header(owner_user))
        token = gen_resp.get_json()["data"]["download_token"]
        before = AuditLog.query.count()
        client.get(f"/api/pdf/download/{token}", headers=auth_header(owner_user))
        assert AuditLog.query.count() > before

    @patch("weasyprint.HTML")
    def test_receipt_voucher_pdf_generates(self, mock_html, client, db, company,
                                           owner_user, tmp_path, app):
        app.config["UPLOAD_DIR"] = str(tmp_path)
        mock_html.return_value.write_pdf.return_value = FAKE_PDF
        rv = make_receipt_voucher(db, company, owner_user)
        resp = client.post(f"/api/receipt_voucher/{rv.id}/generate-pdf",
                           headers=auth_header(owner_user))
        assert resp.status_code == 201
