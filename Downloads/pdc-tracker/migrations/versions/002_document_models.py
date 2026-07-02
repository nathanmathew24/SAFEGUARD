"""Document models — Phase 2

Revision ID: 002
Revises: 001
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Enums ----
    op.execute("""
        CREATE TYPE docstatus AS ENUM ('draft', 'confirmed', 'voided')
    """)
    op.execute("""
        CREATE TYPE invoicetype AS ENUM ('standard', 'proforma', 'tax_invoice')
    """)
    op.execute("""
        CREATE TYPE paymentmethod AS ENUM ('cash', 'bank_transfer', 'cheque', 'pdc')
    """)
    op.execute("""
        CREATE TYPE paymentstatus AS ENUM ('unpaid', 'partial', 'paid')
    """)
    op.execute("""
        CREATE TYPE pdcstatus AS ENUM ('pending', 'submitted', 'cleared', 'bounced', 'cancelled')
    """)
    op.execute("""
        CREATE TYPE rvpaymentmethod AS ENUM ('cash', 'bank_transfer', 'cheque')
    """)

    # ---- document_sequences ----
    op.create_table(
        "document_sequences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("last_number", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "doc_type", "year", name="uq_doc_sequence"),
    )

    # Shared column definitions for DocumentMixin (used inline per table)
    def shared_cols():
        return [
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("document_number", sa.String(50), nullable=False),
            sa.Column("status", sa.Enum("draft", "confirmed", "voided",
                                        name="docstatus", create_type=False),
                      nullable=False, server_default="draft"),
            sa.Column("party_name", sa.String(255), nullable=False),
            sa.Column("party_trn", sa.String(50), nullable=True),
            sa.Column("document_date", sa.Date(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("reference_number", sa.String(100), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_voided", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("void_reason", sa.Text(), nullable=True),
            sa.Column("voided_by", sa.Integer(), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        ]

    # ---- invoices ----
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("invoice_type",
                  sa.Enum("standard", "proforma", "tax_invoice",
                          name="invoicetype", create_type=False),
                  nullable=False, server_default="tax_invoice"),
        sa.Column("subtotal_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payment_method",
                  sa.Enum("cash", "bank_transfer", "cheque", "pdc",
                          name="paymentmethod", create_type=False),
                  nullable=True),
        sa.Column("payment_status",
                  sa.Enum("unpaid", "partial", "paid",
                          name="paymentstatus", create_type=False),
                  nullable=False, server_default="unpaid"),
        sa.Column("amount_paid", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_company_id", "invoices", ["company_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_document_date", "invoices", ["document_date"])

    # ---- purchase_invoices ----
    op.create_table(
        "purchase_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("supplier_invoice_number", sa.String(100), nullable=True),
        sa.Column("subtotal_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payment_method",
                  sa.Enum("cash", "bank_transfer", "cheque", "pdc",
                          name="paymentmethod", create_type=False),
                  nullable=True),
        sa.Column("payment_status",
                  sa.Enum("unpaid", "partial", "paid",
                          name="paymentstatus", create_type=False),
                  nullable=False, server_default="unpaid"),
        sa.Column("amount_paid", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pinv_company_id", "purchase_invoices", ["company_id"])
    op.create_index("ix_pinv_status", "purchase_invoices", ["status"])

    # ---- lpos ----
    op.create_table(
        "lpos",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("delivery_expected_date", sa.Date(), nullable=True),
        sa.Column("subtotal_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lpos_company_id", "lpos", ["company_id"])

    # ---- quotations ----
    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("subtotal_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("converted_to_invoice_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["converted_to_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotations_company_id", "quotations", ["company_id"])

    # ---- credit_notes ----
    op.create_table(
        "credit_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("linked_invoice_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["linked_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cn_company_id", "credit_notes", ["company_id"])

    # ---- debit_notes ----
    op.create_table(
        "debit_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("linked_invoice_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["linked_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dn_company_id", "debit_notes", ["company_id"])

    # ---- delivery_notes ----
    op.create_table(
        "delivery_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("linked_invoice_id", sa.Integer(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("received_by", sa.String(255), nullable=True),
        sa.Column("items_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["linked_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_delnote_company_id", "delivery_notes", ["company_id"])

    # ---- pdcs ----
    op.create_table(
        "pdcs",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("cheque_number", sa.String(100), nullable=False),
        sa.Column("bank_name", sa.String(255), nullable=False),
        sa.Column("cheque_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("submission_reminder_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("pdc_status",
                  sa.Enum("pending", "submitted", "cleared", "bounced", "cancelled",
                          name="pdcstatus", create_type=False),
                  nullable=False, server_default="pending"),
        sa.Column("linked_invoice_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["linked_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pdcs_company_id", "pdcs", ["company_id"])
    op.create_index("ix_pdcs_cheque_date", "pdcs", ["cheque_date"])
    op.create_index("ix_pdcs_pdc_status", "pdcs", ["pdc_status"])

    # ---- receipt_vouchers ----
    op.create_table(
        "receipt_vouchers",
        sa.Column("id", sa.Integer(), nullable=False),
        *shared_cols(),
        sa.Column("received_from", sa.String(255), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payment_method",
                  sa.Enum("cash", "bank_transfer", "cheque",
                          name="rvpaymentmethod", create_type=False),
                  nullable=False),
        sa.Column("linked_invoice_id", sa.Integer(), nullable=True),
        sa.Column("bank_reference", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["linked_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rv_company_id", "receipt_vouchers", ["company_id"])

    # ---- line_items ----
    op.create_table(
        "line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("discount_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tax_rate_bp", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("line_total", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_line_items_doc", "line_items", ["document_type", "document_id"])


def downgrade():
    op.drop_table("line_items")
    op.drop_table("receipt_vouchers")
    op.drop_table("pdcs")
    op.drop_table("delivery_notes")
    op.drop_table("debit_notes")
    op.drop_table("credit_notes")
    op.drop_table("quotations")
    op.drop_table("lpos")
    op.drop_table("purchase_invoices")
    op.drop_table("invoices")
    op.drop_table("document_sequences")
    op.execute("DROP TYPE IF EXISTS rvpaymentmethod")
    op.execute("DROP TYPE IF EXISTS pdcstatus")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS paymentmethod")
    op.execute("DROP TYPE IF EXISTS invoicetype")
    op.execute("DROP TYPE IF EXISTS docstatus")
