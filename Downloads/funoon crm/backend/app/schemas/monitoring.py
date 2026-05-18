from datetime import datetime

from pydantic import BaseModel


class MonitoringConfigOut(BaseModel):
    id: str
    project_id: str
    sentry_dsn: str | None
    uptime_monitor_id: str | None
    anthropic_key_label: str | None
    error_rate_threshold: float
    token_budget_monthly: int | None
    alert_whatsapp: str | None

    model_config = {"from_attributes": True}


class MonitoringConfigCreate(BaseModel):
    sentry_dsn: str | None = None
    uptime_monitor_id: str | None = None
    anthropic_key_label: str | None = None
    error_rate_threshold: float = 5.0
    token_budget_monthly: int | None = None
    alert_whatsapp: str | None = None


class MonitoringEventOut(BaseModel):
    id: str
    project_id: str
    event_type: str
    severity: str
    description: str | None
    resolved: bool
    resolved_at: datetime | None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class MonitoringMetricOut(BaseModel):
    id: str
    project_id: str
    metric_type: str
    value: float
    recorded_at: datetime

    model_config = {"from_attributes": True}


class MetricIngest(BaseModel):
    metric_type: str
    value: float
