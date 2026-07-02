"""PDC Phase 4 — direction, reminder fields, company notification config

Revision ID: 004
Revises: 003
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # New enum for PDC direction
    op.execute("CREATE TYPE pdcdirection AS ENUM ('received', 'issued')")

    # --- companies: notification contacts + reminder config ---
    op.add_column("companies", sa.Column("owner_whatsapp", sa.String(20), nullable=True))
    op.add_column("companies", sa.Column("finance_whatsapp", sa.String(20), nullable=True))
    op.add_column("companies", sa.Column(
        "pdc_reminder_days_received",
        sa.Integer(),
        nullable=False,
        server_default="3",
    ))
    op.add_column("companies", sa.Column(
        "pdc_reminder_days_issued",
        sa.Integer(),
        nullable=False,
        server_default="5",
    ))

    # --- pdcs: direction + reminder + status timestamps ---
    op.add_column("pdcs", sa.Column(
        "pdc_direction",
        sa.Enum("received", "issued", name="pdcdirection"),
        nullable=False,
        server_default="received",
    ))
    op.add_column("pdcs", sa.Column(
        "reminder_sent",
        sa.Boolean(),
        nullable=False,
        server_default="false",
    ))
    op.add_column("pdcs", sa.Column(
        "reminder_sent_at",
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column("pdcs", sa.Column(
        "cleared_at",
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column("pdcs", sa.Column(
        "bounced_at",
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column("pdcs", sa.Column(
        "submitted_at",
        sa.DateTime(timezone=True),
        nullable=True,
    ))


def downgrade():
    op.drop_column("pdcs", "submitted_at")
    op.drop_column("pdcs", "bounced_at")
    op.drop_column("pdcs", "cleared_at")
    op.drop_column("pdcs", "reminder_sent_at")
    op.drop_column("pdcs", "reminder_sent")
    op.drop_column("pdcs", "pdc_direction")

    op.drop_column("companies", "pdc_reminder_days_issued")
    op.drop_column("companies", "pdc_reminder_days_received")
    op.drop_column("companies", "finance_whatsapp")
    op.drop_column("companies", "owner_whatsapp")

    op.execute("DROP TYPE pdcdirection")
