"""
Phase 3 — Extraction pipeline tests.
All Claude API calls are mocked — no live API calls in CI.
"""
import io
import os
import json
from unittest.mock import patch, MagicMock
from tests.conftest import auth_header

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _pdf_bytes():
    with open(os.path.join(FIXTURES, "sample_invoice.pdf"), "rb") as f:
        return f.read()


def _png_bytes():
    with open(os.path.join(FIXTURES, "sample_invoice.png"), "rb") as f:
        return f.read()


def _mock_classify_response(doc_type="invoice", confidence=0.95):
    """Build a mock Anthropic message response for the classifier."""
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps({"document_type": doc_type, "confidence": confidence}))]
    msg.usage = MagicMock(input_tokens=150, output_tokens=30)
    return msg


def _mock_extract_response(fields: dict):
    """Build a mock Anthropic message response for the extractor."""
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps({"fields": fields}))]
    msg.usage = MagicMock(input_tokens=400, output_tokens=200)
    return msg


def _high_confidence_fields():
    return {
        "party_name":    {"value": "Acme Trading LLC", "confidence": 0.97},
        "document_date": {"value": "2026-07-01",       "confidence": 0.95},
        "total_amount":  {"value": 525000,              "confidence": 0.92},
        "subtotal_amount": {"value": 500000,            "confidence": 0.91},
        "tax_amount":    {"value": 25000,               "confidence": 0.90},
    }


def _low_confidence_fields():
    fields = _high_confidence_fields()
    fields["total_amount"]["confidence"] = 0.60  # below 0.85 threshold
    return fields


# ---- Upload tests ----

def test_upload_pdf_success(client, owner_user, company, tmp_path):
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 201, rv.get_json()
    data = rv.get_json()
    assert "upload_id" in data
    assert data["mime_type"] == "application/pdf"


def test_upload_png_success(client, owner_user, company):
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_png_bytes()), "invoice.png"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 201
    assert rv.get_json()["mime_type"] == "image/png"


def test_upload_rejects_exe(client, owner_user, company):
    fake_exe = b"MZ\x90\x00" + b"\x00" * 100  # DOS/PE magic bytes
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(fake_exe), "malware.exe"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 422
    assert rv.get_json()["error"]["code"] == "INVALID_FILE"


def test_upload_rejects_png_with_wrong_extension(client, owner_user, company):
    """PNG bytes but .exe extension — should be rejected on extension check."""
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_png_bytes()), "disguised.exe"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 422


def test_upload_rejects_oversized(client, owner_user, company):
    big = b"\x89PNG\r\n\x1a\n" + b"A" * (11 * 1024 * 1024)
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(big), "big.png"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 422
    assert rv.get_json()["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_requires_auth(client, company):
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 401


def test_upload_requires_company_id(client, owner_user):
    rv = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf")},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 422


# ---- Extraction pipeline tests ----

def test_extract_high_confidence_creates_document(client, owner_user, company, db, tmp_path):
    """When all critical fields have confidence >= 0.85, document is auto-created."""
    # Upload
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice", 0.95),
            _mock_extract_response(_high_confidence_fields()),
        ]
        rv = client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    assert rv.status_code == 200, rv.get_json()
    data = rv.get_json()
    assert data["status"] == "created"
    assert "document_id" in data
    assert data["document_type"] == "invoice"


def test_extract_low_confidence_creates_review(client, owner_user, company, db):
    """When a critical field has confidence < 0.85, ExtractionReview is created."""
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice", 0.93),
            _mock_extract_response(_low_confidence_fields()),
        ]
        rv = client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "pending_review"
    assert "review_id" in data
    assert "total_amount" in data["low_confidence_fields"]


def test_extraction_logs_claude_calls(client, owner_user, company, db):
    """Every Claude call writes an ExtractionLog entry."""
    from app.models.extraction_log import ExtractionLog

    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_high_confidence_fields()),
        ]
        client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    db.session.expire_all()
    logs = ExtractionLog.query.filter_by(upload_id=upload_id).all()
    assert len(logs) == 2
    steps = {l.agent_step for l in logs}
    assert steps == {"classify", "extract"}
    for log in logs:
        assert log.success is True
        assert log.input_tokens == 150 or log.input_tokens == 400


def test_extraction_truncated_io_in_log(client, owner_user, company, db):
    """ExtractionLog stores only truncated I/O — never full prompt."""
    from app.models.extraction_log import ExtractionLog

    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_high_confidence_fields()),
        ]
        client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    db.session.expire_all()
    for log in ExtractionLog.query.filter_by(upload_id=upload_id).all():
        if log.truncated_input:
            assert len(log.truncated_input) <= 500
        if log.truncated_output:
            assert len(log.truncated_output) <= 500


