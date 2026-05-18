from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.monitoring import MonitoringConfig, MonitoringEvent, MonitoringMetric
from app.schemas.monitoring import (
    MetricIngest,
    MonitoringConfigCreate,
    MonitoringConfigOut,
    MonitoringEventOut,
    MonitoringMetricOut,
)
from app.services.alert_service import alert_farzeel
from app.services.ai_service import complete

router = APIRouter()


# ── Monitoring config ─────────────────────────────────────────────────────────

@router.get("/{project_id}/config", response_model=MonitoringConfigOut)
async def get_config(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonitoringConfig).where(MonitoringConfig.project_id == project_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No monitoring config for this project")
    return config


@router.put("/{project_id}/config", response_model=MonitoringConfigOut)
async def upsert_config(
    project_id: str,
    body: MonitoringConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MonitoringConfig).where(MonitoringConfig.project_id == project_id)
    )
    config = result.scalar_one_or_none()
    if config:
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(config, field, value)
    else:
        config = MonitoringConfig(project_id=project_id, **body.model_dump())
        db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


# ── Metrics ingestion ─────────────────────────────────────────────────────────

@router.post("/{project_id}/metrics", response_model=MonitoringMetricOut, status_code=status.HTTP_201_CREATED)
async def ingest_metric(
    project_id: str,
    body: MetricIngest,
    db: AsyncSession = Depends(get_db),
):
    metric = MonitoringMetric(project_id=project_id, **body.model_dump())
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    await _check_alert_rules(project_id, body.metric_type, body.value, db)
    return metric


@router.get("/{project_id}/metrics", response_model=list[MonitoringMetricOut])
async def list_metrics(
    project_id: str,
    metric_type: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(MonitoringMetric)
        .where(MonitoringMetric.project_id == project_id)
        .order_by(MonitoringMetric.recorded_at.desc())
        .limit(limit)
    )
    if metric_type:
        q = q.where(MonitoringMetric.metric_type == metric_type)
    result = await db.execute(q)
    return result.scalars().all()


# ── Events / alert log ────────────────────────────────────────────────────────

@router.get("/{project_id}/events", response_model=list[MonitoringEventOut])
async def list_events(
    project_id: str,
    resolved: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(MonitoringEvent)
        .where(MonitoringEvent.project_id == project_id)
        .order_by(MonitoringEvent.occurred_at.desc())
    )
    if resolved is not None:
        q = q.where(MonitoringEvent.resolved == resolved)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/{project_id}/events/{event_id}/resolve", response_model=MonitoringEventOut)
async def resolve_event(
    project_id: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MonitoringEvent).where(
            MonitoringEvent.id == event_id,
            MonitoringEvent.project_id == project_id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.resolved = True
    event.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(event)
    return event


# ── Summary grid (all projects) ───────────────────────────────────────────────

@router.get("", response_model=list[dict])
async def monitoring_summary(db: AsyncSession = Depends(get_db)):
    from app.models.project import Project
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Project).options(selectinload(Project.monitoring_config))
    )
    projects = result.scalars().all()

    summaries = []
    for p in projects:
        latest_metrics: dict[str, float] = {}
        metrics_result = await db.execute(
            select(MonitoringMetric)
            .where(MonitoringMetric.project_id == p.id)
            .order_by(MonitoringMetric.recorded_at.desc())
            .limit(50)
        )
        for m in metrics_result.scalars().all():
            if m.metric_type not in latest_metrics:
                latest_metrics[m.metric_type] = m.value

        open_events_result = await db.execute(
            select(MonitoringEvent)
            .where(MonitoringEvent.project_id == p.id, MonitoringEvent.resolved == False)  # noqa: E712
            .order_by(MonitoringEvent.occurred_at.desc())
            .limit(1)
        )
        last_event = open_events_result.scalar_one_or_none()

        summaries.append({
            "project_id": str(p.id),
            "project_name": p.name,
            "health": p.health,
            "metrics": latest_metrics,
            "last_alert": last_event.description if last_event else None,
            "last_alert_at": last_event.occurred_at.isoformat() if last_event else None,
        })
    return summaries


# ── AI: diagnose error spike ──────────────────────────────────────────────────

@router.post("/{project_id}/ai/diagnose", response_model=dict)
async def ai_diagnose(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonitoringEvent)
        .where(MonitoringEvent.project_id == project_id)
        .order_by(MonitoringEvent.occurred_at.desc())
        .limit(10)
    )
    events = result.scalars().all()
    if not events:
        return {"diagnosis": "No recent events to diagnose."}

    events_text = "\n".join(
        f"- [{e.severity}] {e.description} ({e.occurred_at.strftime('%Y-%m-%d %H:%M')})"
        for e in events
    )
    response = await complete(
        system="You are Funoon's internal operations assistant. Tone: direct, specific, low-word-count.",
        messages=[{
            "role": "user",
            "content": f"Diagnose this error spike and suggest likely root causes:\n{events_text}",
        }],
        max_tokens=300,
    )
    return {"diagnosis": response.content[0].text}


# ── Internal: alert rule evaluation ──────────────────────────────────────────

async def _check_alert_rules(
    project_id: str,
    metric_type: str,
    value: float,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(MonitoringConfig).where(MonitoringConfig.project_id == project_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return

    alert_msg: str | None = None
    severity = "warning"

    if metric_type == "error_rate_24h" and value > config.error_rate_threshold:
        alert_msg = f"Error rate {value:.1f}% exceeds threshold {config.error_rate_threshold}% for project {project_id}"
        severity = "critical"
    elif metric_type == "uptime_24h" and value < 99.0:
        alert_msg = f"Uptime {value:.1f}% below 99% for project {project_id}"
        severity = "warning"
    elif metric_type == "token_spend_month" and config.token_budget_monthly:
        pct = (value / config.token_budget_monthly) * 100
        if pct >= 80:
            alert_msg = f"Token spend at {pct:.0f}% of monthly budget for project {project_id}"
            severity = "warning"

    if alert_msg:
        event = MonitoringEvent(
            project_id=project_id,
            event_type=metric_type,
            severity=severity,
            description=alert_msg,
        )
        db.add(event)
        await db.commit()
        await alert_farzeel(alert_msg)
