"""Multi-currency support — add currency and exchange_rate_to_aed to all document tables

Revision ID: 006
Revises: 005
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

_DOC_TABLES = [
    "invoices", "purchase_invoices", "lpos", "quotations",
    "credit_notes", "debit_notes", "delivery_notes", "pdcs", "receipt_vouchers",
]


def upgrade():
    for table in _DOC_TABLES:
        op.add_column(table, sa.Column(
            "currency", sa.String(3), nullable=False, server_default="AED"
        ))
        op.add_column(table, sa.Column(
            "exchange_rate_to_aed", sa.Numeric(20, 6), nullable=False, server_default="1.0"
        ))


def downgrade():
    for table in _DOC_TABLES:
        op.drop_column(table, "exchange_rate_to_aed")
        op.drop_column(table, "currency")