# ---- Review queue tests ----

def test_review_queue_list(client, owner_user, company, db):
    """GET /api/extractions/pending returns pending reviews."""
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_low_confidence_fields()),
        ]
        client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    rv = client.get(f"/api/extractions/pending?company_id={company.id}",
                    headers=auth_header(owner_user))
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["total"] == 1
    assert data["data"][0]["status"] == "pending"


def test_get_review(client, owner_user, company):
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_low_confidence_fields()),
        ]
        rv_ext = client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    review_id = rv_ext.get_json()["review_id"]
    rv = client.get(f"/api/extractions/{review_id}", headers=auth_header(owner_user))
    assert rv.status_code == 200
    assert rv.get_json()["id"] == review_id
    assert rv.get_json()["extracted_fields"] is not None


def test_approve_review_creates_document(client, owner_user, company, db):
    """Approving a review with corrections creates the Phase 2 document."""
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_low_confidence_fields()),
        ]
        rv_ext = client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    review_id = rv_ext.get_json()["review_id"]
    rv = client.post(
        f"/api/extractions/{review_id}/approve",
        json={
            "company_id": company.id,
            "corrected_fields": {"total_amount": 525000},
        },
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 200, rv.get_json()
    assert "document_id" in rv.get_json()

    # Review is now approved
    rv2 = client.get(f"/api/extractions/{review_id}", headers=auth_header(owner_user))
    assert rv2.get_json()["status"] == "approved"


def test_reject_review(client, owner_user, company, db):
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_low_confidence_fields()),
        ]
        rv_ext = client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    review_id = rv_ext.get_json()["review_id"]
    rv = client.post(
        f"/api/extractions/{review_id}/reject",
        json={"company_id": company.id, "reason": "Unreadable scan"},
        headers=auth_header(owner_user),
    )
    assert rv.status_code == 200

    rv2 = client.get(f"/api/extractions/{review_id}", headers=auth_header(owner_user))
    assert rv2.get_json()["status"] == "rejected"


def test_cannot_approve_already_approved(client, owner_user, company):
    rv_up = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(_pdf_bytes()), "invoice.pdf"), "company_id": company.id},
        content_type="multipart/form-data",
        headers=auth_header(owner_user),
    )
    upload_id = rv_up.get_json()["upload_id"]

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = [
            _mock_classify_response("invoice"),
            _mock_extract_response(_low_confidence_fields()),
        ]
        rv_ext = client.post(
            "/api/extractions",
            json={"upload_id": upload_id, "company_id": company.id},
            headers=auth_header(owner_user),
        )

    review_id = rv_ext.get_json()["review_id"]
    client.post(f"/api/extractions/{review_id}/approve",
                json={"company_id": company.id},
                headers=auth_header(owner_user))
    rv = client.post(f"/api/extractions/{review_id}/approve",
                     json={"company_id": company.id},
                     headers=auth_header(owner_user))
    assert rv.status_code == 422


# ---- RBAC tests ----

def test_viewer_cannot_trigger_extraction(client, viewer_user, company):
    rv = client.post(
        "/api/extractions",
        json={"upload_id": 1, "company_id": company.id},
        headers=auth_header(viewer_user),
    )
    assert rv.status_code == 403


def test_ops_staff_cannot_approve(client, ops_user, company):
    rv = client.post(
        "/api/extractions/1/approve",
        json={"company_id": company.id},
        headers=auth_header(ops_user),
    )
    assert rv.status_code == 403


def test_ops_staff_cannot_reject(client, ops_user, company):
    rv = client.post(
        "/api/extractions/1/reject",
        json={"company_id": company.id, "reason": "test"},
        headers=auth_header(ops_user),
    )
    assert rv.status_code == 403


def test_unauthenticated_cannot_view_pending(client, company):
    rv = client.get(f"/api/extractions/pending?company_id={company.id}")
    assert rv.status_code == 401


# ---- Sanitization test ----

def test_sanitize_strips_control_chars():
    from app.utils.ocr import sanitize_text
    dirty = "Invoice\x00Date: 2026-07-01\x01\x02Amount: 5250"
    clean = sanitize_text(dirty)
    assert "\x00" not in clean
    assert "\x01" not in clean
    assert "Invoice" in clean
    assert "Amount: 5250" in clean


def test_sanitize_limits_length():
    from app.utils.ocr import sanitize_text
    long_text = "A" * 10000
    result = sanitize_text(long_text)
    assert len(result) <= 8000
