import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = structlog.get_logger()

scheduler = AsyncIOScheduler(timezone="Asia/Dubai")


def register_jobs() -> None:
    if settings.standup_enabled:
        scheduler.add_job(
            _daily_standup,
            CronTrigger(day_of_week="mon-fri", hour=settings.standup_hour, minute=settings.standup_minute),
            id="daily_standup",
            replace_existing=True,
        )

    scheduler.add_job(
        _weekly_pipeline_digest,
        CronTrigger(day_of_week="mon", hour=settings.standup_hour, minute=settings.standup_minute),
        id="weekly_pipeline_digest",
        replace_existing=True,
    )

    scheduler.add_job(
        _monthly_financial_summary,
        CronTrigger(day=1, hour=8, minute=0),
        id="monthly_financial_summary",
        replace_existing=True,
    )

    scheduler.add_job(
        _auto_flag_projects,
        CronTrigger(minute=0),  # every hour
        id="auto_flag_projects",
        replace_existing=True,
    )

    scheduler.add_job(
        _invoice_overdue_check,
        CronTrigger(hour=8, minute=0),
        id="invoice_overdue_check",
        replace_existing=True,
    )


async def _daily_standup() -> None:
    try:
        logger.info("job_daily_standup_started")
        # Prompt 14 — implementation
    except Exception as e:
        logger.error("job_daily_standup_failed", error=str(e))


async def _weekly_pipeline_digest() -> None:
    try:
        logger.info("job_weekly_digest_started")
        # Prompt 14 — implementation
    except Exception as e:
        logger.error("job_weekly_digest_failed", error=str(e))


async def _monthly_financial_summary() -> None:
    try:
        logger.info("job_monthly_summary_started")
        # Prompt 14 — implementation
    except Exception as e:
        logger.error("job_monthly_summary_failed", error=str(e))


async def _auto_flag_projects() -> None:
    try:
        logger.info("job_auto_flag_started")
        from app.database import SessionLocal
        from app.routers.projects import run_auto_flag
        async with SessionLocal() as db:
            await run_auto_flag(db)
        logger.info("job_auto_flag_done")
    except Exception as e:
        logger.error("job_auto_flag_failed", error=str(e))


async def _invoice_overdue_check() -> None:
    try:
        logger.info("job_invoice_overdue_started")
        from app.database import SessionLocal
        from app.routers.financial import run_invoice_overdue_check
        from app.services.alert_service import alert_farzeel
        async with SessionLocal() as db:
            overdue = await run_invoice_overdue_check(db)
        if overdue:
            nums = ", ".join(i.number or str(i.id) for i in overdue)
            await alert_farzeel(f"Overdue invoices: {nums}")
        logger.info("job_invoice_overdue_done", count=len(overdue))
    except Exception as e:
        logger.error("job_invoice_overdue_failed", error=str(e))
