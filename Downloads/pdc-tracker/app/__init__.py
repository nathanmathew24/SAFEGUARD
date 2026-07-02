from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, migrate, bcrypt, limiter
from config import get_config


def create_app(config_object=None):
    load_dotenv()

    app = Flask(__name__)

    if config_object is None:
        app.config.from_object(get_config())
    else:
        app.config.from_object(config_object)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    limiter.init_app(app)

    # Import models so Alembic/migrate detects them
    with app.app_context():
        from app.models import (  # noqa: F401
            company, user, refresh_token, audit_log,
            document_sequence, line_item,
            invoice, purchase_invoice, lpo, quotation,
            credit_note, debit_note, delivery_note, pdc, receipt_voucher,
            uploaded_file, extraction_review, extraction_log,
        )

        # Register document types in the service registry
        from app.services.document_service import register_doc_type
        from app.models.invoice import Invoice
        from app.models.purchase_invoice import PurchaseInvoice
        from app.models.lpo import LPO
        from app.models.quotation import Quotation
        from app.models.credit_note import CreditNote
        from app.models.debit_note import DebitNote
        from app.models.delivery_note import DeliveryNote
        from app.models.pdc import PDC
        from app.models.receipt_voucher import ReceiptVoucher

        register_doc_type("invoice", Invoice, "invoice", has_line_items=True)
        register_doc_type("purchase_invoice", PurchaseInvoice, "purchase_invoice", has_line_items=True)
        register_doc_type("lpo", LPO, "lpo", has_line_items=True)
        register_doc_type("quotation", Quotation, "quotation", has_line_items=True)
        register_doc_type("credit_note", CreditNote, "credit_note", has_line_items=True)
        register_doc_type("debit_note", DebitNote, "debit_note", has_line_items=True)
        register_doc_type("delivery_note", DeliveryNote, "delivery_note", has_line_items=False)
        register_doc_type("pdc", PDC, "pdc", has_line_items=False)
        register_doc_type("receipt_voucher", ReceiptVoucher, "receipt_voucher", has_line_items=False)

    # Phase 1 blueprints
    from app.api.health import health_bp
    from app.api.auth import auth_bp
    from app.api.audit import audit_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(audit_bp, url_prefix="/api")

    # Phase 3 upload + extraction blueprints
    from app.api.upload import upload_bp
    from app.api.extractions import extractions_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(extractions_bp)

    # Phase 2 document blueprints
    from app.api.documents import make_document_blueprint

    doc_blueprints = [
        ("invoice",          "/api/invoices"),
        ("purchase_invoice", "/api/purchase-invoices"),
        ("lpo",              "/api/lpos"),
        ("quotation",        "/api/quotations"),
        ("credit_note",      "/api/credit-notes"),
        ("debit_note",       "/api/debit-notes"),
        ("delivery_note",    "/api/delivery-notes"),
        ("pdc",              "/api/pdcs"),
        ("receipt_voucher",  "/api/receipt-vouchers"),
    ]
    for slug, prefix in doc_blueprints:
        bp = make_document_blueprint(slug, prefix)
        app.register_blueprint(bp)

    # Phase 4 PDC endpoints
    from app.api.pdc import pdc_bp
    app.register_blueprint(pdc_bp)

    # Phase 4 scheduler — only start in non-testing environments
    if not app.config.get("TESTING", False):
        from app.services.scheduler_service import init_scheduler
        init_scheduler(app)

    # Global error handlers — never expose internals
    from app.utils.errors import register_error_handlers

    register_error_handlers(app)

    return app
