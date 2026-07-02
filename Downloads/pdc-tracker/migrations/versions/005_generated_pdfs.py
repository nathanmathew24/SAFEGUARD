"""Generated PDFs tracking — Phase 5

Revision ID: 005
Revises: 004
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "generated_pdfs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("generated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_generated_pdfs_doc", "generated_pdfs", ["doc_type", "doc_id"])


def downgrade():
    op.drop_index("ix_generated_pdfs_doc", "generated_pdfs")
    op.drop_table("generated_pdfs")
