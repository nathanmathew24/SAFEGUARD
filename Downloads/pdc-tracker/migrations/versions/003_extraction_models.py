"""Extraction models — Phase 3

Revision ID: 003
Revises: 002
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE extractionstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE reviewstatus AS ENUM ('pending', 'approved', 'rejected')")

    # ---- uploaded_files ----
    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extraction_status",
                  sa.Enum("pending", "processing", "completed", "failed",
                          name="extractionstatus", create_type=False),
                  nullable=False, server_default="pending"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_uploaded_files_company_id", "uploaded_files", ["company_id"])
    op.create_index("ix_uploaded_files_uploaded_by", "uploaded_files", ["uploaded_by"])

    # ---- extraction_reviews ----
    op.create_table(
        "extraction_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extracted_fields", sa.JSON(), nullable=True),
        sa.Column("low_confidence_fields", sa.JSON(), nullable=True),
        sa.Column("status",
                  sa.Enum("pending", "approved", "rejected",
                          name="reviewstatus", create_type=False),
                  nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_document_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_extraction_reviews_company_id", "extraction_reviews", ["company_id"])
    op.create_index("ix_extraction_reviews_status", "extraction_reviews", ["status"])

    # ---- extraction_logs ----
    op.create_table(
        "extraction_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("agent_step", sa.String(50), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("truncated_input", sa.Text(), nullable=True),
        sa.Column("truncated_output", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_extraction_logs_upload_id", "extraction_logs", ["upload_id"])


def downgrade():
    op.drop_table("extraction_logs")
    op.drop_table("extraction_reviews")
    op.drop_table("uploaded_files")
    op.execute("DROP TYPE IF EXISTS reviewstatus")
    op.execute("DROP TYPE IF EXISTS extractionstatus")
