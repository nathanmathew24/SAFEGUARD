"""
Anomaly detection — five categories, conservative thresholds (tunable via config).

1. price_deviation   — >25% from historical avg (needs ≥3 data points)
2. quantity_outlier  — >3 std-dev from historical avg (needs ≥5 data points)
3. duplicate_document — same customer + same total already exists
4. missing_fields    — required fields blank (e.g. due_date)
5. total_mismatch    — DeliveryNote total ≠ its Invoice locked total
"""
import math
from datetime import datetime, timezone
from typing import Optional

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.models.anomaly_flag import AnomalyFlag
from app.models.invoice import Invoice
from app.models.line_item import LineItem
from app.models.delivery_note import DeliveryNote


def _flag(company_id, doc_type, doc_id, category, severity, message, details=None):
    flag = AnomalyFlag(
        company_id=company_id,
        document_type=doc_type,
        document_id=doc_id,
        category=category,
        severity=severity,
        message=message,
        details=details,
    )
    db.session.add(flag)


def check_invoice(invoice: Invoice):
    """Run all applicable anomaly checks for a new/updated Invoice."""
    cid = invoice.company_id
    doc_type = "invoice"
    doc_id = invoice.id

    # 1 & 2 — per-line price and quantity checks
    price_threshold = current_app.config.get("ANOMALY_PRICE_DEVIATION_PCT", 25.0)
    qty_threshold = current_app.config.get("ANOMALY_QTY_STDDEV_FACTOR", 3.0)
    price_min = current_app.config.get("ANOMALY_PRICE_MIN_SAMPLES", 3)
    qty_min = current_app.config.get("ANOMALY_QTY_MIN_SAMPLES", 5)

    for li in invoice.line_items:
        if li.product_id is None:
            continue

        # Fetch historical data from other finalized invoices for this product
        historical_lines = (
            db.session.query(LineItem)
            .join(Invoice, LineItem.invoice_id == Invoice.id)
            .filter(
                Invoice.company_id == cid,
                Invoice.status == "finalized",
                Invoice.id != invoice.id,
                LineItem.product_id == li.product_id,
            )
            .all()
        )

        prices = [float(h.unit_price) for h in historical_lines]
        qtys = [float(h.quantity) for h in historical_lines]

        # Price deviation
        if len(prices) >= price_min:
            avg_price = sum(prices) / len(prices)
            if avg_price > 0:
                deviation_pct = abs(float(li.unit_price) - avg_price) / avg_price * 100
                if deviation_pct > price_threshold:
                    _flag(
                        cid, doc_type, doc_id, "price_deviation", "high",
                        f"Line price {li.unit_price} deviates {deviation_pct:.1f}% "
                        f"from historical avg {avg_price:.2f} for product {li.product_id}",
                        {"product_id": li.product_id, "current": float(li.unit_price),
                         "avg": avg_price, "deviation_pct": deviation_pct},
                    )

        # Quantity outlier
        if len(qtys) >= qty_min:
            avg_qty = sum(qtys) / len(qtys)
            variance = sum((q - avg_qty) ** 2 for q in qtys) / len(qtys)
            std_dev = math.sqrt(variance) if variance > 0 else 0
            if std_dev > 0 and abs(float(li.quantity) - avg_qty) > qty_threshold * std_dev:
                _flag(
                    cid, doc_type, doc_id, "quantity_outlier", "medium",
                    f"Quantity {li.quantity} is more than {qty_threshold}σ from historical "
                    f"avg {avg_qty:.2f} (σ={std_dev:.2f}) for product {li.product_id}",
                    {"product_id": li.product_id, "current": float(li.quantity),
                     "avg": avg_qty, "std_dev": std_dev},
                )

    # 3 — duplicate document
    dup = (
        db.session.query(Invoice)
        .filter(
            Invoice.company_id == cid,
            Invoice.customer_id == invoice.customer_id,
            Invoice.total == invoice.total,
            Invoice.id != invoice.id,
        )
        .first()
    )
    if dup:
        _flag(
            cid, doc_type, doc_id, "duplicate_document", "high",
            f"Invoice total {invoice.total} matches existing invoice {dup.id} "
            f"for the same customer",
            {"duplicate_invoice_id": dup.id},
        )

    # 4 — missing required fields
    missing = []
    if not invoice.due_date:
        missing.append("due_date")
    if not invoice.customer_name:
        missing.append("customer_name")
    if missing:
        _flag(
            cid, doc_type, doc_id, "missing_fields", "medium",
            f"Required fields missing: {', '.join(missing)}",
            {"fields": missing},
        )


def check_delivery_note(dn: DeliveryNote):
    """Check DeliveryNote total against its locked Invoice total."""
    invoice = db.session.get(Invoice, dn.invoice_id)
    if invoice is None:
        return

    if float(dn.total) != float(invoice.total):
        _flag(
            dn.company_id, "delivery_note", dn.id, "total_mismatch", "high",
            f"DeliveryNote total {dn.total} does not match locked Invoice {invoice.id} "
            f"total {invoice.total}",
            {"dn_total": float(dn.total), "invoice_total": float(invoice.total)},
        )
