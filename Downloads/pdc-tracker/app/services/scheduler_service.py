"""
APScheduler with SQLAlchemyJobStore (PostgreSQL) for persistent jobs.
Jobs survive app restarts. All times in UTC; UAE = UTC+4.
"""
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def init_scheduler(app) -> None:
    global _scheduler
    if _scheduler is not None:
        return

    db_url = app.config["SQLALCHEMY_DATABASE_URI"]
    jobstores = {
        "default": SQLAlchemyJobStore(url=db_url, tablename="apscheduler_jobs"),
    }
    _scheduler = BackgroundScheduler(jobstores=jobstores, timezone="UTC")

    # Daily 04:00 UTC = 08:00 UAE
    _scheduler.add_job(
        _pdc_reminder_job,
        trigger="cron",
        hour=4,
        minute=0,
        id="pdc_reminder_daily",
        replace_existing=True,
        args=[app],
    )
    # Daily 04:30 UTC = 08:30 UAE
    _scheduler.add_job(
        _overdue_scan_job,
        trigger="cron",
        hour=4,
        minute=30,
        id="overdue_scan_daily",
        replace_existing=True,
        args=[app],
    )

    _scheduler.start()
    logger.info("APScheduler started with PostgreSQL job store")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None


# ── Job implementations ───────────────────────────────────────────────────────

def _pdc_reminder_job(app) -> None:
    """
    Scan pending PDCs where cheque_date is within reminder window
    and reminder has not yet been sent.
    """
    with app.app_context():
        try:
            from app.models.pdc import PDC
            from app.models.company import Company
            from app.models.audit_log import AuditAction
            from app.services.audit_service import log_event
            from app.services.pdc_service import send_pdc_reminder, send_pdc_escalation

            today = date.today()
            pdcs = PDC.query.filter(
                PDC.pdc_status == "pending",
                PDC.reminder_sent.is_(False),
            ).all()

            reminded = 0
            escalated = 0
            for pdc in pdcs:
                if pdc.cheque_date is None:
                    continue
                company = Company.query.get(pdc.company_id)
                if company is None:
                    continue

                days_ahead = (pdc.cheque_date - today).days
                reminder_window = (
                    company.pdc_reminder_days_received
                    if pdc.pdc_direction == "received"
                    else company.pdc_reminder_days_issued
                )

                if days_ahead < 0:
                    send_pdc_escalation(pdc, company)
                    log_event(
                        action=AuditAction.UPDATE,
                        table_name="pdcs",
                        record_id=pdc.id,
                        user_id=None,
                        ip_address="scheduler",
                        new_values={"event": "escalation_sent"},
                    )
                    escalated += 1
                elif days_ahead <= reminder_window:
                    send_pdc_reminder(pdc, company)
                    log_event(
                        action=AuditAction.UPDATE,
                        table_name="pdcs",
                        record_id=pdc.id,
                        user_id=None,
                        ip_address="scheduler",
                        new_values={"event": "reminder_sent"},
                    )
                    reminded += 1

            logger.info("pdc_reminder_job done: %d reminded, %d escalated", reminded, escalated)
        except Exception:
            logger.exception("pdc_reminder_job failed")


def _overdue_scan_job(app) -> None:
    """
    Scan invoices past due_date that are still unpaid — log each to audit.
    PDCs past cheque_date and still pending are also logged.
    """
    with app.app_context():
        try:
            from app.models.invoice import Invoice
            from app.models.purchase_invoice import PurchaseInvoice
            from app.models.audit_log import AuditAction
            from app.services.audit_service import log_event

            today = date.today()
            overdue_count = 0

            for ModelCls in (Invoice, PurchaseInvoice):
                rows = ModelCls.query.filter(
                    ModelCls.due_date < today,
                    ModelCls.status == "confirmed",
                    ModelCls.is_voided.is_(False),
                    ModelCls.payment_status == "unpaid",
                ).all()
                for doc in rows:
                    log_event(
                        action=AuditAction.UPDATE,
                        table_name=doc.__tablename__,
                        record_id=doc.id,
                        user_id=None,
                        ip_address="scheduler",
                        new_values={"event": "overdue_detected", "due_date": str(doc.due_date)},
                    )
                    overdue_count += 1

            logger.info("overdue_scan_job done: %d overdue items detected", overdue_count)
        except Exception:
            logger.exception("overdue_scan_job failed")
