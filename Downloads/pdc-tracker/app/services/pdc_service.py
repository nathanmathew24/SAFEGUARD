"""
PDC status-machine transitions and reminder dispatch.
Every transition writes to AuditLog.
Amounts always in fils (INTEGER) — never float.
"""
from datetime import datetime, timezone

from app.extensions import db
from app.models.pdc import PDC
from app.models.company import Company
from app.models.audit_log import AuditAction
from app.services.audit_service import log_event
from app.utils.whatsapp_sender import send_whatsapp

# Allowed transitions: current_status → allowed next statuses
_TRANSITIONS = {
    "pending":   {"submitted", "cancelled"},
    "submitted": {"cleared", "bounced", "cancelled"},
    "cleared":   set(),
    "bounced":   set(),
    "cancelled": set(),
}


def _assert_transition(pdc: PDC, target: str) -> None:
    allowed = _TRANSITIONS.get(pdc.pdc_status, set())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition PDC {pdc.id} from '{pdc.pdc_status}' to '{target}'"
        )


def mark_submitted(pdc_id: int, user_id: int, ip: str) -> PDC:
    pdc = PDC.query.get_or_404(pdc_id)
    _assert_transition(pdc, "submitted")
    old = pdc.to_dict()
    pdc.pdc_status = "submitted"
    pdc.submitted_at = datetime.now(timezone.utc)
    db.session.flush()
    log_event(
        action=AuditAction.UPDATE,
        table_name="pdcs",
        record_id=pdc.id,
        user_id=user_id,
        ip_address=ip,
        old_values=old,
        new_values=pdc.to_dict(),
    )
    return pdc


def mark_cleared(pdc_id: int, user_id: int, ip: str) -> PDC:
    pdc = PDC.query.get_or_404(pdc_id)
    _assert_transition(pdc, "cleared")
    old = pdc.to_dict()
    pdc.pdc_status = "cleared"
    pdc.cleared_at = datetime.now(timezone.utc)
    db.session.flush()
    log_event(
        action=AuditAction.UPDATE,
        table_name="pdcs",
        record_id=pdc.id,
        user_id=user_id,
        ip_address=ip,
        old_values=old,
        new_values=pdc.to_dict(),
    )
    return pdc


def mark_bounced(pdc_id: int, user_id: int, ip: str) -> PDC:
    pdc = PDC.query.get_or_404(pdc_id)
    _assert_transition(pdc, "bounced")
    old = pdc.to_dict()
    pdc.pdc_status = "bounced"
    pdc.bounced_at = datetime.now(timezone.utc)
    db.session.flush()
    log_event(
        action=AuditAction.UPDATE,
        table_name="pdcs",
        record_id=pdc.id,
        user_id=user_id,
        ip_address=ip,
        old_values=old,
        new_values=pdc.to_dict(),
    )
    return pdc


def mark_cancelled(pdc_id: int, user_id: int, ip: str) -> PDC:
    pdc = PDC.query.get_or_404(pdc_id)
    _assert_transition(pdc, "cancelled")
    old = pdc.to_dict()
    pdc.pdc_status = "cancelled"
    db.session.flush()
    log_event(
        action=AuditAction.UPDATE,
        table_name="pdcs",
        record_id=pdc.id,
        user_id=user_id,
        ip_address=ip,
        old_values=old,
        new_values=pdc.to_dict(),
    )
    return pdc


def send_pdc_reminder(pdc: PDC, company: Company) -> None:
    """
    Dispatch a WhatsApp reminder for a due PDC.
    Called by the scheduler job; marks reminder_sent on success.
    """
    aed = pdc.amount / 100  # display only — stored as fils
    aed_str = f"AED {aed:,.2f}"

    if pdc.pdc_direction == "received":
        body = (
            f"PDC REMINDER: {aed_str} cheque from {pdc.party_name} "
            f"due {pdc.cheque_date.strftime('%d %b %Y')}. Submit to bank today."
        )
        recipients = [r for r in [company.finance_whatsapp, company.owner_whatsapp] if r]
    else:
        body = (
            f"PAYMENT DUE: {aed_str} to {pdc.party_name} on "
            f"{pdc.cheque_date.strftime('%d %b %Y')}. PDC #{pdc.cheque_number} to be cleared."
        )
        recipients = [r for r in [company.owner_whatsapp] if r]

    for recipient in recipients:
        send_whatsapp(recipient, body, message_type="pdc_reminder")

    pdc.reminder_sent = True
    pdc.reminder_sent_at = datetime.now(timezone.utc)
    db.session.commit()


def send_pdc_escalation(pdc: PDC, company: Company) -> None:
    """Escalate overdue PDC to Owner. Called by scheduler after cheque_date passes."""
    aed = pdc.amount / 100
    aed_str = f"AED {aed:,.2f}"
    body = (
        f"URGENT: PDC of {aed_str} from {pdc.party_name} was due "
        f"{pdc.cheque_date.strftime('%d %b %Y')} and has not been submitted."
    )
    if company.owner_whatsapp:
        send_whatsapp(company.owner_whatsapp, body, message_type="pdc_escalation")
