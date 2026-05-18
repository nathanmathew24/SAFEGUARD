"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("contact_name", sa.Text()),
        sa.Column("whatsapp", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("source", sa.Text()),
        sa.Column("stage", sa.Text(), nullable=False, server_default="inbound"),
        sa.Column("enquiry", sa.Text()),
        sa.Column("estimated_mrr", sa.Integer()),
        sa.Column("next_action", sa.Text()),
        sa.Column("next_action_due", sa.Date()),
        sa.Column("ai_context", sa.Text()),
        sa.Column("ai_context_updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_clients_stage", "clients", ["stage"])

    op.create_table(
        "client_stage_history",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("from_stage", sa.Text()),
        sa.Column("to_stage", sa.Text(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("moved_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "client_notes",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", sa.UUID()),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("health", sa.Text(), nullable=False, server_default="green"),
        sa.Column("live_since", sa.Date()),
        sa.Column("renewal_date", sa.Date()),
        sa.Column("stack_tags", sa.ARRAY(sa.Text())),
        sa.Column("external_links", JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_projects_health", "projects", ["health"])

    op.create_table(
        "project_blockers",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("owner", sa.Text()),
        sa.Column("due_date", sa.Date()),
        sa.Column("resolved", sa.Boolean(), server_default="false"),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "project_notes",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "monitoring_configs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("sentry_dsn", sa.Text()),
        sa.Column("uptime_monitor_id", sa.Text()),
        sa.Column("anthropic_key_label", sa.Text()),
        sa.Column("error_rate_threshold", sa.Float(), server_default="5.0"),
        sa.Column("token_budget_monthly", sa.Integer()),
        sa.Column("alert_whatsapp", sa.Text()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )

    op.create_table(
        "monitoring_events",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("resolved", sa.Boolean(), server_default="false"),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_monitoring_events_project", "monitoring_events", ["project_id", "occurred_at"])

    op.create_table(
        "monitoring_metrics",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("metric_type", sa.Text(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_monitoring_metrics_project", "monitoring_metrics", ["project_id", "recorded_at"])

    op.create_table(
        "billing_records",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("cycle", sa.Text(), server_default="monthly"),
        sa.Column("status", sa.Text(), server_default="active"),
        sa.Column("started_at", sa.Date()),
        sa.Column("ended_at", sa.Date()),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", sa.UUID()),
        sa.Column("number", sa.Text()),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("issued_date", sa.Date()),
        sa.Column("due_date", sa.Date()),
        sa.Column("status", sa.Text(), server_default="draft"),
        sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_index("idx_invoices_status", "invoices", ["status"])

    op.create_table(
        "infra_costs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID()),
        sa.Column("service", sa.Text(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_infra_costs_month", "infra_costs", ["month"])

    op.create_table(
        "components",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("tech_tags", sa.ARRAY(sa.Text())),
        sa.Column("status", sa.Text(), server_default="stable"),
        sa.Column("version", sa.Text()),
        sa.Column("github_path", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "component_deployments",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("component_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sops",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("category", sa.Text()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "incident_log",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID()),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text()),
        sa.Column("resolution", sa.Text()),
        sa.Column("time_to_resolve", sa.Integer()),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("messages", JSONB(), server_default="[]"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_conversations")
    op.drop_table("incident_log")
    op.drop_table("sops")
    op.drop_table("component_deployments")
    op.drop_table("components")
    op.drop_index("idx_infra_costs_month", "infra_costs")
    op.drop_table("infra_costs")
    op.drop_index("idx_invoices_status", "invoices")
    op.drop_table("invoices")
    op.drop_table("billing_records")
    op.drop_index("idx_monitoring_metrics_project", "monitoring_metrics")
    op.drop_table("monitoring_metrics")
    op.drop_index("idx_monitoring_events_project", "monitoring_events")
    op.drop_table("monitoring_events")
    op.drop_table("monitoring_configs")
    op.drop_table("project_notes")
    op.drop_table("project_blockers")
    op.drop_index("idx_projects_health", "projects")
    op.drop_table("projects")
    op.drop_table("client_notes")
    op.drop_table("client_stage_history")
    op.drop_index("idx_clients_stage", "clients")
    op.drop_table("clients")
