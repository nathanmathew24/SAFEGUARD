"""
PDF generation: Jinja2 (autoescape=True) → WeasyPrint → Fernet-encrypted file.
Signed download URLs use HMAC-SHA256 with JWT_SECRET; expire after 1 hour.
"""
import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from flask import current_app
from jinja2 import Environment, FileSystemLoader, select_autoescape


# ── Template registry: doc_type slug → (template_name, has_line_items) ──────

_TEMPLATES = {
    "invoice":          ("pdf/invoice.html",          True),
    "purchase_invoice": ("pdf/purchase_invoice.html", True),
    "lpo":              ("pdf/lpo.html",               True),
    "quotation":        ("pdf/quotation.html",         True),
    "credit_note":      ("pdf/credit_note.html",       True),
    "debit_note":       ("pdf/debit_note.html",        True),
    "delivery_note":    ("pdf/delivery_note.html",     False),
    "receipt_voucher":  ("pdf/receipt_voucher.html",   False),
}


def _jinja_env(app) -> Environment:
    templates_dir = os.path.join(app.root_path, "templates")
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),  # XSS prevention — always on
    )
    return env


def _fernet(app) -> Fernet:
    key = app.config.get("ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY not configured")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def render_pdf(doc, doc_type: str, company, app) -> bytes:
    """
    Render document to PDF bytes.
    doc must be a model instance with to_dict() and optionally .line_items.
    Never accepts raw user HTML — server templates only.
    """
    template_name, has_line_items = _TEMPLATES[doc_type]

    env = _jinja_env(app)
    template = env.get_template(template_name)

    context = {
        "doc": doc,
        "company": company,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "line_items": doc.line_items if has_line_items and hasattr(doc, "line_items") else [],
    }
    html_str = template.render(**context)

    # Lazy import — WeasyPrint requires GTK system libs not available everywhere
    from weasyprint import HTML  # noqa: PLC0415
    pdf_bytes = HTML(string=html_str, base_url=app.root_path).write_pdf()
    return pdf_bytes


def save_pdf(pdf_bytes: bytes, doc_type: str, doc_id: int, version: int, app) -> str:
    """Encrypt and write PDF to disk. Returns the stored file path."""
    upload_dir = app.config.get("UPLOAD_DIR", "uploads")
    pdf_dir = os.path.join(upload_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    filename = f"{doc_type}_{doc_id}_v{version}_{uuid.uuid4().hex}.pdf.enc"
    path = os.path.join(pdf_dir, filename)

    encrypted = _fernet(app).encrypt(pdf_bytes)
    with open(path, "wb") as f:
        f.write(encrypted)

    return path


def load_pdf(file_path: str, app) -> bytes:
    """Decrypt and return PDF bytes from disk."""
    with open(file_path, "rb") as f:
        encrypted = f.read()
    return _fernet(app).decrypt(encrypted)


# ── Signed URL ────────────────────────────────────────────────────────────────

_URL_TTL = 3600  # 1 hour in seconds


def generate_signed_token(pdf_id: int, app) -> str:
    """
    Returns an HMAC-SHA256 signed token: '{pdf_id}:{expires}:{sig}'.
    Never exposes the file path to the client.
    """
    secret = app.config["JWT_SECRET"]
    expires = int(time.time()) + _URL_TTL
    payload = f"{pdf_id}:{expires}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_signed_token(token: str, app) -> int | None:
    """
    Verifies the signed token. Returns pdf_id on success, None on failure.
    Constant-time comparison prevents timing attacks.
    """
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        pdf_id_str, expires_str, sig = parts
        expires = int(expires_str)
        if time.time() > expires:
            return None  # expired
        secret = app.config["JWT_SECRET"]
        payload = f"{pdf_id_str}:{expires_str}"
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        return int(pdf_id_str)
    except Exception:
        return None
